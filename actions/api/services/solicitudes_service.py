from datetime import datetime, timedelta
from typing import Optional, List, Union, Dict
from bson import ObjectId
from dateutil import rrule
from datetime import time
from data.db.mongo import solicitudes_collection, users_collection
from actions.api.services.user_service import calcular_vacaciones_usuario
from actions.api.models.models import (
    SolicitudCreate, SolicitudInDB, TipoSolicitud, EstadoSolicitud, SolicitudUpdate
)
from fastapi import Depends
from actions.api.services.socket_manager import socket_manager
import pytz
ECUADOR_TZ = pytz.timezone("America/Guayaquil")

async def crear_solicitud(solicitud: SolicitudCreate) -> SolicitudInDB:
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    solicitud_dict = solicitud.dict()
    solicitud_dict["fecha_solicitud"] = now
    solicitud_dict["estado"] = EstadoSolicitud.PENDIENTE
    
    result = await solicitudes_collection.insert_one(solicitud_dict)
    solicitud_creada = await solicitudes_collection.find_one({"_id": result.inserted_id})
    solicitud_in_db = SolicitudInDB(**solicitud_creada, id=str(solicitud_creada["_id"]))
    
    await socket_manager.notify_new_solicitud(solicitud_in_db.dict(), jefe_id=solicitud_in_db.jefe_id, user_id=solicitud_in_db.usuario_id)
    
    return solicitud_in_db


async def actualizar_estado_solicitud(
    solicitud_id: str,
    nuevo_estado: EstadoSolicitud,
    aprobado_por_id: str,
    observaciones: Optional[str] = None
) -> Optional[SolicitudInDB]:
    if not ObjectId.is_valid(solicitud_id):
        return None
    
    update_data = {
        "estado": nuevo_estado,
        "fecha_aprobacion": datetime.now(ECUADOR_TZ).replace(tzinfo=None),
        "aprobado_por_id": aprobado_por_id,
    }
    
    if observaciones:
        update_data["observaciones"] = observaciones
    
    result = await solicitudes_collection.update_one(
        {"_id": ObjectId(solicitud_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 1:
        solicitud = await obtener_solicitud_por_id(solicitud_id)
        if solicitud:
            if nuevo_estado == EstadoSolicitud.APROBADA:
                await actualizar_dias_usuario(solicitud)
            
            # Notificar via WebSocket
            await socket_manager.notify_solicitud_update(
                solicitud.dict(),
                solicitud.usuario_id,
                solicitud.jefe_id
            )
            
        return solicitud
    return None

async def modificar_solicitud(
    solicitud_id: str,
    modificador_id: str,
    update_data: SolicitudUpdate
) -> Optional[SolicitudInDB]:
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    """Modifica una solicitud de manera más segura"""
    if not ObjectId.is_valid(solicitud_id):
        return None
    
    solicitud = await obtener_solicitud_por_id(solicitud_id)
    if not solicitud:
        return None
    
    # Obtener el valor anterior del reembolso
    reembolso_anterior = solicitud.reembolso if hasattr(solicitud, 'reembolso') else 0
    
    # Preparar datos de actualización
    update_dict = {
        "modificado_por_id": modificador_id,
        "fecha_modificacion": now
    }
    
    if update_data.reembolso is not None:
        update_dict["reembolso"] = max(0, update_data.reembolso)
        
        # Calcular diferencia para actualizar el usuario
        diferencia = update_data.reembolso - reembolso_anterior
        
        # Actualizar días reembolsados del usuario
        usuario = await users_collection.find_one({"_id": ObjectId(solicitud.usuario_id)})
        if usuario:
            nuevos_dias = (usuario.get("dias_reembolsados", 0) + diferencia)
            await users_collection.update_one(
                {"_id": ObjectId(solicitud.usuario_id)},
                {"$set": {"dias_reembolsados": max(0, nuevos_dias)}}
            )
    
    # Validar que solo se modifique descuento para permisos
    if update_data.descuento is not None and solicitud.tipo != TipoSolicitud.PERMISO:
        raise ValueError("El descuento solo puede modificarse en solicitudes de permiso")
    
    # Manejo de estado
    if update_data.estado:
        update_dict["estado"] = update_data.estado
        if update_data.estado == EstadoSolicitud.APROBADA:
            update_dict["fecha_aprobacion"] = now
            update_dict["aprobado_por_id"] = modificador_id
    
    # Manejo de fechas/horas
    if update_data.fecha_desde or update_data.fecha_hasta:
        if solicitud.tipo == TipoSolicitud.VACACIONES:
            if update_data.fecha_desde:
                update_dict["detalle.desde_dia"] = update_data.fecha_desde
            if update_data.fecha_hasta:
                update_dict["detalle.hasta_dia"] = update_data.fecha_hasta
        else:  # Permiso u Hoja de Ruta
            if update_data.fecha_desde:
                update_dict["detalle.desde_hora"] = update_data.fecha_desde
            if update_data.fecha_hasta:
                update_dict["detalle.hasta_hora"] = update_data.fecha_hasta
    
    # Reembolso (horas)
    if update_data.reembolso is not None:
        update_dict["reembolso"] = max(0, update_data.reembolso)  # No negativo
    
    # Descuento (solo para permisos)
    if update_data.descuento is not None and solicitud.tipo == TipoSolicitud.PERMISO:
        update_dict["detalle.descuento"] = update_data.descuento
    
    # Observaciones
    if update_data.observaciones:
        update_dict["observaciones"] = update_data.observaciones
    
    # Aplicar cambios
    result = await solicitudes_collection.update_one(
        {"_id": ObjectId(solicitud_id)},
        {"$set": update_dict}
    )
    
    if updated_solicitud:
        await socket_manager.notify_solicitud_update(
            updated_solicitud.dict(),
            updated_solicitud.usuario_id,
            updated_solicitud.jefe_id
        )
    
    if result.modified_count == 1:
        updated_solicitud = await obtener_solicitud_por_id(solicitud_id)
        if updated_solicitud and updated_solicitud.estado == EstadoSolicitud.APROBADA:
            await actualizar_dias_usuario(updated_solicitud)
        
        return updated_solicitud
    return None

async def obtener_solicitud_por_id(solicitud_id: str) -> Optional[SolicitudInDB]:
    """Obtiene una solicitud por su ID"""
    if not ObjectId.is_valid(solicitud_id):
        return None
    solicitud = await solicitudes_collection.find_one({"_id": ObjectId(solicitud_id)})
    if solicitud:
        return SolicitudInDB(**solicitud, id=str(solicitud["_id"]))
    return None

async def listar_todas_solicitudes() -> List[SolicitudInDB]:
    """Obtiene todas las solicitudes"""
    solicitudes = []
    async for solicitud in solicitudes_collection.find().sort("fecha_solicitud", -1):
        solicitudes.append(SolicitudInDB(**solicitud, id=str(solicitud["_id"])))
    return solicitudes

async def listar_solicitudes_por_usuario(
    usuario_id: str, 
    estado: Optional[EstadoSolicitud] = None,
    tipo: Optional[TipoSolicitud] = None,
    pagina: int = 1,
    por_pagina: int = 10
) -> Dict[str, Union[int, List[SolicitudInDB]]]:
    query = {"usuario_id": usuario_id}
    
    if estado:
        query["estado"] = estado.value
    if tipo:
        query["tipo"] = tipo.value
    
    total = await solicitudes_collection.count_documents(query)
    
    solicitudes = []
    skip = (pagina - 1) * por_pagina
    
    async for solicitud in solicitudes_collection.find(query).skip(skip).limit(por_pagina).sort("fecha_solicitud", -1):
        solicitudes.append(SolicitudInDB(**solicitud, id=str(solicitud["_id"])))
    
    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "solicitudes": solicitudes
    }
    
async def obtener_solicitudes_por_jefe(
    jefe_id: str, 
    estado: Optional[EstadoSolicitud] = None,
    tipo: Optional[TipoSolicitud] = None,
    pagina: int = 1,
    por_pagina: int = 10
) -> Dict[str, Union[int, List[SolicitudInDB]]]:
    query = {"jefe_id": jefe_id}
    
    if estado:
        query["estado"] = estado.value
    if tipo:
        query["tipo"] = tipo.value
    
    total = await solicitudes_collection.count_documents(query)
    
    solicitudes = []
    skip = (pagina - 1) * por_pagina
    
    async for solicitud in solicitudes_collection.find(query).skip(skip).limit(por_pagina).sort("fecha_solicitud", -1):
        solicitudes.append(SolicitudInDB(**solicitud, id=str(solicitud["_id"])))
    
    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "solicitudes": solicitudes
    }
    
def calcular_horas_laborables(desde: datetime, hasta: datetime) -> float:
    """
    Calcula las horas laborables entre dos fechas (8 horas por día laborable)
    Considera que cada mes tiene 22 días laborables de 8 horas cada uno
    """
    # Definir horario laboral (8 horas por día)
    hora_inicio = time(8, 0)
    hora_fin = time(16, 0)
    
    # Si es el mismo día
    if desde.date() == hasta.date():
        if desde.weekday() >= 5:  # Fin de semana
            return 0
        # Calcular horas dentro del día
        inicio = max(desde.time(), hora_inicio)
        fin = min(hasta.time(), hora_fin)
        if inicio >= fin:
            return 0
        return (datetime.combine(desde.date(), fin) - datetime.combine(desde.date(), inicio)).total_seconds() / 3600
    
    # Para rangos de múltiples días
    total_horas = 0
    for dt in rrule.rrule(rrule.DAILY, dtstart=desde, until=hasta):
        if dt.weekday() >= 5:  # Fin de semana
            continue
        
        # Primer día
        if dt.date() == desde.date():
            inicio = max(desde.time(), hora_inicio)
            fin = hora_fin
            if inicio < fin:
                total_horas += (datetime.combine(dt.date(), fin) - datetime.combine(dt.date(), inicio)).total_seconds() / 3600
        # Último día
        elif dt.date() == hasta.date():
            inicio = hora_inicio
            fin = min(hasta.time(), hora_fin)
            if inicio < fin:
                total_horas += (datetime.combine(dt.date(), fin) - datetime.combine(dt.date(), inicio)).total_seconds() / 3600
        # Días intermedios completos
        else:
            total_horas += 8  # 8 horas por día laborable
    
    return total_horas

async def calcular_tiempo_solicitud(solicitud: SolicitudInDB) -> float:
    """
    Calcula el tiempo utilizado en horas
    - Vacaciones: días completos * 8 horas
    - Hoja de ruta/Permiso: diferencia directa en horas
    """
    if solicitud.tipo == TipoSolicitud.VACACIONES:
        detalle = solicitud.detalle
        delta = detalle.hasta_dia - detalle.desde_dia
        return (delta.days + 1) * 8  # Incluye ambos días extremos, 8 horas por día
    elif solicitud.tipo in [TipoSolicitud.HOJA_RUTA, TipoSolicitud.PERMISO]:
        detalle = solicitud.detalle
        delta = detalle.hasta_hora - detalle.desde_hora
        return delta.total_seconds() / 3600  # Devuelve horas decimales
    return 0

async def actualizar_dias_usuario(solicitud: SolicitudInDB):
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    """
    Actualiza los días utilizados/reembolsados del usuario según la solicitud
    - Para días utilizados: calcula automáticamente
    - Para reembolsos: usa el valor manual ingresado
    """
    if not solicitud.estado == EstadoSolicitud.APROBADA:
        return
    
    tiempo_horas = await calcular_tiempo_solicitud(solicitud)
    tiempo_dias = tiempo_horas / 8  # Convertir horas a días (8 horas = 1 día)
    
    usuario = await users_collection.find_one({"_id": ObjectId(solicitud.usuario_id)})
    if not usuario:
        return
    
    update_data = {}
    
    # Para días utilizados (automático)
    if solicitud.tipo in [TipoSolicitud.VACACIONES, TipoSolicitud.HOJA_RUTA]:
        update_data["dias_utilizados"] = usuario.get("dias_utilizados", 0) + tiempo_dias
    elif solicitud.tipo == TipoSolicitud.PERMISO and getattr(solicitud.detalle, 'descuento', False):
        update_data["dias_utilizados"] = usuario.get("dias_utilizados", 0) + tiempo_dias
    
    # Para reembolsos (manual)
    if solicitud.reembolso and solicitud.reembolso > 0:
        update_data["dias_reembolsados"] = usuario.get("dias_reembolsados", 0) + solicitud.reembolso
    
    if update_data:
        update_data["updated_at"] = now
        await users_collection.update_one(
            {"_id": ObjectId(solicitud.usuario_id)},
            {"$set": update_data}
        )
        await calcular_vacaciones_usuario(solicitud.usuario_id)
