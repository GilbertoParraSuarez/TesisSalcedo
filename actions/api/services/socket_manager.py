from fastapi import WebSocket
from typing import Dict, List, Set
import json
from collections import defaultdict
from starlette.websockets import WebSocketState

from datetime import datetime

def custom_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Object of type {type(obj)} is not JSON serializable')


class SocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = defaultdict(dict)
        self.user_groups: Dict[str, Set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, user_id: str, groups: List[str]):
        try:
            # Asegurar que websocket está aceptado
            if websocket.client_state != WebSocketState.CONNECTED:
                await websocket.accept()
                
            for group in groups:
                self.active_connections[group][user_id] = websocket
                self.user_groups[user_id].add(group)
            
            print(f"Usuario {user_id} conectado a grupos: {groups}")
            
            # Enviar confirmación
            await websocket.send_text(json.dumps({
                "type": "connection_established",
                "message": "Successfully connected"
            }))
            
        except Exception as e:
            print(f"Error connecting user {user_id}: {e}")
            raise

    def disconnect(self, websocket: WebSocket, user_id: str):
        for group in self.user_groups.get(user_id, []):
            if user_id in self.active_connections.get(group, {}):
                del self.active_connections[group][user_id]
        if user_id in self.user_groups:
            del self.user_groups[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        for group in self.user_groups.get(user_id, []):
            if user_id in self.active_connections.get(group, {}):
                websocket = self.active_connections[group][user_id]
                await websocket.send_text(json.dumps(message, default=custom_serializer))

    async def broadcast_to_group(self, message: dict, group: str):
        if group not in self.active_connections:
            return

        # Copiamos la lista para evitar errores si el dict cambia durante la iteración
        for user_id, websocket in list(self.active_connections[group].items()):
            try:
                await websocket.send_text(json.dumps(message, default=custom_serializer))
            except Exception as e:
                print(f"[SOCKET] Error enviando a {user_id}, desconectando: {e}")
                await self.disconnect(user_id=user_id, websocket=websocket)


    async def notify_solicitud_update(self, solicitud: dict, user_id: str, jefe_id: str):
    # Notificar al usuario
        await self.send_personal_message({
            "type": "solicitud_update",
            "data": solicitud
        }, user_id)
        
        # Notificar al jefe
        if jefe_id:
            await self.send_personal_message({
                "type": "solicitud_update",
                "data": solicitud
            }, jefe_id)
        
        # Notificar a todos los admins
        await self.broadcast_to_group({
            "type": "solicitud_update",
            "data": solicitud
        }, "admin")
        
        await self.broadcast_to_group({
            "type": "solicitud_update",
            "data": solicitud
        }, "boss")

    async def notify_new_solicitud(self, solicitud: dict, jefe_id: str, user_id: str):
        # Notificar al jefe
        if jefe_id:
            await self.send_personal_message({
                "type": "new_solicitud",
                "data": solicitud
            }, jefe_id)

        # Notificar a todos los admins
        await self.broadcast_to_group({
            "type": "new_solicitud",
            "data": solicitud
        }, "admin")

        # Notificar al usuario (por si quieres mostrar "enviado", o después una actualización de estado)
        await self.send_personal_message({
            "type": "solicitud_update",
            "data": solicitud
        }, user_id)


socket_manager = SocketManager()
