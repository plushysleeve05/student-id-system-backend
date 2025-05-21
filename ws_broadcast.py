# === backend/ws_broadcast.py ===

from fastapi import WebSocket, WebSocketDisconnect
import json

# Store all connected clients
clients = []

async def websocket_endpoint(websocket: WebSocket):
    # 1) Accept the connection
    await websocket.accept()
    
    # 2) Mark it not-yet-ready
    websocket.is_ready = False
    
    # 3) Register in our global list
    clients.append(websocket)
    print(f"[WebSocket] New client connected: {websocket.client}")

    try:
        while True:
            # 4) Wait for any message from the client
            msg_text = await websocket.receive_text()
            print(f"[WebSocket] Received from client: {msg_text}")

            # 5) On first message, flip the ready flag
            if not websocket.is_ready:
                websocket.is_ready = True
                print(f"[WebSocket] Client {websocket.client} marked READY")

            # 6) Echo back (optional, but helpful for debugging)
            await websocket.send_text(json.dumps({"echo": msg_text}))

    except WebSocketDisconnect:
        # 7) Cleanup on disconnect
        if websocket in clients:
            clients.remove(websocket)
        print(f"[WebSocket] Client disconnected: {websocket.client}")


async def broadcast_event(event_data):
    # 8) Only broadcast to sockets that have said they’re ready
    ready_clients = [ws for ws in clients if getattr(ws, "is_ready", False)]
    print(f"[WebSocket] Broadcasting to {len(ready_clients)} READY clients…")

    disconnected = []
    for ws in ready_clients:
        try:
            await ws.send_json(event_data)
        except Exception as e:
            print(f"[WebSocket] Failed to send to {ws.client}: {e}")
            disconnected.append(ws)

    # 9) Remove any dead sockets
    for ws in disconnected:
        if ws in clients:
            clients.remove(ws)
        print(f"[WebSocket] Removed disconnected client: {ws.client}")
