# actions/api/routes/websocket_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from actions.api.services.socket_manager import socket_manager
from jose import JWTError, jwt
import json
import os

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

from fastapi import WebSocket, WebSocketDisconnect, status
import json

@router.websocket("/ws/solicitudes/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    print(f"[SOCKET] Intentando conectar con user_id: {user_id}")

    await websocket.accept()  # 👈 MUY IMPORTANTE

    try:
        # Espera primer mensaje de autenticación
        msg = await websocket.receive_text()
        print("[SOCKET] Mensaje recibido:", msg)

        data = json.loads(msg)

        # Validación del tipo de mensaje
        if data.get("type") != "auth":
            print("[SOCKET] Tipo inválido:", data.get("type"))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Validación del token
        token = data.get("token")
        if not token:
            print("[SOCKET] Token no proporcionado")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Validación de grupos (si no hay, asigna por defecto)
        groups = data.get("groups", ["solicitudes"])

        print(f"[SOCKET] Token recibido, grupos: {groups}")

        # Lógica para guardar conexión
        await socket_manager.connect(websocket, user_id, groups)

        # Opcional: responder al cliente que autenticó bien
        await websocket.send_json({"type": "auth_ok", "message": "Conexión autenticada correctamente"})

        # Bucle para recibir otros mensajes (si tu app los usa)
        while True:
            msg = await websocket.receive_text()
            print(f"[SOCKET] Mensaje recibido de {user_id}: {msg}")

    except WebSocketDisconnect:
        print(f"[SOCKET] Cliente desconectado: {user_id}")
        await socket_manager.disconnect(user_id)

    except Exception as e:
        print(f"[SOCKET] Error inesperado: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Esto sí se debería ver en cualquier entorno")