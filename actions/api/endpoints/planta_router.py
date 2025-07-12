from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from actions.api.services.auth_service import AuthService
from actions.api.services.planta_service import PlantService
from actions.api.models.models import PlantaOut, PlantaCreate, PlantaUpdate, UserOut

router = APIRouter(prefix="/plants", tags=["plants"])
auth_service = AuthService()
plant_service = PlantService()

@router.get("/", response_model=List[PlantaOut])
async def list_plants(
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    return await plant_service.list_plants()

@router.post("/", response_model=PlantaOut)
async def create_plant(
    plant: PlantaCreate,
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    # Solo admins e investigadores pueden crear plantas
    if current_user.role not in ["administradores", "investigadores"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear plantas"
        )
    
    created_plant = await plant_service.create_plant(plant)
    if not created_plant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la planta"
        )
    return created_plant

@router.get("/{plant_id}", response_model=PlantaOut)
async def get_plant(
    plant_id: str,
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    plant = await plant_service.get_plant_by_id(plant_id)
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planta no encontrada"
        )
    return plant

@router.put("/{plant_id}", response_model=PlantaOut)
async def update_plant(
    plant_id: str,
    plant_data: PlantaUpdate,
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    # Solo admins e investigadores pueden actualizar plantas
    if current_user.role not in ["administradores", "investigadores"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar plantas"
        )
    
    updated_plant = await plant_service.update_plant(plant_id, plant_data)
    if not updated_plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planta no encontrada"
        )
    return updated_plant

@router.delete("/{plant_id}")
async def delete_plant(
    plant_id: str,
    current_user: UserOut = Depends(auth_service.get_current_user)
):
    # Solo admins pueden eliminar plantas
    if current_user.role != "administradores":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar plantas"
        )
    
    if not await plant_service.delete_plant(plant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planta no encontrada"
        )
    return {"message": "Planta eliminada correctamente"}