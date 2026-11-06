import asyncio
import json
import cv2
import numpy as np
import mss
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from ultralytics import YOLO

from backend.agent_playwright import run_autonomous_qa_agent

app = FastAPI(title="Bug AI Detector Engine - CachyOS")

model = YOLO('yolov8n.pt')

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # Przechwytywanie ekranu pod Linux / CachyOS (mss)
    with mss.mss() as sct:
        monitor = sct.monitors[1] # Główny monitor

        try:
            while True:
                # Pobranie klatki ekranu
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # Analiza AI (YOLOv8)
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

                # Telemetria i Bounding Boxy dla HTML
                payload = {
                    "fps": 30,
                    "detections": detections
                }

                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(0.03) # ~30 FPS

        except WebSocketDisconnect:
            manager.disconnect(websocket)
            print("Klient WebSocket rozłączony")

# Endpoint do uruchamiania agenta Playwright w tle dla portu 8085
@app.post("/api/run-agent")
async def trigger_agent(background_tasks: BackgroundTasks, target_url: str = "http://localhost:8085"):
    """Uruchamia agenta Playwright w tle bez blokowania WebSocketa."""
    background_tasks.add_task(run_autonomous_qa_agent, target_url)
    return {"status": "success", "message": f"Agent Playwright został uruchomiony dla {target_url}"}
