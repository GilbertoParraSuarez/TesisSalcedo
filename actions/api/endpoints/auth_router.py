from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated

from actions.api.services.auth_service import AuthService
from actions.api.services.user_service import UserService
from actions.api.models.models import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()
user_service = UserService()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    user_out = UserOut(
        id=user.id,
        username=user.username,
        nombre=user.nombre,
        apellido=user.apellido,
        plantas_ids=user.plantas_ids,
        creado_en=user.creado_en,
        role=user.role
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_data": user_out
    }

@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate):
    existing_user = await user_service.get_full_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    created_user = await user_service.create_user(user)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario"
        )
    
    return created_user

@router.get("/me", response_model=UserOut)
async def read_current_user(
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    return current_user