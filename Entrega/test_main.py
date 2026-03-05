from fastapi.testclient import TestClient
from main import app, historial_analisis

client = TestClient(app)

def setup_function():
    # Limpiar base de datos en memoria antes de cada test
    historial_analisis.clear()
    import main
    main.contador_id = 0

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "🏦 API de Riesgo Crediticio" in data["mensaje"]

def test_crear_analisis_valido():
    payload = {
        "municipio": "Bogota D.C.",
        "cartera_a": 1500000000,
        "cartera_b": 200000000,
        "cartera_c": 50000000,
        "cartera_d": 25000000,
        "cartera_e": 10000000,
        "total_cartera": 1800000000,
        "total_captaciones": 2500000000
    }
    response = client.post("/analizar", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["municipio"] == "Bogota D.C."
    assert data["nivel_riesgo"] == "riesgo_moderado"
    # Indice = (C+D+E) / total = 85m / 1800m = ~0.0472
    assert "mensaje" in data

def test_crear_analisis_invalido():
    payload = {
        "municipio": "Bogota D.C.",
        "total_cartera": "texto_invalido" # Esto debería causar un error 422 de Pydantic
    }
    response = client.post("/analizar", json=payload)
    assert response.status_code == 422 

def test_listar_historial_vacio():
    response = client.get("/historial")
    assert response.status_code == 200
    assert response.json() == []

def test_listar_y_obtener_historial_con_datos():
    # Primero insertar uno
    payload = {
        "municipio": "Medellin",
        "total_cartera": 1000,
        "cartera_a": 1000,
        "cartera_b": 0,
        "cartera_c": 0,
        "cartera_d": 0,
        "cartera_e": 0
    }
    client.post("/analizar", json=payload)
    
    # Listar
    response = client.get("/historial")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["municipio"] == "Medellin"
    
    # Obtener especifico
    analisis_id = data[0]["id"]
    response = client.get(f"/historial/{analisis_id}")
    assert response.status_code == 200
    data_esp = response.json()
    assert data_esp["municipio"] == "Medellin"
    
def test_obtener_analisis_no_existente():
    response = client.get("/historial/999")
    assert response.status_code == 404

def test_eliminar_analisis():
    # Insertar uno
    payload = {
        "municipio": "Cali",
        "total_cartera": 5000,
        "cartera_a": 5000,
        "cartera_b": 0,
        "cartera_c": 0,
        "cartera_d": 0,
        "cartera_e": 0
    }
    client.post("/analizar", json=payload)
    
    # Eliminarlo (id = 1 porque borramos db antes de cada test en setup)
    response = client.delete("/historial/1")
    assert response.status_code == 200
    assert response.json()["id_eliminado"] == 1
    
    # Verificar que ya no esta
    response_get = client.get("/historial/1")
    assert response_get.status_code == 404
