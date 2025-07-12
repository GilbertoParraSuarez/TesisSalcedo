import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "agricultura_db")

if not MONGO_URI:
    raise ValueError("MONGO_URI no configurada")

client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database(DB_NAME)

async def init_db():
    try:
        await client.admin.command('ping')
        print("✅ MongoDB conectado")
        
        # Índices básicos (opcionales pero recomendados)
        await db.users.create_index("username", unique=True)
        await db.plantas.create_index("nombre")
        await db.lecturas.create_index([("planta_id", 1), ("fecha", -1)])
        
    except Exception as e:
        print(f"❌ Error MongoDB: {e}")
        raise

async def ensure_collections():
    """Crea las colecciones solo si no existen"""
    required_collections = ["users", "plantas", "lecturas"]
    existing_collections = await db.list_collection_names()
    
    for col in required_collections:
        if col not in existing_collections:
            await db.create_collection(col)
            print(f"Colección '{col}' creada")

# Colecciones principales
users_collection = db["users"]
plantas_collection = db["plantas"]
lecturas_collection = db["lecturas"]

# GridFS (opcional)
fs_bucket = AsyncIOMotorGridFSBucket(db)