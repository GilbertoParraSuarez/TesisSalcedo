from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated
from actions.api.models.models import UserCreate, UserOut, Token, UserInDB, Role, ChangePasswordRequest
from actions.api.dependencies import get_current_admin
from actions.api.services.user_service import (
    authenticate_user,
    create_user,
    get_full_user_data,
    update_user_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/change-password")
async def change_password(
    change_password_data: ChangePasswordRequest,
    current_user: UserInDB = Depends(get_full_user_data)
):
    try:
        success = await update_user_password(
            username=current_user.username,
            current_password=change_password_data.current_password,
            new_password=change_password_data.new_password
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo actualizar la contraseña"
            )
        return {"message": "Contraseña actualizada correctamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/register", response_model=UserOut)
async def register_user(
    user: UserCreate,
):
    if created_user := await create_user(user):
        return created_user
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Username or email already registered"
    )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not getattr(user, "disabled", False):  # Si disabled=False o no existe
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACCOUNT_DISABLED",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    
    user_out = UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        second_name=user.second_name,
        jefe_inmediato=user.jefe_inmediato,
        fecha_ingreso=user.fecha_ingreso,
        saldo_actual_mensual=user.saldo_actual_mensual,
        saldo_historico=user.saldo_historico,
        saldo_total=user.saldo_total,
        dias_utilizados=user.dias_utilizados,
        dias_reembolsados=user.dias_reembolsados,
        regimen=user.regimen,
        cargo=user.cargo,
        unidad=user.unidad,
        role=user.role,
        unlocked=user.unlocked
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_data": user_out
    }

@router.get("/users/me", response_model=UserOut)
async def read_users_me(
    username: str = Depends(lambda: Depends(get_full_user_data))
):
    return username