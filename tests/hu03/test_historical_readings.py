from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime
from main import app
from actions.api.models.models import LecturaOut

client = TestClient(app)

@patch("actions.api.services.lectura_service.ReadingService.get_readings_by_plant", new_callable=AsyncMock)
def test_get_historical_readings(mock_get_readings):
    plant_id = "planta123"

    # Crea un listado de lecturas simuladas (datos históricos)
    lectura_simulada = LecturaOut(
        id="reading001",
        planta_id=plant_id,
        humedad=45.0,
        temperatura=18.5,
        ec=1.1,
        ph=6.3,
        nitrogeno=12.0,
        fosforo=8.0,
        potasio=10.0,
        fecha=datetime.fromisoformat("2025-07-19T22:17:56.854+00:00"),
        notas="Lectura histórica simulada"
    )

    mock_get_readings.return_value = [lectura_simulada]

    # Realiza la petición al endpoint
    response = client.get(f"/readings/plant/{plant_id}")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    lectura = data[0]
    assert lectura["id"] == "reading001"
    assert lectura["humedad"] == 45.0
    assert lectura["temperatura"] == 18.5
    assert lectura["ph"] == 6.3
    assert lectura["nitrogeno"] == 12.0
    assert lectura["fosforo"] == 8.0
    assert lectura["potasio"] == 10.0
    assert lectura["notas"] == "Lectura histórica simulada"
