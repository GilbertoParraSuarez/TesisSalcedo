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

    response = client.post("/readings/", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Verifica que los valores retornados sean los mismos
    for key in payload:
        assert data[key] == payload[key] or key == "id"  # Ignora 'id' generado
