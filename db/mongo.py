import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI no configurada")

client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database("chat_db")
fs_bucket = AsyncIOMotorGridFSBucket(db)

async def init_db():
    try:
        await client.admin.command('ping')
        print("✅ MongoDB conectado")
        
        # Crear índices existentes
        await db.chats.create_index("user_id")
        await db.chats.create_index([("messages.timestamp", 1)])
        
        # Nuevos índices para solicitudes
        await db.solicitudes.create_index("usuario_id")
        await db.solicitudes.create_index("estado")
        await db.solicitudes.create_index("tipo")
        await db.solicitudes.create_index("fecha_solicitud")
        
        # Crear índices para usuarios
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        await db.users.create_index("role")
        await db.users.create_index("disabled")
        
         # Índices para las opciones de usuario
        await db.user_options.create_index("option_type")
        await db.user_options.create_index("is_active")
        await db.user_options.create_index([("option_type", 1), ("is_active", 1)])  # Índice compuesto
        
    except Exception as e:
        print(f"❌ Error MongoDB: {e}")
        raise

async def ensure_collections():
    if "chats" not in await db.list_collection_names():
        await db.create_collection("chats")
        print("Colección 'chats' creada")

    if "solicitudes" not in await db.list_collection_names():
        await db.create_collection("solicitudes")
        print("Colección 'solicitudes' creada")
        
    if "users" not in await db.list_collection_names():
        await db.create_collection("users")
        print("Colección 'users' creada")
    
    if "user_options" not in await db.list_collection_names():
        await db.create_collection("user_options")
        print("Colección 'user_options' creada")


# Colecciones existentes
chats_collection = db["chats"]
solicitudes_collection = db["solicitudes"]

# Colección para usuarios
users_collection = db["users"]

options_collection = db["user_options"]

# GridFS
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
fs_bucket = AsyncIOMotorGridFSBucket(db)