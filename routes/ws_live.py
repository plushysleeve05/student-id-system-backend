# backend/routes/ws_live.py

import json
import cv2
import numpy as np
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.tasks.process_frame import process_frame

router = APIRouter()

DASHBOARD_URL = "http://127.0.0.1:8000/api/dashboard/update"

async def send_dashboard_update(total=1, recognized=0, unrecognized=0, login_attempts=0):
    today = __import__("datetime").datetime.utcnow().date().isoformat()
    payload = {
        "date": today,
        "total_faces_detected": total,
        "recognized_faces": recognized,
        "unrecognized_faces": unrecognized,
        "total_login_attempts": login_attempts,
    }
    # fire-and-forget
    async with httpx.AsyncClient() as client:
        try:
            await client.post(DASHBOARD_URL, json=payload, timeout=2.0)
        except Exception:
            pass  # swallow any errors

@router.websocket("/ws/live")
async def live_feed_ws(websocket: WebSocket):
    mode = websocket.query_params.get("mode", "matching")
    await websocket.accept()

    try:
        while True:
            msg = await websocket.receive()

            # handle text control frames (mode change)
            if "text" in msg and msg["text"]:
                try:
                    data = json.loads(msg["text"])
                    if data.get("type") == "mode" and data.get("mode") in ("matching", "ml"):
                        mode = data["mode"]
                except json.JSONDecodeError:
                    pass
                continue

            # binary frame = JPEG
            frame_bytes = msg.get("bytes")
            if not frame_bytes:
                continue

            img = cv2.imdecode(
                np.frombuffer(frame_bytes, np.uint8),
                cv2.IMREAD_COLOR
            )

            # run per-frame detection
            evt = await process_frame(img, mode)

            # 1) send it back to client
            await websocket.send_json(evt)

            # 2) update dashboard stats
            #   every frame = 1 total face
            #   recognized_faces = 1 if evt.type=="success"
            total = 1
            recognized = 1 if evt.get("type") == "success" else 0
            unrecognized = 1 if evt.get("type") == "warning" else 0
            # no login attempts here
            await send_dashboard_update(total, recognized, unrecognized)

    except WebSocketDisconnect:
        return
