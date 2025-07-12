from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional, Dict, Any
from actions.api.services.message_service import MessageService
from actions.api.models.models import (
    BotMessage,
    ChatCreate,
    ChatResponse,
    
)

router = APIRouter(prefix="/api", tags=["chats"])

@router.post("/chats/", response_model=dict)
async def create_chat(chat_data: ChatCreate):
    try:
        return await MessageService.create_chat(chat_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chats/{chat_id}/messages/", response_model=dict)
async def save_message(
    chat_id: str,
    message: BotMessage,
):
    try:
        return await MessageService.save_message(
            chat_id=chat_id,
            sender=message.sender,
            text=message.text,
            componente_activo=message.componente_activo,
            tipo_formulario=message.tipo_formulario,
            componente_utilizado=message.componente_utilizado,
            form_id=message.form_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats/{chat_id}/", response_model=dict)
async def get_chat(chat_id: str):
    try:
        return await MessageService.get_chat(chat_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/chats/", response_model=List[ChatResponse])
async def list_user_chats(user_id: str):
    try:
        return await MessageService.list_chats(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.patch("/chats/{chat_id}/messages/{message_id}/mark_used/", response_model=dict)
async def mark_component_used(
    chat_id: str,
    message_id: str,
    form_id: Optional[str] = None,
    tipo_formulario: Optional[str] = None
):
    try:
        return await MessageService.mark_component_used(chat_id, message_id, form_id, tipo_formulario)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
