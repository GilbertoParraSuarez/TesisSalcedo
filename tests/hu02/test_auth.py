from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from jose import jwt
from actions.api.models.models import UserInDB, UserOut
import os

client = TestClient(app)

SECRET_KEY = os.getenv("SECRET_KEY", "testsecret")
ALGORITHM = "HS256"
FAKE_HASHED_PW = os.getenv("TEST_FAKE_HASHED_PW", "fakehashed")

def fake_jwt_token(username, role):
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@patch("actions.api.services.auth_service.AuthService.authenticate_user", new_callable=AsyncMock)
def test_login_success(mock_authenticate):
    user_mock = UserInDB(
        id="user123",
        username="admin",
        nombre="Admin",
        apellido="Test",
        creado_en=datetime.utcnow(),
        role="administradores",
        hashed_password=FAKE_HASHED_PW
    )

    mock_authenticate.return_value = user_mock

    response = client.post("/auth/token", data={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "administradores"
    assert data["user_data"]["username"] == "admin"

@patch("actions.api.services.user_service.UserService.get_full_user", new_callable=AsyncMock)
@patch("actions.api.services.user_service.UserService.create_user", new_callable=AsyncMock)
def test_register_user(mock_create_user, mock_get_user):
    mock_get_user.return_value = None

    user_created = UserOut(
        id="user123",
        username="nuevo",
        nombre="Nuevo",
        apellido="Usuario",
        creado_en=datetime.utcnow(),
        role="administradores"
    )

    mock_create_user.return_value = user_created

    response = client.post("/auth/register", json={
        "username": "nuevo",
        "password": "password123",
        "nombre": "Nuevo",
        "apellido": "Usuario",
        "role": "administradores"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "nuevo"
    assert data["role"] == "administradores"

def test_get_current_user():
    # Simula un usuario autenticado
    user_mock = UserOut(
        id="user123",
        username="admin",
        nombre="Admin",
        apellido="Test",
        creado_en=datetime.utcnow(),
        role="administradores"
    )

    # Sobrescribe exactamente la dependencia del router auth_router
    from actions.api.endpoints.auth_router import auth_service
    app.dependency_overrides[auth_service.get_current_user] = lambda: user_mock

    token = fake_jwt_token("admin", "administradores")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "administradores"

    # Limpia overrides al final
    app.dependency_overrides = {}
