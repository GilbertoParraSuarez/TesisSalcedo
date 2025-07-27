from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch
from actions.api.models.models import LecturaOut
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from tests.test_factories import create_lectura_out

client = TestClient(app)

@patch("actions.api.services.lectura_service.ReadingService.get_readings_by_plant", new_callable=AsyncMock)
def test_get_readings_by_plant(mock_get_readings):
    plant_id = "planta123"

    lectura = LecturaOut(
        id="id01",
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

    mock_get_readings.return_value = [lectura]

    response = client.get(f"/readings/plant/{plant_id}")
    assert response.status_code == 200

    readings = response.json()
    assert isinstance(readings, list)

    expected_json = jsonable_encoder(lectura, by_alias=True)

    for lectura_json in readings:
        assert lectura_json == expected_json

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

    lectura_creada = create_lectura_out(payload, lectura_id="id01")


    mock_create_reading.return_value = lectura_creada

    response = client.post("/readings/", json=payload)
    assert response.status_code == 200

    data = response.json()

    expected_json = jsonable_encoder(lectura_creada, by_alias=True)

    assert data == expected_json
