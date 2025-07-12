from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Union
from datetime import datetime, timedelta
from pydantic import BaseModel
from actions.api.services.socket_manager import socket_manager
from actions.api.models.models import (
    SolicitudCreate,
    SolicitudInDB,
    TipoSolicitud,
    EstadoSolicitud,
    DetalleHojaRuta,
    DetallePermiso,
    DetalleVacaciones,
    SolicitudUpdate
)
from data.db.mongo import solicitudes_collection,  fs_bucket
from actions.api.services.solicitudes_service import (
    crear_solicitud,
    obtener_solicitud_por_id,
    actualizar_estado_solicitud,
    listar_todas_solicitudes,
    listar_solicitudes_por_usuario,
    obtener_solicitudes_por_jefe,
    modificar_solicitud as svc_modificar
)
from bson import ObjectId

import pytz

ECUADOR_TZ = pytz.timezone("America/Guayaquil")

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

@router.post("/hoja-ruta", response_model=SolicitudInDB)
async def crear_hoja_ruta(
    usuario_id: str,
    jefe_id: str,
    periodo: str,
    detalle: DetalleHojaRuta,
    #current_user: UserInDB = Depends(get_current_active_user)
    ):
    """
    Crea una nueva hoja de ruta
    """
    solicitud_create = SolicitudCreate(
        usuario_id=usuario_id,
        jefe_id=jefe_id,
        tipo=TipoSolicitud.HOJA_RUTA,
        periodo=periodo,
        detalle=detalle
    )
    return await crear_solicitud(solicitud_create)

@router.post("/permiso", response_model=SolicitudInDB)
async def crear_permiso(
    usuario_id: str,
    jefe_id: str,
    periodo: str,
    detalle: DetallePermiso,
    #current_user: UserInDB = Depends(get_current_active_user)
    ):
    """
    Crea un nuevo permiso
    """
    solicitud_create = SolicitudCreate(
        usuario_id=usuario_id,
        jefe_id=jefe_id,
        tipo=TipoSolicitud.PERMISO,
        periodo=periodo,
        detalle=detalle
    )
    return await crear_solicitud(solicitud_create)

@router.post("/vacaciones", response_model=SolicitudInDB)
async def crear_vacaciones(
    usuario_id: str,
    jefe_id: str,
    periodo: str,
    detalle: DetalleVacaciones,
    #current_user: UserInDB = Depends(get_current_active_user)
    ):
    """
    Crea una nueva solicitud de vacaciones
    """
    solicitud_create = SolicitudCreate(
        usuario_id=usuario_id,
        jefe_id=jefe_id,
        tipo=TipoSolicitud.VACACIONES,
        periodo=periodo,
        detalle=detalle
    )
    return await crear_solicitud(solicitud_create)


# Nuevas rutas API
@router.get("/", response_model=List[SolicitudInDB])
async def listar_todas_las_solicitudes(
):
    return await listar_todas_solicitudes()

@router.get("/{solicitud_id}", response_model=SolicitudInDB)
async def obtener_solicitud_por_formulario_id(
    solicitud_id: str,
):
    solicitud = await obtener_solicitud_por_id(solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return solicitud

@router.get("/usuario/{usuario_id}", response_model=Dict[str, Union[int, List[SolicitudInDB]]])
async def listar_solicitudes_usuario(
    usuario_id: str,
    estado: Optional[EstadoSolicitud] = None,
    tipo: Optional[TipoSolicitud] = None,
    pagina: int = 1,
    por_pagina: int = Query(default=10, le=100),
):   
    return await listar_solicitudes_por_usuario(
        usuario_id=usuario_id,
        estado=estado,
        tipo=tipo,
        pagina=pagina,
        por_pagina=por_pagina)


@router.get("/jefe/{jefe_id}", response_model=Dict[str, Union[int, List[SolicitudInDB]]])
async def listar_solicitudes_por_jefe(
    jefe_id: str,
    estado: Optional[EstadoSolicitud] = None,
    tipo: Optional[TipoSolicitud] = None,
    pagina: int = 1,
    por_pagina: int = Query(default=10, le=100),
):

    return await obtener_solicitudes_por_jefe(
        jefe_id=jefe_id,
        estado=estado,
        tipo=tipo,
        pagina=pagina,
        por_pagina=por_pagina
    )

@router.put("/{solicitud_id}", response_model=SolicitudInDB)
async def modificar_solicitud_endpoint(
    solicitud_id: str,
    modificador_id: str,
    update_data: SolicitudUpdate,
):
    solicitud = await svc_modificar(  # cambia el nombre para evitar recursión
        solicitud_id=solicitud_id,
        modificador_id=modificador_id,
        update_data=update_data
    )

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo modificar la solicitud"
        )

    
    await socket_manager.notify_solicitud_update(solicitud=solicitud.dict(), user_id=solicitud.usuario_id, jefe_id=solicitud.jefe_id)
    return solicitud


@router.put("/{solicitud_id}/aprobar", response_model=SolicitudInDB)
async def aprobar_solicitud(
    solicitud_id: str,
    aprobado_por_id: str,
    observaciones: Optional[str] = None,
):
    solicitud = await actualizar_estado_solicitud(
        solicitud_id,
        EstadoSolicitud.APROBADA,
        aprobado_por_id,
        observaciones
    )

    
    await socket_manager.notify_solicitud_update(solicitud=solicitud.dict(), user_id=solicitud.usuario_id, jefe_id=solicitud.jefe_id)
    return solicitud


@router.put("/{solicitud_id}/rechazar", response_model=SolicitudInDB)
async def rechazar_solicitud(
    solicitud_id: str,
    aprobado_por_id: str,
    observaciones: Optional[str] = None,
):
    solicitud = await actualizar_estado_solicitud(
        solicitud_id,
        EstadoSolicitud.RECHAZADA,
        aprobado_por_id,
        observaciones
    )

    
    await socket_manager.notify_solicitud_update(solicitud=solicitud.dict(), user_id=solicitud.usuario_id, jefe_id=solicitud.jefe_id)
    return solicitud

@router.put("/{solicitud_id}/cancelar", response_model=SolicitudInDB)
async def cancelar_solicitud(
    solicitud_id: str,
    observaciones: Optional[str] = None
):
    """
    Cancela una solicitud sin verificación de usuario
    """
    # Verificar que la solicitud existe
    solicitud = await obtener_solicitud_por_id(solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Solo permitir cancelar si está en estado pendiente
    if solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden cancelar solicitudes pendientes"
        )
    now = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    update_data = {
        "estado": EstadoSolicitud.CANCELADA,
        "observaciones": observaciones,
        "fecha_modificacion":now
    }
    
    # Actualizar en base de datos
    result = await solicitudes_collection.update_one(
        {"_id": ObjectId(solicitud_id)},
        {"$set": update_data}
    )
    
    if result.modified_count != 1:
        raise HTTPException(
            status_code=400,
            detail="No se pudo cancelar la solicitud"
        )
        
    solicitud_actualizada = await obtener_solicitud_por_id(solicitud_id)
    
    await socket_manager.notify_solicitud_update(
        solicitud=solicitud_actualizada.dict(), 
        user_id=solicitud_actualizada.usuario_id, 
        jefe_id=solicitud_actualizada.jefe_id
    )
    return await solicitud_actualizada

@router.put("/{solicitud_id}/reembolso", response_model=SolicitudInDB)
async def agregar_reembolso(
    solicitud_id: str,
    modificador_id: str = Query(...),
    monto_reembolso: float = Query(..., ge=0)
):
    # Verificación básica del ID
    try:
        obj_id = ObjectId(solicitud_id)
    except:
        raise HTTPException(400, "ID inválido")

    # Obtener la solicitud
    solicitud = await obtener_solicitud_por_id(obj_id)
    if not solicitud:
        raise HTTPException(404, "Solicitud no encontrada")

    # Verificar estado
    if solicitud.estado not in ["aprobada", "modificada"]:
        raise HTTPException(400, "Solo solicitudes aprobadas pueden tener reembolso")

    # Actualizar el reembolso
    update_data = {
        "reembolso": monto_reembolso,
        "modificador_id": modificador_id,
        "fecha_modificacion": datetime.now()
    }

    result = await solicitudes_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )

    if result.modified_count != 1:
        raise HTTPException(400, "No se pudo actualizar el reembolso")
    
    await socket_manager.notify_solicitud_update(solicitud=solicitud.dict(), user_id=solicitud.usuario_id, jefe_id=solicitud.jefe_id)
    return await obtener_solicitud_por_id(obj_id)

class DescuentoRequest(BaseModel):
    descuento: bool
    modificador_id: str
    cantidadDias: float | None = None


@router.put("/{solicitud_id}/fechas", response_model=SolicitudInDB)
async def modificar_fechas_solicitud(
    solicitud_id: str,
    request_data: SolicitudUpdate = Body(...)
):
    """Modifica las fechas/horas de una solicitud según su tipo"""
    try:
        obj_id = ObjectId(solicitud_id)
    except:
        raise HTTPException(status_code=400, detail="ID de solicitud inválido")

    # Validar que al menos una fecha viene en el request
    if not request_data.detalle or (
        not request_data.detalle.desde_hora and 
        not request_data.detalle.hasta_hora and
        not request_data.detalle.desde_dia and 
        not request_data.detalle.hasta_dia
    ):
        raise HTTPException(
            status_code=400,
            detail="Se requiere al menos una fecha/hora para modificar"
        )

    solicitud = await obtener_solicitud_por_id(obj_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # Preparar actualización
    update_dict = {
        "modificado_por_id": request_data.modificador_id,
        "fecha_modificacion": datetime.now(),
        "estado": EstadoSolicitud.MODIFICADA
    }

    # Manejo de fechas según tipo de solicitud
    if solicitud.tipo == "vacaciones":
        if request_data.detalle.desde_dia:
            update_dict["detalle.desde_dia"] = request_data.detalle.desde_dia
        if request_data.detalle.hasta_dia:
            update_dict["detalle.hasta_dia"] = request_data.detalle.hasta_dia
    else:  # Permiso u Hoja de Ruta
        if request_data.detalle.desde_hora:
            update_dict["detalle.desde_hora"] = request_data.detalle.desde_hora
        if request_data.detalle.hasta_hora:
            update_dict["detalle.hasta_hora"] = request_data.detalle.hasta_hora

    result = await solicitudes_collection.update_one(
        {"_id": obj_id},
        {"$set": update_dict}
    )
    

    if result.modified_count == 1:
        await socket_manager.notify_solicitud_update(solicitud=solicitud.dict(), user_id=solicitud.usuario_id, jefe_id=solicitud.jefe_id)
        return await obtener_solicitud_por_id(obj_id)
    raise HTTPException(status_code=400, detail="No se pudieron actualizar las fechas")

@router.put("/{solicitud_id}/descontar", response_model=SolicitudInDB)
async def descontar_permiso(
    solicitud_id: str,
    request_data: DescuentoRequest = Body(...)
):
    """Activa/desactiva descuento de un permiso a vacaciones"""
    try:
        obj_id = ObjectId(solicitud_id)
    except:
        raise HTTPException(status_code=400, detail="ID de solicitud inválido")

    # Validación de cantidadDias
    if request_data.descuento and request_data.cantidadDias is None:
        raise HTTPException(
            status_code=400,
            detail="cantidadDias es requerido cuando descuento está activado"
        )

    solicitud = await obtener_solicitud_por_id(obj_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if solicitud.tipo != "permiso":
        raise HTTPException(
            status_code=400,
            detail="Solo permisos pueden tener descuento a vacaciones"
        )

    # Preparar actualización
    update_dict = {
        "modificado_por_id": request_data.modificador_id,
        "fecha_modificacion": datetime.now(),
        "detalle.descuento": request_data.descuento,
        "detalle.cantDesc": request_data.cantidadDias if request_data.descuento else 0
    }

    result = await solicitudes_collection.update_one(
        {"_id": obj_id},
        {"$set": update_dict}
    )
    
    if result.modified_count == 1:
        await socket_manager.notify_solicitud_update(solicitud=solicitud.dict(), user_id=solicitud.usuario_id, jefe_id=solicitud.jefe_id)
        return await obtener_solicitud_por_id(obj_id)
    raise HTTPException(status_code=400, detail="No se pudo actualizar el descuento")

@router.post("/archivo/upload")
async def subir_archivo(archivo: UploadFile = File(...)):
    contents = await archivo.read()
    file_id = await fs_bucket.upload_from_stream(
        archivo.filename,
        contents,
        metadata={"contentType": archivo.content_type}
    )
    return {"archivo_id": str(file_id), "filename": archivo.filename}

@router.get("/archivo/download/{archivo_id}")
async def descargar_archivo(archivo_id: str):
    try:
        object_id = ObjectId(archivo_id)
        stream = await fs_bucket.open_download_stream(object_id)
        headers = {
            "Content-Disposition": f'attachment; filename="{stream.filename}"'
        }
        return StreamingResponse(stream, media_type=stream.metadata.get("contentType"), headers=headers)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    