from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv
from data.db.mongo import init_db, ensure_collections, users_collection
from actions.api.endpoints.lectura_router import router as reading_router  # Cambiado a reading_router
from actions.api.endpoints.auth_router import router as auth_router
from actions.api.endpoints.user_router import router as user_router
from actions.api.services.socket_manager import socket_manager  # WebSockets incluidos
from actions.api.endpoints import websocket_routes  # WebSockets incluidos

load_dotenv()

# Configuración de autenticación (original)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

app = FastAPI(
    title="API Agrícola con WebSockets",  # Título actualizado
    description="API para monitoreo agrícola con WebSockets",  # Descripción actualizada
    version="1.0.0"
)

# Configuración CORS (original)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers (original, con nombres actualizados)
app.include_router(auth_router)
app.include_router(reading_router)
app.include_router(user_router)
app.include_router(websocket_routes.router)

@app.get("/")
def read_root():
    return {"message": "API Agrícola funcionando correctamente"}

# Eventos de inicio (original)
@app.on_event("startup")
async def startup_event():
    await init_db()
    await ensure_collections()

# Funciones de autenticación (original)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = {"username": username, "role": payload.get("role")}
    except JWTError:
        raise credentials_exception
    return token_data

# WebSockets (original)
@app.get("/socket-manager")
def get_socket_manager():
    return socket_manager

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5055)