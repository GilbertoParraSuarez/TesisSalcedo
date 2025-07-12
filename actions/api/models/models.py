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
    plantas_ids: List[str] = Field(default_factory=list)
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

class UserOut(UserBase):
    id: str
    role: Role

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    role: Optional[Role] = None
    plantas_ids: Optional[List[str]] = None
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

""" MODELOS PARA LA PLANTA """
class PlantaBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)

class PlantaCreate(PlantaBase):
    pass

class PlantaInDB(PlantaBase):
    id: str
    ultima_lectura: Optional[datetime] = None

class PlantaOut(PlantaBase):
    id: str
    ultima_lectura: Optional[datetime] = None

class PlantaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class PlantaList(BaseModel):
    plantas: List[PlantaOut]

""" MODELOS PARA LA LECTURA """
class LecturaBase(BaseModel):
    planta_id: str
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
    pass

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