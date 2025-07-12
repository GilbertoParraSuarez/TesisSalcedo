from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

# from actions.api.services.auth_service import AuthService
from actions.api.services.lectura_service import ReadingService
from actions.api.models.models import LecturaOut, LecturaCreate, UserOut

router = APIRouter(prefix="/readings", tags=["readings"])
# auth_service = AuthService()
reading_service = ReadingService()

@router.get("/plant/{plant_id}", response_model=List[LecturaOut])
async def get_plant_readings(
    plant_id: str,
    # current_user: UserOut = Depends(auth_service.get_current_user)
):
    readings = await reading_service.get_readings_by_plant(plant_id)
    if not readings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron lecturas para esta planta"
        )
    return readings

@router.post("/", response_model=LecturaOut)
async def create_reading(
    reading: LecturaCreate,
    # current_user: UserOut = Depends(auth_service.get_current_user)
):
    # TODO: Implementar autenticación
    # Solo agricultores e investigadores pueden crear lecturas
    # if current_user.role not in ["agricultores", "investigadores"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="No tienes permisos para crear lecturas"
    #     )
    
    created_reading = await reading_service.create_reading(reading)
    if not created_reading:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la lectura"
        )
    return created_reading