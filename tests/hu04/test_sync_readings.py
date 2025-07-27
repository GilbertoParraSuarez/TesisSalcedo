from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch
from actions.api.models.models import LecturaCreate, LecturaOut
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from tests.test_factories import create_lectura_out

client = TestClient(app)

@patch("actions.api.services.lectura_service.ReadingService.create_reading", new_callable=AsyncMock)
def test_sensor_data_sync(mock_create_reading):
    """
    H.U.04 - Verifica que los datos de sensores se sincronicen y almacenen correctamente en la BD.
    """

    # Simula el payload que llegaría desde el sensor (por WebSocket, API, etc.)
    payload = {
        "planta_id": "planta123",
        "humedad": 60.0,
        "temperatura": 24.5,
        "ec": 1.5,
        "ph": 6.9,
        "nitrogeno": 12.0,
        "fosforo": 6.0,
        "potasio": 9.0,
        "fecha": "2025-07-20T10:00:00.000Z",
        "notas": "Lectura automática"
    }

    lectura_creada = create_lectura_out(payload, lectura_id="syncid123")

    mock_create_reading.return_value = lectura_creada

    # Llama al endpoint que guarda la lectura (simulando la sincronización automática)
    response = client.post("/readings/", json=payload)

    assert response.status_code == 200

    data = response.json()
    expected_json = jsonable_encoder(lectura_creada, by_alias=True)

    assert data == expected_json
