from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from data.db.mongo import db
from actions.api.models.models import UserCreate, UserOut, UserUpdate, UserInDB

class UserService:
    def __init__(self):
        self.users_collection = db["users"]

    async def create_user(self, user: UserCreate) -> Optional[UserOut]:
        existing_user = await self.users_collection.find_one({"username": user.username})
        if existing_user:
            return None
        
        db_user = user.dict()
        db_user["hashed_password"] = AuthService().get_password_hash(user.password)
        db_user["creado_en"] = datetime.utcnow()
        
        result = await self.users_collection.insert_one(db_user)
        created_user = await self.users_collection.find_one({"_id": result.inserted_id})
        return UserOut(**created_user, id=str(created_user["_id"]))

    async def get_user_by_id(self, user_id: str) -> Optional[UserOut]:
        if not ObjectId.is_valid(user_id):
            return None
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        return UserOut(**user, id=str(user["_id"]))

    async def get_full_user(self, username: str) -> Optional[UserInDB]:
        user = await self.users_collection.find_one({"username": username})
        if not user:
            return None
        return UserInDB(**user, id=str(user["_id"]))

    async def list_users(self) -> List[UserOut]:
        users = []
        async for user in self.users_collection.find():
            users.append(UserOut(**user, id=str(user["_id"])))
        return users

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[UserOut]:
        if not ObjectId.is_valid(user_id):
            return None
        
        update_data = user_data.dict(exclude_unset=True, exclude={"password"})
        
        if user_data.password:
            update_data["hashed_password"] = AuthService().get_password_hash(user_data.password)
        
        if not update_data:
            return None
        
        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 1:
            updated_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            return UserOut(**updated_user, id=str(updated_user["_id"]))
        return None

    async def delete_user(self, user_id: str) -> bool:
        if not ObjectId.is_valid(user_id):
            return False
        result = await self.users_collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count == 1