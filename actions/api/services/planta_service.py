from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from data.db.mongo import db
from actions.api.models.models import PlantaCreate, PlantaOut, PlantaUpdate

class PlantService:
    def __init__(self):
        self.plants_collection = db["plantas"]

    async def create_plant(self, plant: PlantaCreate) -> Optional[PlantaOut]:
        db_plant = plant.dict()
        db_plant["creado_en"] = datetime.utcnow()
        
        result = await self.plants_collection.insert_one(db_plant)
        created_plant = await self.plants_collection.find_one({"_id": result.inserted_id})
        return PlantaOut(**created_plant, id=str(created_plant["_id"]))

    async def get_plant_by_id(self, plant_id: str) -> Optional[PlantaOut]:
        if not ObjectId.is_valid(plant_id):
            return None
        plant = await self.plants_collection.find_one({"_id": ObjectId(plant_id)})
        if not plant:
            return None
        return PlantaOut(**plant, id=str(plant["_id"]))

    async def list_plants(self) -> List[PlantaOut]:
        plants = []
        async for plant in self.plants_collection.find():
            plants.append(PlantaOut(**plant, id=str(plant["_id"])))
        return plants

    async def update_plant(self, plant_id: str, plant_data: PlantaUpdate) -> Optional[PlantaOut]:
        if not ObjectId.is_valid(plant_id):
            return None
        
        update_data = plant_data.dict(exclude_unset=True)
        
        if not update_data:
            return None
        
        result = await self.plants_collection.update_one(
            {"_id": ObjectId(plant_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 1:
            updated_plant = await self.plants_collection.find_one({"_id": ObjectId(plant_id)})
            return PlantaOut(**updated_plant, id=str(updated_plant["_id"]))
        return None

    async def delete_plant(self, plant_id: str) -> bool:
        if not ObjectId.is_valid(plant_id):
            return False
        result = await self.plants_collection.delete_one({"_id": ObjectId(plant_id)})
        return result.deleted_count == 1