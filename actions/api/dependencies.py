from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, Optional
from jose import JWTError, jwt
from datetime import datetime
import os
from dotenv import load_dotenv

from actions.api.models.models import UserInDB, Role, TokenData
from actions.api.services.auth_service import AuthService

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
auth_service = AuthService()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Obtiene el usuario actual basado en el token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
    
    user = await auth_service.get_current_user(token)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)]
) -> UserInDB:
    """Verifica que el usuario esté activo"""
    if current_user.disabled:
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
        if current_user.role != required_role.value:  # Comparar con el valor del Enum
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requieren privilegios de {required_role.value}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return current_user
    return role_checker

# Dependencias específicas para cada rol
get_current_admin = require_role(Role.ADMIN)
get_current_researcher = require_role(Role.INVES)
get_current_farmer = require_role(Role.AGRIC)

async def get_user_from_token(token: str = Depends(oauth2_scheme)) -> Optional[UserInDB]:
    """Obtiene el usuario desde el token sin lanzar excepciones (para uso interno)"""
    try:
        payload = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return await auth_service.get_current_user(token)
    except JWTError:
        return None

def same_user_or_admin(user_id: str):
    """Verifica que el usuario sea el mismo o un admin"""
    async def checker(
        current_user: Annotated[UserInDB, Depends(get_current_active_user)]
    ) -> UserInDB:
        if current_user.id != user_id and current_user.role != Role.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este recurso"
            )
        return current_user
    return checker