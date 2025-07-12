from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from actions.api.services.auth_service import AuthService
from actions.api.services.user_service import UserService
from actions.api.models.models import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])
auth_service = AuthService()
user_service = UserService()

@router.get("/", response_model=List[UserOut])
async def list_users(
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    return await user_service.list_users()

@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: str,
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    user = await user_service.get_user_by_id(user_id)
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
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    # Solo admins o el propio usuario pueden actualizar
    if current_user.role != "administradores" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    
    updated_user = await user_service.update_user(user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return updated_user

@router.delete("/{user_id}")
async def delete_user_data(
    user_id: str,
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    # Solo admins pueden eliminar usuarios
    if current_user.role != "administradores":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar usuarios"
        )
    
    if not await user_service.delete_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return {"message": "Usuario eliminado correctamente"}