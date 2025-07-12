from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any, Optional
from data.db.mongo import chats_collection
from actions.api.models.models import ChatCreate
import pytz

ECUADOR_TZ = pytz.timezone("America/Guayaquil")

class MessageService:
    @staticmethod
    async def create_chat(chat_data: ChatCreate) -> Dict[str, Any]:
        now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
        welcome_msg = {
            "message_id": str(now.timestamp()),
            "sender": "bot",
            "text": chat_data.initial_message,
            "timestamp": now,
            "componente_activo": "selector",
            "tipo_formulario": None,
            "componente_utilizado": False,
            "form_id": None
        }

        chat_doc = {
            "user_id": chat_data.user_id,
            "created_at": now,
            "updated_at": now,
            "status": "active",
            "messages": [welcome_msg]
        }
        result = await chats_collection.insert_one(chat_doc)
        return {
            "chat_id": str(result.inserted_id),
            "initial_message": welcome_msg
        }

    @staticmethod
    async def save_message(
        chat_id: str,
        sender: str,
        text: str,
        componente_activo: Optional[str] = None,
        tipo_formulario: Optional[str] = None,
        componente_utilizado: bool = False,
        form_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, str]:
        now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
        message_data = {
            "message_id": str(now.timestamp()),
            "sender": sender,
            "text": text,
            "componente_activo": componente_activo,
            "tipo_formulario": tipo_formulario,
            "componente_utilizado": componente_utilizado,
            "timestamp": now,
            "form_id": form_id,
            **kwargs
        }
        result = await chats_collection.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$push": {"messages": message_data},
                "$set": {"updated_at": now}
            }
        )
        if result.modified_count != 1:
            raise ValueError("Chat no encontrado")
        return {
            "status": "success",
            "message_data": message_data
        }
        
    @staticmethod
    async def get_chat(chat_id: str) -> Dict[str, Any]:
        chat = await chats_collection.find_one(
            {"_id": ObjectId(chat_id)}
        )
        if not chat:
            raise ValueError("Chat no encontrado")
        chat["_id"] = str(chat["_id"])
        return chat

    @staticmethod
    async def list_chats(user_id: str) -> List[Dict[str, Any]]:
        chats = await chats_collection.find(
            {"user_id": user_id},
            {
                "_id": 1,
                "user_id": 1,
                "created_at": 1,
                "updated_at": 1,
                "status": 1,
                "messages": {"$slice": -1}
            }
        ).to_list(None)

        return [{
            "chat_id": str(chat["_id"]),
            "user_id": chat["user_id"],
            "status": chat["status"],
            "created_at": chat["created_at"],
            "updated_at": chat["updated_at"],
            "last_message": chat["messages"][0] if chat["messages"] else None
        } for chat in chats]

    @staticmethod
    async def mark_component_used(
        chat_id: str, 
        message_id: str,
        form_id: str,
        tipo_formulario: str
    ) -> Dict[str, str]:
        update_data = {
            "messages.$.componente_utilizado": True,
            "messages.$.tipo_formulario": tipo_formulario,
        }
        
        if form_id is not None:
            update_data["messages.$.form_id"] = form_id

        result = await chats_collection.update_one(
            {
                "_id": ObjectId(chat_id),
                "messages.message_id": message_id
            },
            {
                "$set": update_data
            }
        )
        
        if result.modified_count != 1:
            raise ValueError("No se pudo actualizar el mensaje")
        
        return {
            "status": "success",
            "message": "Componente actualizado correctamente"
        }