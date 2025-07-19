from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch
from actions.api.models.models import LecturaOut
from datetime import datetime

client = TestClient(app)

@patch("actions.api.services.lectura_service.ReadingService.get_readings_by_plant", new_callable=AsyncMock)
def test_get_readings_by_plant(mock_get_readings):
    plant_id = "planta123"

    # Crea un objeto LecturaOut simulado
    lectura = LecturaOut(
        id="fakeid123",
        planta_id=plant_id,
        humedad=55.5,
        temperatura=22.3,
        ec=1.2,
        ph=6.8,
        nitrogeno=10.0,
        fosforo=5.0,
        potasio=8.0,
        fecha=datetime.fromisoformat("2025-07-19T21:24:54.401000+00:00"),
        notas="Lectura simulada"
    )

    # Simula el retorno del servicio usando model_dump(by_alias=True)
    mock_get_readings.return_value = [lectura]

    response = client.get(f"/readings/plant/{plant_id}")
    assert response.status_code == 200

    readings = response.json()
    assert isinstance(readings, list)

    for lectura_json in readings:
        assert "id" in lectura_json
        assert "planta_id" in lectura_json
        assert lectura_json["planta_id"] == plant_id
        assert "humedad" in lectura_json
        assert "ph" in lectura_json
        assert "temperatura" in lectura_json

@patch("actions.api.services.lectura_service.ReadingService.create_reading", new_callable=AsyncMock)
def test_create_reading(mock_create_reading):
    payload = {
        "planta_id": "planta123",
        "humedad": 55.5,
        "temperatura": 22.3,
        "ec": 1.2,
        "ph": 6.8,
        "nitrogeno": 10.0,
        "fosforo": 5.0,
        "potasio": 8.0,
        "fecha": "2025-07-19T21:24:54.401Z",
        "notas": "Lectura de prueba"
    }

    # Simula la respuesta del servicio con LecturaOut
    lectura_creada = LecturaOut(
        id="fakeid123",
        planta_id=payload["planta_id"],
        humedad=payload["humedad"],
        temperatura=payload["temperatura"],
        ec=payload["ec"],
        ph=payload["ph"],
        nitrogeno=payload["nitrogeno"],
        fosforo=payload["fosforo"],
        potasio=payload["potasio"],
        fecha=datetime.fromisoformat(payload["fecha"].replace("Z", "+00:00")),
        notas=payload["notas"]
    )

    mock_create_reading.return_value = lectura_creada

    response = client.post("/readings/", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "fakeid123"
    assert data["planta_id"] == payload["planta_id"]
    assert data["humedad"] == payload["humedad"]
    assert data["temperatura"] == payload["temperatura"]
    assert data["ec"] == payload["ec"]
    assert data["ph"] == payload["ph"]
    assert data["nitrogeno"] == payload["nitrogeno"]
    assert data["fosforo"] == payload["fosforo"]
    assert data["potasio"] == payload["potasio"]
    assert data["notas"] == payload["notas"]
