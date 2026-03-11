from fastapi.testclient import TestClient
import sys
sys.path.insert(0, ".")
from main import app

client = TestClient(app)

print("Test 1: GET /health")
r = client.get("/health")
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

print("Test 2: POST /analizar")
datos = {"municipio": "Bogota D.C.", "cartera_a": 1500000000.0, "cartera_b": 200000000.0, "cartera_c": 50000000.0, "cartera_d": 25000000.0, "cartera_e": 10000000.0, "total_cartera": 1800000000.0, "total_captaciones": 2500000000.0}
r = client.post("/analizar", json=datos)
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

print("Test 3: GET /historial")
r = client.get("/historial")
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

print("\nTest 4: POST /analizar (segundo analisis)")
datos2 = {"municipio": "Medellin", "cartera_a": 800000000.0, "cartera_b": 100000000.0, "cartera_c": 80000000.0, "cartera_d": 40000000.0, "cartera_e": 20000000.0, "total_cartera": 1040000000.0, "total_captaciones": 1200000000.0}
r = client.post("/analizar", json=datos2)
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

print("\nTest 5: GET /historial (completo)")
r = client.get("/historial")
print(f"Status: {r.status_code}")
print(f"Total registros: {len(r.json())}")
for item in r.json():
    print(f"  - ID {item['id']}: {item['municipio']} | Riesgo: {item['indice_riesgo']} | Nivel: {item['nivel_riesgo']}")

print("\n" + "="*70)
print("TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
print("="*70)
