from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime
from data.db.mongo import options_collection
from actions.api.models.models import UserOption, UserOptionResponse

class OptionService:
# En option_service.py, modifica el método create_option
    @staticmethod
    async def create_option(option: UserOption):
        try:
            option_dict = option.dict()
            option_dict.setdefault("is_active", True)
            result = await options_collection.insert_one(option_dict)
            inserted_option = await options_collection.find_one({"_id": result.inserted_id})
            inserted_option["id"] = str(inserted_option["_id"])
            return inserted_option
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_options_by_type(option_type: str):
        try:
            options = []
            async for option in options_collection.find({"option_type": option_type, "is_active": True}):
                option["id"] = str(option["_id"])
                options.append(option)
            return options
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_all_options():
        try:
            options = []
            async for option in options_collection.find({"is_active": True}):
                option["id"] = str(option["_id"])
                options.append(option)
            return options
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def update_option(option_id: str, option_data: dict):
        try:
            result = await options_collection.update_one(
                {"_id": ObjectId(option_id)},
                {"$set": option_data}
            )
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Opción no encontrada")
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def delete_option(option_id: str):
        try:
            # Borrado lógico
            result = await options_collection.update_one(
                {"_id": ObjectId(option_id)},
                {"$set": {"is_active": False}}
            )
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Opción no encontrada")
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))