from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
from actions.api.services.user_service import (
    list_all_users,
    update_user,
    delete_user,
    get_user_by_id,
    calcular_vacaciones_usuario,
    actualizar_vacaciones_todos_usuarios,
    toggle_user_status,
    list_bosses,
)
from actions.api.models.models import UserOut, UserUpdate, UserStatusUpdate, UserInDB, Role
from actions.api.dependencies import get_current_admin, get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])

# Endpoints existentes (se mantienen igual)
@router.get("/", response_model=List[UserOut])
async def list_users():
    return await list_all_users()

@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: str,
    #admin: UserOut = Depends(get_current_admin)
):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

@router.put("/{user_id}", response_model=UserOut)
async def update_user_data(
    user_id: str,
    user_data: UserUpdate,
):
    updated_user = await update_user(user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return updated_user

@router.delete("/{user_id}")
async def remove_user(
    user_id: str,
):
    if not await delete_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return {"message": "Usuario eliminado correctamente"}

@router.put("/{user_id}/vacaciones", response_model=UserOut)
async def obtener_vacaciones_actualizadas(
    user_id: str,
):
    # Verificar permisos (solo admin, jefe o el propio usuario)
    user_out = await calcular_vacaciones_usuario(user_id)
    if not user_out:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user_out

@router.post("/vacaciones/actualizar-todos", response_model=List[UserOut])
async def actualizar_vacaciones_todos(
    #admin: UserOut = Depends(get_current_admin)
):
    usuarios_actualizados = await actualizar_vacaciones_todos_usuarios()
    return usuarios_actualizados

@router.put("/{user_id}/status", response_model=UserOut)
async def cambiar_estado_usuario(
    user_id: str,
    status_update: UserStatusUpdate,
    #current_user: UserInDB = Depends(get_current_admin)
):
    user_out = await toggle_user_status(user_id, status_update)
    if not user_out:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user_out

@router.get("/bosses", response_model=List[UserOut])
async def listar_jefes(
    current_user: UserOut = Depends(get_current_active_user)  # Requiere autenticación
):
    return await list_bosses(current_user)

