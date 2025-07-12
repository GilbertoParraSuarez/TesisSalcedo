from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from jose import JWTError, jwt
from actions.api.models.models import UserInDB, Role
from data.db.mongo import users_collection
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Obtiene el usuario actual basado en el token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    
    return UserInDB(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        second_name=user.get("second_name"),
        jefe_inmediato=user.get("jefe_inmediato"),
        cargo=user.get("cargo", ""),
        unidad=user.get("unidad", ""),
        fecha_ingreso=user.get("fecha_ingreso", datetime.now()),
        regimen=user.get("regimen", ""),
        role=user["role"],
        hashed_password=user["hashed_password"],
        disabled=user.get("disabled", True)
    )

async def get_current_active_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)]
) -> UserInDB:
    """Verifica que el usuario esté activo"""
    if current_user.disabled == False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user

def require_role(required_role: Role):
    """Factory para crear dependencias de verificación de roles"""
    async def role_checker(
        current_user: Annotated[UserInDB, Depends(get_current_active_user)]
    ) -> UserInDB:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requieren privilegios de {required_role.value}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return current_user
    return role_checker

# Dependencias específicas para cada rol
get_current_admin = require_role(Role.ADMIN)
get_current_boss = require_role(Role.BOSS)