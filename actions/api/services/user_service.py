from datetime import datetime, timedelta
from typing import Optional, List, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from data.db.mongo import db
from actions.api.models.models import UserInDB, UserCreate, UserOut, UserUpdate, UserStatusUpdate, PeriodoInactividad, RegimenLaboral
import os
from dotenv import load_dotenv
from bson import ObjectId
from enum import Enum
from dateutil.relativedelta import relativedelta
import pytz
ECUADOR_TZ = pytz.timezone("America/Guayaquil")

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
users_collection = db["users"]

async def create_user(user: UserCreate):
    existing_user = await users_collection.find_one({
        "$or": [
            {"username": user.username},
            {"email": user.email}
        ]
    })
    if existing_user:
        return None
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    db_user = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "second_name": user.second_name,
        "jefe_inmediato": user.jefe_inmediato,
        "cargo": user.cargo,
        "unidad": user.unidad,
        "fecha_ingreso": user.fecha_ingreso,
        "regimen": user.regimen,
        "unlocked": False,
        "hashed_password": pwd_context.hash(user.password),
        "role": user.role,
        "disabled": True,
        "saldo_historico": 0.0,
        "saldo_total": 0.0,
        "dias_utilizados": 0.0,
        "dias_reembolsados": 0.0,
        "ultima_actualizacion_vacaciones": now,
        "periodos_inactividad": [],
        "created_at": now,
        "updated_at": now
    }
    
    result = await users_collection.insert_one(db_user)
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    return UserOut(**created_user, id=str(created_user["_id"]))

async def get_full_user_data(username: str):
    user = await users_collection.find_one({"username": username})
    if not user:
        return None
    return UserInDB(**user, id=str(user["_id"]))

async def authenticate_user(username: str, password: str):
    user = await users_collection.find_one({"username": username})
    if not user or not pwd_context.verify(password, user["hashed_password"]):
        return None
    return UserInDB(**user, id=str(user["_id"]))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    to_encode = data.copy()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def list_all_users() -> List[UserOut]:
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    users = []
    async for user in users_collection.find():
        users.append(UserOut(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            full_name=user.get("full_name"),
            second_name=user.get("second_name"),
            jefe_inmediato=user.get("jefe_inmediato"),
            cargo=user.get("cargo", ""),
            unidad=user.get("unidad", ""),
            fecha_ingreso=user["fecha_ingreso"],
            regimen=user["regimen"],
            saldo_historico=user.get("saldo_historico", 0.0),
            saldo_actual_mensual=user.get("saldo_actual_mensual", 0.0),
            dias_utilizados=user.get("dias_utilizados", 0.0),
            dias_reembolsados=user.get("dias_reembolsados", 0.0),
            saldo_total=user.get("saldo_total", 0.0),
            unlocked=user["unlocked"],
            disabled=user.get("disabled", True),
            role=user["role"],
            ultima_actualizacion_vacaciones=user.get("ultima_actualizacion_vacaciones", now),
            periodos_inactividad=user.get("periodos_inactividad", []),
            updated_at=user.get("updated_at", now),
        ))
    return users

def validate_password_strength(password: str) -> bool:
    """Verifica que la contraseña cumpla con requisitos mínimos de seguridad"""
    if len(password) < 8:
        return False
    # Puedes agregar más validaciones (mayúsculas, números, caracteres especiales)
    return True

async def update_user_password(
    username: str, 
    current_password: str, 
    new_password: str
) -> bool:
    """
    Actualiza la contraseña de un usuario y gestiona el estado 'unlocked'
    - Verifica la contraseña actual
    - Valida la nueva contraseña
    - Si unlocked=False, lo cambia a True
    - Retorna True si la operación fue exitosa
    """
    # Obtener el usuario actual
    user_data = await users_collection.find_one({"username": username})
    if not user_data:
        raise ValueError("Usuario no encontrado")

    # Verificar contraseña actual
    if not pwd_context.verify(current_password, user_data["hashed_password"]):
        raise ValueError("La contraseña actual es incorrecta")

    # Verificar que la nueva contraseña sea diferente
    if pwd_context.verify(new_password, user_data["hashed_password"]):
        raise ValueError("La nueva contraseña debe ser diferente a la actual")

    # Validar fortaleza de la nueva contraseña
    if len(new_password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")

    # Preparar la actualización
    update_data = {
        "$set": {
            "hashed_password": pwd_context.hash(new_password)
        }
    }

    # Si está bloqueado, desbloquear
    if user_data.get("unlocked") is False:
        update_data["$set"]["unlocked"] = True

    # Ejecutar la actualización
    result = await users_collection.update_one(
        {"username": username},
        update_data
    )

    return result.modified_count > 0

async def update_user(user_id: str, user_data: UserUpdate) -> Optional[UserOut]:
    if not ObjectId.is_valid(user_id):
        return None
    
    update_data = {k: v for k, v in user_data.dict(exclude_unset=True, exclude={"password"}).items() if v is not None}
    
    if hasattr(user_data, 'password') and user_data.password:
        update_data["hashed_password"] = pwd_context.hash(user_data.password)
        
    if not update_data:
        return None
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    update_data["updated_at"] = now
    
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data})
    
    if result.modified_count == 1:
        updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        return UserOut(**updated_user, id=str(updated_user["_id"]))
    return None

async def delete_user(user_id: str) -> bool:
    if not ObjectId.is_valid(user_id):
        return False
    
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count == 1

async def get_user_by_id(user_id: str) -> Optional[UserOut]:
    """Obtiene un usuario por su ID"""
    try:
        # Verifica si el user_id es un ObjectId válido
        if not ObjectId.is_valid(user_id):
            return None
            
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
            
        return UserOut(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            full_name=user.get("full_name", ""),
            second_name=user.get("second_name", ""),
            jefe_inmediato=user.get("jefe_inmediato", ""),
            cargo=user.get("cargo", ""),
            unidad=user.get("unidad", ""),
            fecha_ingreso=user["fecha_ingreso"],
            regimen=user["regimen"],
            unlocked=user.get("unlocked"),
            saldo_historico=user.get("saldo_historico"),
            saldo_actual_mensual=user.get("saldo_actual_mensual"),
            dias_utilizados=user.get("dias_utilizados"),
            dias_reembolsados=user.get("dias_reembolsados"),
            disabled=user.get("disabled"),
            periodos_inactividad=user.get("periodos_inactividad", []),
            role=user["role"]
        )
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        return None

async def list_bosses(current_user: UserOut = None) -> List[UserOut]:
    # 1. Construir query correctamente
    query = {
        "role": {"$in": ["boss"]},  # Incluye ambos roles
        "disabled": True  # Solo usuarios activos
    }
    
    # 3. Obtener y ordenar jefes
    jefes = await users_collection.find(query).sort(
        [("full_name", 1), ("second_name", 1)]  # Orden alfabético
    ).to_list(1000)
    
    # 4. Mapear resultados
    return [
        UserOut(
            id=str(jefe["_id"]),
            username=jefe["username"],
            email=jefe["email"],
            full_name=jefe.get("full_name", ""),
            second_name=jefe.get("second_name", ""),
            cargo=jefe.get("cargo", ""),
            unidad=jefe.get("unidad", ""),
            fecha_ingreso=jefe["fecha_ingreso"],
            regimen=jefe["regimen"],
            role=jefe["role"],
        )
        for jefe in jefes
    ]


""" LOGICA PARA LOS CALCULOS """

from dateutil.relativedelta import relativedelta

async def calcular_vacaciones_usuario(user_id: str) -> Optional[UserOut]:
    if not ObjectId.is_valid(user_id):
        return None
    
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    user_model = UserInDB(**user, id=str(user["_id"]))
    fecha_actual = now
    
    # Calcular antigüedad efectiva
    antiguedad = calcular_antiguedad_efectiva(
        user_model.fecha_ingreso, 
        user_model.periodos_inactividad
    )
    dias_servicio = antiguedad.days
    años_servicio = dias_servicio / 365.25  # Cálculo preciso con decimales

    # Determinar el periodo actual (1 de noviembre a 31 de octubre)
    año_periodo = fecha_actual.year if fecha_actual.month >= 11 else fecha_actual.year - 1
    inicio_periodo = datetime(año_periodo, 11, 1)
    fin_periodo = datetime(año_periodo + 1, 10, 31)
    
    # Calcular meses transcurridos en el periodo actual
    if user_model.fecha_ingreso > inicio_periodo:
        # Si ingresó después del inicio del periodo, calculamos desde su fecha de ingreso
        fecha_inicio_calculo = user_model.fecha_ingreso
    else:
        fecha_inicio_calculo = inicio_periodo
        
    if fecha_actual >= fin_periodo:
        meses_transcurridos = 12  # Periodo completo
    else:
        delta = relativedelta(fecha_actual, fecha_inicio_calculo)
        meses_transcurridos = delta.years * 12 + delta.months
        # Consideramos mes completo si tiene 15+ días trabajados
        if delta.days >= 15:
            meses_transcurridos += 1
    
    # Asegurar que no sea negativo y no exceda 12 meses
    meses_transcurridos = max(0, min(12, meses_transcurridos))
    
    if user_model.regimen == RegimenLaboral.LOSEP:
        # LOSEP: 2.5 días por mes (30 días anuales)
        dias_ganados_mes = 2.5
        dias_acumulados_periodo = meses_transcurridos * dias_ganados_mes
        horas_acumuladas_periodo = dias_acumulados_periodo * 8
    else:
        # Código de Trabajo - Corregido según tu observación
        if años_servicio < 1:
            dias_anuales = 0  # No tiene derecho hasta cumplir el primer año
        else:
            # Desde el primer año completo son 15 días
            if años_servicio < 5:
                dias_anuales = 15
            elif años_servicio < 6:
                dias_anuales = 15  # Hasta cumplir el sexto año
            elif años_servicio < 7:
                dias_anuales = 16
            elif años_servicio < 8:
                dias_anuales = 17
            else:
                dias_anuales = 30

        # Calcular días acumulados proporcionales
        dias_acumulados_periodo = (meses_transcurridos / 12) * dias_anuales
        horas_acumuladas_periodo = dias_acumulados_periodo * 8
        
    # Actualizar saldos
    update_data = {
        "saldo_actual_mensual": round(dias_acumulados_periodo, 2),
        "saldo_total": round(user_model.saldo_historico + dias_acumulados_periodo - user_model.dias_utilizados + user_model.dias_reembolsados, 2),
        "horas_disponibles": round(horas_acumuladas_periodo, 2),
        "ultima_actualizacion_vacaciones": fecha_actual,
        "updated_at": fecha_actual
    }
    
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    return UserOut(**updated_user, id=str(updated_user["_id"]))

async def actualizar_vacaciones_todos_usuarios():
    """
    Actualiza el cálculo de vacaciones para todos los usuarios activos
    """
    usuarios_actualizados = []
    async for user in users_collection.find({"disabled": True}):
        user_out = await calcular_vacaciones_usuario(str(user["_id"]))
        if user_out:
            usuarios_actualizados.append(user_out)
    return usuarios_actualizados

async def toggle_user_status(
    user_id: str, 
    status_update: UserStatusUpdate
) -> Optional[UserOut]:
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    if not ObjectId.is_valid(user_id):
        return None
    
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    
    user_model = UserInDB(**user, id=str(user["_id"]))
    fecha_actual = now
    update_data = {
        "disabled": status_update.disabled,
        "fecha_ultimo_cambio_estado": fecha_actual,
        "updated_at": fecha_actual
    }
    
    # Convertir periodos existentes a objetos PeriodoInactividad
    periodos_inactividad = [
        PeriodoInactividad(**p) if isinstance(p, dict) else p
        for p in user_model.periodos_inactividad
    ]
    
    if status_update.disabled == False:
        # Agregar nuevo periodo de inactividad (sin fecha fin)
        nuevo_periodo = PeriodoInactividad(
            fecha_inicio=fecha_actual,
            fecha_fin=None,
            motivo=status_update.motivo_inactividad or "Desactivado por administrador"
        )
        periodos_inactividad.append(nuevo_periodo)
    else:
        # Buscar el último periodo sin fecha fin y cerrarlo
        for periodo in reversed(periodos_inactividad):
            if periodo.fecha_fin is None:
                periodo.fecha_fin = fecha_actual
                break
    
    # Convertir a diccionarios para MongoDB
    update_data["periodos_inactividad"] = [
        {
            "fecha_inicio": p.fecha_inicio,
            "fecha_fin": p.fecha_fin,
            "motivo": p.motivo
        }
        for p in periodos_inactividad
    ]
    
    # Actualizar en base de datos
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # Recalcular vacaciones
    return await calcular_vacaciones_usuario(user_id)

def calcular_antiguedad_efectiva(fecha_ingreso: datetime, periodos_inactividad: List[PeriodoInactividad]) -> relativedelta:
    """
    Calcula la antigüedad efectiva restando los periodos de inactividad
    """
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    fecha_actual = now
    tiempo_total = fecha_actual - fecha_ingreso
    tiempo_inactividad = timedelta(0)
    
    for periodo in periodos_inactividad:
        inicio = periodo.fecha_inicio
        fin = periodo.fecha_fin if periodo.fecha_fin else fecha_actual
        tiempo_inactividad += (fin - inicio)
    
    tiempo_efectivo = tiempo_total - tiempo_inactividad
    fecha_ingreso_efectiva = fecha_actual - tiempo_efectivo
    
    return relativedelta(fecha_actual, fecha_ingreso_efectiva)