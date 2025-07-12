from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from data.db.mongo import db
from actions.api.models.models import LecturaCreate, LecturaOut, LecturaUpdate

class ReadingService:
    def __init__(self):
        self.readings_collection = db["lecturas"]
        self.plants_collection = db["plantas"]

    async def create_reading(self, reading: LecturaCreate) -> Optional[LecturaOut]:
        db_reading = reading.dict()
        db_reading["fecha"] = datetime.utcnow()
        
        # Actualizar última lectura en la planta
        await self.plants_collection.update_one(
            {"_id": ObjectId(reading.planta_id)},
            {"$set": {"ultima_lectura": db_reading["fecha"]}}
        )
        
        result = await self.readings_collection.insert_one(db_reading)
        created_reading = await self.readings_collection.find_one({"_id": result.inserted_id})
        return LecturaOut(**created_reading, id=str(created_reading["_id"]))

    async def get_readings_by_plant(self, plant_id: str) -> List[LecturaOut]:
        if not ObjectId.is_valid(plant_id):
            return []
        
        readings = []
        async for reading in self.readings_collection.find({"planta_id": plant_id}):
            readings.append(LecturaOut(**reading, id=str(reading["_id"])))
        return readings

    async def get_reading_by_id(self, reading_id: str) -> Optional[LecturaOut]:
        if not ObjectId.is_valid(reading_id):
            return None
        reading = await self.readings_collection.find_one({"_id": ObjectId(reading_id)})
        if not reading:
            return None
        return LecturaOut(**reading, id=str(reading["_id"]))