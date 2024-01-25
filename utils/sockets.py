from fastapi import FastAPI, WebSocket
from typing import List

app = FastAPI()
active_connections: List[WebSocket] = []

@app.websocket("/ws/busbooking")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for connection in active_connections:
                await connection.send_text(f"Update: {data}")
    except Exception as e:
        active_connections.remove(websocket)
