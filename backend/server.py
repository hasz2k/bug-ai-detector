from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import cv2
import mss
import numpy as np
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("backend")

# Katalog główny projektu (~/Pulpit/Ai-detector), niezależnie od miejsca uruchomienia
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Konfiguracja (można nadpisać zmiennymi środowiskowymi) -------------------
# Model v4 był trenowany na 1280px (dla ONNX z dynamic=False musi się zgadzać).
IMGSZ = int(os.environ.get("IMGSZ", 1280))
FRAME_INTERVAL = float(os.environ.get("FRAME_INTERVAL", 0.005))
WS_PAUSE = 0.001
CONF_THRESHOLD = float(os.environ.get("CONF", 0.25))

# Numer monitora w mss (1 = główny, 2 = drugi ...)
CAPTURE_MONITOR = int(os.environ.get("CAPTURE_MONITOR", 1))

# Opcjonalny region przechwytywania: CAPTURE_REGION="left,top,width,height"
_region = os.environ.get("CAPTURE_REGION")
CAPTURE_REGION: dict[str, int] | None = (
    dict(zip(("left", "top", "width", "height"), map(int, _region.split(","))))
    if _region
    else None
)

DEVICE: int | str = 0 if torch.cuda.is_available() else "cpu"

# Na GPU preferujemy .engine / .pt (PyTorch), na CPU — OpenVINO / ONNX / PyTorch.
if DEVICE == "cpu":
    MODEL_CANDIDATES = (
        BASE_DIR / "yolov8_ui_bugs_openvino_model",
        BASE_DIR / "yolov8_ui_bugs.onnx",
        BASE_DIR / "yolov8_ui_bugs.pt",
        BASE_DIR / "yolov8n.pt",
    )
else:
    MODEL_CANDIDATES = (
        BASE_DIR / "yolov8_ui_bugs.engine",
        BASE_DIR / "yolov8_ui_bugs.pt",
        BASE_DIR / "yolov8_ui_bugs.onnx",
        BASE_DIR / "yolov8n.pt",
    )


def load_detection_model() -> YOLO:
    for candidate in MODEL_CANDIDATES:
        if candidate.exists():
            log.info("Znaleziono silnik modelu: %s", candidate.name)
            return YOLO(str(candidate), task="detect")
    log.warning("Brak wytrenowanego modelu UI w %s — używam fallbacku yolov8n.pt", BASE_DIR)
    return YOLO("yolov8n.pt")


class IssueRequest(BaseModel):
    title: str
    description: str
    system: str


class ReportRequest(BaseModel):
    session_id: str
    target_url: str
    detections: list[Any]


class DetectorState:
    def __init__(self) -> None:
        self.model: YOLO | None = None
        self.latest: np.ndarray | None = None
        self.frame_id: int = 0
        self.frame_lock = threading.Lock()
        self.infer_lock = threading.Lock()
        self.stop = threading.Event()
        self.thread: threading.Thread | None = None

    def capture_worker(self) -> None:
        """Przechwytywanie ekranu (Wayland/KDE przez spectacle w /dev/shm, X11 przez mss)."""
        is_wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

        if is_wayland and shutil.which("spectacle"):
            shm_path = "/dev/shm/bug_ai_frame.png"
            log.info(
                "Wykryto Wayland — przechwytywanie natywne przez spectacle (%s), region=%s",
                shm_path,
                CAPTURE_REGION,
            )
            try:
                while not self.stop.is_set():
                    subprocess.run(
                        ["spectacle", "-b", "-n", "-f", "-o", shm_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    img = cv2.imread(shm_path)
                    if img is not None:
                        if CAPTURE_REGION:
                            l, t = CAPTURE_REGION["left"], CAPTURE_REGION["top"]
                            w, h = CAPTURE_REGION["width"], CAPTURE_REGION["height"]
                            img = np.ascontiguousarray(img[t : t + h, l : l + w])
                        with self.frame_lock:
                            self.latest = img
                            self.frame_id += 1
                    time.sleep(FRAME_INTERVAL)
            finally:
                if os.path.exists(shm_path):
                    os.remove(shm_path)
            return

        with mss.mss() as sct:
            monitor = CAPTURE_REGION or sct.monitors[CAPTURE_MONITOR]
            log.info("Przechwytywanie X11 (mss): %s", monitor)
            while not self.stop.is_set():
                frame = np.ascontiguousarray(np.asarray(sct.grab(monitor))[:, :, :3])
                with self.frame_lock:
                    self.latest = frame
                    self.frame_id += 1
                time.sleep(FRAME_INTERVAL)

    def get_frame(self) -> tuple[int, np.ndarray | None]:
        with self.frame_lock:
            return self.frame_id, self.latest

    def infer(self, frame: np.ndarray):
        assert self.model is not None, "Model nie został załadowany"
        with self.infer_lock:
            return self.model(
                frame, imgsz=IMGSZ, conf=CONF_THRESHOLD, device=DEVICE, verbose=False
            )[0]


state = DetectorState()


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("Inicjalizacja Bug AI Detector Engine (IMGSZ=%d, CONF=%.2f)...", IMGSZ, CONF_THRESHOLD)
    log.info("Urządzenie inferencji: %s", DEVICE)
    state.model = load_detection_model()

    log.info("Rozgrzewanie silnika inferencyjnego...")
    dummy = np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)
    for _ in range(3):
        state.model(dummy, imgsz=IMGSZ, device=DEVICE, verbose=False)

    state.stop.clear()
    state.thread = threading.Thread(target=state.capture_worker, daemon=True)
    state.thread.start()
    try:
        yield
    finally:
        state.stop.set()
        if state.thread:
            state.thread.join(timeout=2)
        log.info("Zamykanie serwera Bug AI...")


app = FastAPI(title="Bug AI Detector API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/run-agent")
async def api_run_agent(target_url: str):
    log.info("Uruchamianie agenta Playwright dla URL: %s", target_url)
    await asyncio.sleep(1)
    return {"status": "success", "message": f"Agent QA rozpoczął skan: {target_url}"}


@app.post("/api/create-issue")
async def api_create_issue(req: IssueRequest):
    log.info("Tworzenie ticketa w %s: %s", req.system.upper(), req.title)
    await asyncio.sleep(0.5)
    issue_key = f"{req.system.upper()}-10{int(time.time() % 1000)}"
    return {"status": "success", "issue_key": issue_key}


@app.post("/api/export-report")
async def api_export_report(req: ReportRequest):
    log.info("Generowanie raportów dla sesji %s", req.session_id)
    await asyncio.sleep(1)
    return {
        "status": "success",
        "reports": {
            "pdf": f"/exports/{req.session_id}.pdf",
            "csv": f"/exports/{req.session_id}.csv",
        },
    }


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    log.info("Klient UI podłączony do telemetrii: %s", websocket.client)

    prev_time = time.time()
    last_id = -1
    try:
        while True:
            frame_id, frame = state.get_frame()
            if frame is None or frame_id == last_id:
                await asyncio.sleep(0.005)
                continue
            last_id = frame_id

            result = await asyncio.to_thread(state.infer, frame)

            h, w = frame.shape[:2]
            detections = []
            for box in result.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "label": f"{state.model.names[cls_id]} ({int(conf * 100)}%)",
                    "confidence": conf,
                    "bbox": {
                        "top": f"{(y1 / h) * 100:.2f}%",
                        "left": f"{(x1 / w) * 100:.2f}%",
                        "width": f"{((x2 - x1) / w) * 100:.2f}%",
                        "height": f"{((y2 - y1) / h) * 100:.2f}%",
                    },
                })

            now = time.time()
            fps = 1.0 / (now - prev_time) if now > prev_time else 0.0
            prev_time = now

            await websocket.send_text(json.dumps({"fps": round(fps, 1), "detections": detections}))
            await asyncio.sleep(WS_PAUSE)

    except WebSocketDisconnect:
        log.info("UI rozłączone: %s", websocket.client)
    except Exception as e:
        log.exception("Błąd strumienia wideo: %s", e)
        try:
            await websocket.close()
        except RuntimeError:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)