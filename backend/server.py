import asyncio
import json
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ultralytics import YOLO

app = FastAPI(title="Bug AI Detector Engine")

# Ładowanie lekkiego modelu detekcji (lub własnego wykrywania artefaktów)
# Możesz użyć 'yolov8n.pt' do testów obiektów lub własnego trenowanego modelu na błędach renderowania
model = YOLO('yolov8n.pt')

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Symulacja przechwytywania klatek lub odbiór obrazu z bufora
    cap = cv2.VideoCapture(0) # 0 dla kamerki lokalnej / przechwytywania okna
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.03)
                continue

            # Analiza klatki przez AI
            results = model(frame, verbose=False)[0]
            detections = []

            h, w, _ = frame.shape

            for box in results.boxes:
                # Normalizacja współrzędnych do procentów widoku dla Tailwind CSS
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

            # Wysyłanie telemetrii i detekcji do frontendu
            payload = {
                "fps": round(cap.get(cv2.CAP_PROP_FPS) or 60),
                "detections": detections
            }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.03) # ~30 FPS transmisji dancyh
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        cap.release()