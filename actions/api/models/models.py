from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from bson import ObjectId
from enum import Enum

""" MODELOS PARA EL USUARIO (manteniendo los existentes) """
class Role(str, Enum):
    AGRIC = "agricultores"
    INVES = "investigadores"
    ADMIN = "administradores"

class UserBase(BaseModel):
    username: str
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: Role = Field(default=Role.AGRIC)  # Corregido el valor por defecto

class UserInDB(UserBase):
    id: str
    role: Role
    hashed_password: str
    
    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: str
    username: str
    nombre: str
    apellido: str
    role: str
    creado_en: datetime
    
    class Config:
        fields = {'hashed_password': {'exclude': True}}

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    role: Optional[Role] = None
    password: Optional[str] = None

class UserList(BaseModel):
    users: List[UserOut]
    
class Token(BaseModel):
    access_token: str
    token_type: str
    role: Role
    user_data: UserOut

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[Role] = None

""" MODELOS PARA LA LECTURA """
class LecturaBase(BaseModel):
    humedad: float
    temperatura: float
    ec: float
    ph: float
    nitrogeno: Optional[float] = None
    fosforo: Optional[float] = None
    potasio: Optional[float] = None
    fecha: datetime = Field(default_factory=datetime.utcnow)
    notas: Optional[str] = None

class LecturaCreate(LecturaBase):
        planta_id: Optional[str] = None  # ← Agregado

class LecturaInDB(LecturaBase):
    id: str

class LecturaOut(LecturaBase):
    id: str

class LecturaUpdate(BaseModel):
    humedad: Optional[float] = None
    temperatura: Optional[float] = None
    ec: Optional[float] = None
    ph: Optional[float] = None
    nitrogeno: Optional[float] = None
    fosforo: Optional[float] = None
    potasio: Optional[float] = None
    notas: Optional[str] = None

class LecturaList(BaseModel):
    lecturas: List[LecturaOut]
    count: int