from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional, Union, Any
from bson import ObjectId
from enum import Enum

class TipoSolicitud(str, Enum):
    VACACIONES = "vacaciones"
    HOJA_RUTA = "hoja_ruta"
    PERMISO = "permiso"

class MotivoHojaRuta(str, Enum):
    ASUNTO_PARTICULAR = "asunto particular"
    OTROS = "otros"

class MotivoPermiso(str, Enum):
    ASUNTOS_OFICINA = "asuntos de oficina"
    SALUD = "salud/enfermedad"
    CALAMIDAD = "calamidad doméstica"
    OTROS = "otros"

class EstadoSolicitud(str, Enum):
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"
    MODIFICADA = "modificada"

class SolicitudBase(BaseModel):
    usuario_id: str
    jefe_id: str
    tipo: TipoSolicitud
    estado: EstadoSolicitud = EstadoSolicitud.PENDIENTE
    fecha_solicitud: datetime = Field(default_factory=datetime.utcnow)
    fecha_aprobacion: Optional[datetime] = None
    aprobado_por_id: Optional[str] = None
    observaciones: Optional[str] = None
    periodo: Optional[str] = None
    modificado_por_id: Optional[str] = None
    reembolso: Optional[float] = 0
    fecha_modificacion: Optional[datetime] = None
    
class DetalleHojaRuta(BaseModel):
    motivo: MotivoHojaRuta
    desde_hora: datetime
    hasta_hora: datetime
    detalles: Optional[str] = None

class DetallePermiso(BaseModel):
    motivo: MotivoPermiso
    desde_hora: datetime
    hasta_hora: datetime
    detalles: Optional[str] = None
    archivo: Optional[str] = None
    descuento: bool = Field(default=False)
    cantDesc: Optional[float] = None

class DetalleVacaciones(BaseModel):
    desde_dia: datetime
    hasta_dia: datetime
    fecha_reincorporacion: datetime

class SolicitudCreate(BaseModel):
    usuario_id: str
    jefe_id: str
    tipo: TipoSolicitud
    periodo: str
    detalle: Union[DetalleHojaRuta, DetallePermiso, DetalleVacaciones]

class SolicitudInDB(SolicitudBase):
    id: str
    detalle: Union[DetalleHojaRuta, DetallePermiso, DetalleVacaciones]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }
    
class DetalleUpdate(BaseModel):
    desde_hora: Optional[datetime] = None
    hasta_hora: Optional[datetime] = None
    detalles: Optional[str] = None
    desde_dia: Optional[datetime] = None
    hasta_dia: Optional[datetime] = None
    fecha_reincorporacion: Optional[datetime] = None

# Añadir esto al final del archivo
class SolicitudUpdate(BaseModel):
    detalle: Optional[DetalleUpdate] = None
    modificador_id: str  # Requerido para auditar quién hizo el cambio
    
""" MODELOS PARA EL USUARIO """


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
class Role(str, Enum):
    USER = "user"
    BOSS = "boss"
    ADMIN = "admin"

class RegimenLaboral(str, Enum):
    LOSEP = "losep"
    CT = "codigo_trabajo"

class PeriodoInactividad(BaseModel):
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    motivo: str = Field(..., min_length=0)

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    second_name: Optional[str] = None
    jefe_inmediato: Optional[str] = None
    cargo: str = Field(..., min_length=2, max_length=100)
    unidad: str = Field(..., min_length=2, max_length=100)
    fecha_ingreso: datetime
    regimen: RegimenLaboral
    unlocked: bool = Field(default=False)
    # Campos de acumulación y estado
    saldo_historico: float = Field(default=0.0)
    saldo_actual_mensual: float = Field(default=0.0)
    dias_utilizados: float = Field(default=0.0)
    dias_reembolsados: float = Field(default=0.0)
    saldo_total: float = Field(default=0.0)
    
    # Campos de estado/inactividad
    disabled: bool = Field(default=True)
    fecha_ultimo_cambio_estado: Optional[datetime] = None
    ultima_actualizacion_vacaciones: datetime = Field(default_factory=datetime.utcnow)
    periodos_inactividad: Optional[List[PeriodoInactividad]] = Field(default_factory=list)
    
    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: Role = Field(default=Role.USER)

class UserInDB(UserBase):
    id: str
    role: Role
    hashed_password: str

    class Config:
        from_attributes = True

class UserOut(UserBase):
    id: str
    role: Role
    email: EmailStr

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    second_name: Optional[str] = None
    jefe_inmediato: Optional[str] = None
    cargo: Optional[str] = None
    unidad: Optional[str] = None
    role: Optional[Role] = None
    unlocked: Optional[bool] = None
    disabled: Optional[bool] = None
    password: Optional[str] = None
    regimen: Optional[str] = None
    fecha_ingreso: Optional[datetime] = None
    saldo_historico: Optional[float] = None
    saldo_actual_mensual: Optional[float] = None
    dias_utilizados: Optional[float] = None
    dias_reembolsados: Optional[float] = None
    saldo_total: Optional[float] = None
    
class UserStatusUpdate(BaseModel):
    disabled: bool
    motivo_inactividad: Optional[str] = None
    
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
    
""" MODELOS PARA MENSAJES Y CHAT """
class MessageBase(BaseModel):
    message_id: Optional[str] = None
    text: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    componente_activo: Optional[str] = None
    tipo_formulario: Optional[str] = None
    componente_utilizado: Optional[bool] = Field(default=False)
    form_id: Optional[str] = None

class UserMessage(MessageBase):
    sender: str = "user"
    
class BotMessage(MessageBase):
    sender: str = "bot"
    componente_activo: Optional[str] = None  # selector|formulario|cancelar
    tipo_formulario: Optional[str] = None    # vacaciones|permiso|hoja_ruta
    componente_utilizado: Optional[bool] = Field(default=False)
    form_id: Optional[str] = None
    
class ChatCreate(BaseModel):
    user_id: str
    initial_message: Optional[str] = Field(
        default="Hola!, soy el asistente virtual de la EPEMA. \nPuedo ayudarte con permisos, vacaciones y hojas de ruta.\nSi necesitas ayuda, dímelo o escoge una de las siguientes opciones:",
        description="Mensaje inicial automático del bot"
    )
    
class ChatResponse(BaseModel):
    chat_id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_message: Optional[Dict[str, Any]] = None

""" MODELOS PARA OPCIONES DE USUARIO """
class UserOption(BaseModel):
    option_type: str  # "cargo" o "unidad"
    value: str
    is_active: bool = True

class UserOptionCreate(BaseModel):
    option_type: str
    value: str

class UserOptionResponse(BaseModel):
    id: str
    option_type: str
    value: str
    is_active: bool