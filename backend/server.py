import asyncio
import json
import os

import cv2
import numpy as np
import mss
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO

from backend.agent_playwright import run_autonomous_qa_agent

app = FastAPI(title="Bug AI Detector Engine - CachyOS")

os.makedirs("logs", exist_ok=True)
os.makedirs("videos", exist_ok=True)
app.mount("/logs", StaticFiles(directory="logs"), name="logs")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

model = YOLO('yolov8n.pt')


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        try:
            while True:
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                results = model(frame, verbose=False)[0]
                detections = []
                h, w, _ = frame.shape

                for box in results.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    label = model.names[cls_id]

                    detections.append({
                        "label": f"{label} ({int(confidence * 100)}%)",
                        "confidence": confidence,
                        "bbox": {
                            "top": f"{round((y1 / h) * 100, 2)}%",
                            "left": f"{round((x1 / w) * 100, 2)}%",
                            "width": f"{round(((x2 - x1) / w) * 100, 2)}%",
                            "height": f"{round(((y2 - y1) / h) * 100, 2)}%"
                        }
                    })

                payload = {
                    "fps": 30,
                    "detections": detections
                }

                await manager.broadcast(json.dumps(payload))
                await asyncio.sleep(0.03)

        except WebSocketDisconnect:
            manager.disconnect(websocket)
            print("Klient WebSocket rozłączony")


@app.post("/api/run-agent")
async def trigger_agent(background_tasks: BackgroundTasks, target_url: str = "http://localhost:8085"):
    background_tasks.add_task(run_autonomous_qa_agent, target_url)
    return {"status": "success", "message": f"Agent Playwright został uruchomiony dla {target_url}"}
