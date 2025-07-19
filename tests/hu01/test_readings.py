from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch

client = TestClient(app)

@patch("actions.api.services.lectura_service.ReadingService.get_readings_by_plant", new_callable=AsyncMock)
def test_get_readings_by_plant(mock_get_readings):
    plant_id = "planta123"

    # Simula datos retornados por la base de datos incluyendo 'id'
    mock_get_readings.return_value = [
        {
            "id": "fakeid123",
            "planta_id": plant_id,
            "humedad": 55.5,
            "temperatura": 22.3,
            "ec": 1.2,
            "ph": 6.8,
            "nitrogeno": 10.0,
            "fosforo": 5.0,
            "potasio": 8.0,
            "fecha": "2025-07-19T21:24:54.401Z",
            "notas": "Lectura simulada"
        }
    ]

    response = client.get(f"/readings/plant/{plant_id}")
    assert response.status_code == 200
    readings = response.json()
    assert isinstance(readings, list)
    for lectura in readings:
        assert "id" in lectura
        assert "planta_id" in lectura
        assert "humedad" in lectura
        assert "ph" in lectura
        assert "temperatura" in lectura
        assert lectura["planta_id"] == plant_id

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

    # Simula la respuesta del servicio incluyendo 'id'
    mock_create_reading.return_value = {
        **payload,
        "id": "fakeid123"
    }

    response = client.post("/readings/", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == "fakeid123"
    for key in payload:
        assert data[key] == payload[key]
