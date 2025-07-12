from fastapi import APIRouter, HTTPException
from actions.api.models.models import UserOptionCreate, UserOptionResponse
from actions.api.services.option_service import OptionService

router = APIRouter(prefix="/options", tags=["options"])

@router.post("/", response_model=UserOptionResponse)
async def create_option(option: UserOptionCreate):
    try:
        return await OptionService.create_option(option)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{option_type}", response_model=list[UserOptionResponse])
async def get_options(option_type: str):
    try:
        return await OptionService.get_options_by_type(option_type)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=list[UserOptionResponse])
async def get_all_options():
    try:
        return await OptionService.get_all_options()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{option_id}", response_model=dict)
async def update_option(option_id: str, option_data: dict):
    try:
        return await OptionService.update_option(option_id, option_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{option_id}", response_model=dict)
async def delete_option(option_id: str):
    try:
        return await OptionService.delete_option(option_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))