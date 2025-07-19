from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_readings_by_plant():
    plant_id = "planta123"  # Usa un ID conocido o de prueba
    response = client.get(f"/readings/plant/{plant_id}")
    
    if response.status_code == 404:
        assert response.json()["detail"] == "No se encontraron lecturas para esta planta"
    else:
        assert response.status_code == 200
        readings = response.json()
        assert isinstance(readings, list)
        for lectura in readings:
            assert "humedad" in lectura
            assert "ph" in lectura
            assert "temperatura" in lectura

def test_create_reading():
    payload = {
        "plant_id": "planta123",
        "humedad": 55.5,
        "ph": 6.8,
        "temperatura": 22.3
    }
    response = client.post("/readings/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["plant_id"] == payload["plant_id"]
    assert data["humedad"] == payload["humedad"]
    assert data["ph"] == payload["ph"]
    assert data["temperatura"] == payload["temperatura"]
