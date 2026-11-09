"""Bug AI Detector Engine - serwer FastAPI (CachyOS)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import cv2
import mss
import numpy as np
from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from ultralytics import YOLO

from backend.agent_playwright import run_autonomous_qa_agent
from backend.integrations import ConfigError, TrackerError, create_jira_issue, create_redmine_issue
from backend.reports import REPORTS_DIR, generate_csv_report, generate_pdf_report
from backend.webhooks import notify_all

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
VIDEOS_DIR = BASE_DIR / "videos"

MODEL_PATH = "yolov8n.pt"
MONITOR_INDEX = 1
TARGET_FPS = 30
FRAME_INTERVAL_S = 1 / TARGET_FPS
IDLE_POLL_S = 0.25
ERROR_BACKOFF_S = 1.0
DEFAULT_TARGET_URL = "http://localhost:8085"

# --- Konfiguracja CORS ------------------------------------------------------
_DEFAULT_ORIGINS = "http://localhost:8085,http://127.0.0.1:8085"
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    @property
    def has_connections(self) -> bool:
        return bool(self.active_connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        connections = list(self.active_connections)
        results = await asyncio.gather(
            *(connection.send_text(message) for connection in connections),
            return_exceptions=True,
        )
        for connection, result in zip(connections, results):
            if isinstance(result, Exception):
                self.disconnect(connection)


class ScreenDetector:
    def __init__(self, model: YOLO, monitor_index: int = MONITOR_INDEX) -> None:
        self._model = model
        self._monitor_index = monitor_index
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="screen-detector")
        self._local = threading.local()

    def _screen(self) -> mss.base.MSSBase:
        if not hasattr(self._local, "sct"):
            self._local.sct = mss.mss()
        return self._local.sct

    @staticmethod
    def _percent(value: float, total: float) -> str:
        return f"{round((value / total) * 100, 2)}%"

    def _to_detection(self, box: Any, width: int, height: int) -> dict[str, Any]:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        confidence = float(box.conf[0])
        label = self._model.names[int(box.cls[0])]
        return {
            "label": f"{label} ({int(confidence * 100)}%)",
            "confidence": confidence,
            "bbox": {
                "top": self._percent(y1, height),
                "left": self._percent(x1, width),
                "width": self._percent(x2 - x1, width),
                "height": self._percent(y2 - y1, height),
            },
        }

    def _detect(self) -> list[dict[str, Any]]:
        sct = self._screen()
        frame = cv2.cvtColor(np.array(sct.grab(sct.monitors[self._monitor_index])), cv2.COLOR_BGRA2BGR)
        height, width = frame.shape[:2]
        results = self._model(frame, conf=0.35, verbose=False)[0]
        return [self._to_detection(box, width, height) for box in results.boxes]

    async def detect(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._detect)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


manager = ConnectionManager()


async def stream_frames(detector: ScreenDetector) -> None:
    loop = asyncio.get_running_loop()
    while True:
        if not manager.has_connections:
            await asyncio.sleep(IDLE_POLL_S)
            continue

        started = loop.time()
        try:
            detections = await detector.detect()
        except Exception:
            logger.exception("Błąd analizy klatki")
            await asyncio.sleep(ERROR_BACKOFF_S)
            continue

        elapsed = loop.time() - started
        fps = round(1 / max(elapsed, FRAME_INTERVAL_S), 1)
        await manager.broadcast(json.dumps({"fps": fps, "detections": detections}))
        await asyncio.sleep(max(FRAME_INTERVAL_S - elapsed, 0))


@asynccontextmanager
async def lifespan(app: FastAPI):
    detector = ScreenDetector(YOLO(MODEL_PATH))
    streamer = asyncio.create_task(stream_frames(detector))
    try:
        yield
    finally:
        streamer.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await streamer
        detector.close()


app = FastAPI(title="Bug AI Detector Engine - CachyOS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)

for route, directory in (("/logs", LOGS_DIR), ("/videos", VIDEOS_DIR), ("/reports", REPORTS_DIR)):
    directory.mkdir(parents=True, exist_ok=True)
    app.mount(route, StaticFiles(directory=directory), name=route.strip("/"))


class IssueReportRequest(BaseModel):
    title: str
    description: str
    system: str = "jira"


class ExportReportRequest(BaseModel):
    session_id: str
    target_url: str = DEFAULT_TARGET_URL
    detections: list[dict[str, Any]] = Field(default_factory=list)


def _create_jira(report: IssueReportRequest) -> tuple[dict[str, Any], str]:
    key = create_jira_issue(summary=report.title, description=report.description).get("key")
    return {"issue_key": key}, str(key)


def _create_redmine(report: IssueReportRequest) -> tuple[dict[str, Any], str]:
    issue_id = create_redmine_issue(subject=report.title, description=report.description).get("issue", {}).get("id")
    return {"issue_id": issue_id}, f"#{issue_id}"


ISSUE_BACKENDS = {
    "jira": ("Jira", _create_jira),
    "redmine": ("Redmine", _create_redmine),
}


async def _handle_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Klient WebSocket rozłączony")
    finally:
        manager.disconnect(websocket)


@app.websocket("/ws/stream")
async def websocket_endpoint_ws(websocket: WebSocket) -> None:
    await _handle_websocket(websocket)


@app.websocket("/stream")
async def websocket_endpoint_legacy(websocket: WebSocket) -> None:
    await _handle_websocket(websocket)


@app.post("/api/run-agent")
async def trigger_agent(background_tasks: BackgroundTasks, target_url: str = DEFAULT_TARGET_URL):
    background_tasks.add_task(run_autonomous_qa_agent, target_url)
    background_tasks.add_task(
        notify_all,
        f"Rozpoczęto autonomiczną sesję testową QA dla URL: {target_url}",
        "🚀 Playwright Agent Triggered",
    )
    return {"status": "success", "message": f"Agent Playwright został uruchomiony dla {target_url}"}


@app.post("/api/create-issue")
def report_issue(report: IssueReportRequest, background_tasks: BackgroundTasks):
    backend = ISSUE_BACKENDS.get(report.system.lower())
    if backend is None:
        raise HTTPException(
            status_code=422,
            detail="Nieobsługiwany system zgłoszeń. Wybierz 'jira' lub 'redmine'.",
        )

    name, create = backend
    try:
        fields, reference = create(report)
    except ConfigError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except TrackerError as err:
        raise HTTPException(status_code=502, detail=str(err)) from err

    background_tasks.add_task(
        notify_all,
        f"Utworzono nowe zgłoszenie {name}: *{reference}*\nTytuł: {report.title}",
        f"📌 {name} Issue Created",
    )
    return {"status": "success", **fields}


@app.post("/api/export-report")
def export_report(req: ExportReportRequest):
    try:
        csv_file = generate_csv_report(req.session_id, req.detections)
        pdf_file = generate_pdf_report(req.session_id, req.target_url, req.detections)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err

    return {
        "status": "success",
        "reports": {
            "csv": f"/reports/{csv_file.name}",
            "pdf": f"/reports/{pdf_file.name}",
        },
    }
