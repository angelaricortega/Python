"""
tests/test_endpoints.py — Pruebas de integración para los endpoints FastAPI.

Utiliza TestClient de Starlette (incluido en FastAPI) para simular
requests HTTP sin levantar un servidor real.

Cubre:
    - POST /encuestas/     → 201 Created, 422 Unprocessable Entity
    - GET  /encuestas/     → 200 OK (lista vacía y con datos)
    - GET  /encuestas/{id} → 200 OK, 404 Not Found
    - PUT  /encuestas/{id} → 200 OK, 404 Not Found
    - DELETE /encuestas/{id} → 204 No Content, 404 Not Found
    - GET /encuestas/estadisticas/ → 200 OK
    - GET / → 200 OK (health check)
    - Manejo personalizado de errores HTTP 422

Ejecución:
    pytest tests/test_endpoints.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from main import app, db_encuestas

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Payload válido reutilizable
# ─────────────────────────────────────────────────────────────────────────────

ENCUESTA_VALIDA = {
    "encuestado": {
        "nombre": "Laura Daniela Jiménez",
        "edad": 32,
        "genero": "femenino",
        "estrato": 3,
        "departamento": "Cundinamarca",
        "municipio": "Bogotá",
        "nivel_educativo": "universitario",
        "ocupacion": "Abogada",
    },
    "respuestas": [
        {
            "pregunta_id": 1,
            "enunciado": "¿Qué tan satisfecho está con el servicio de salud?",
            "tipo_pregunta": "likert",
            "valor": 4,
        },
        {
            "pregunta_id": 2,
            "enunciado": "Nivel de confianza en las instituciones (%)",
            "tipo_pregunta": "porcentaje",
            "valor": 60.0,
        },
    ],
    "observaciones_generales": "Encuesta aplicada en zona urbana.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: limpiar base de datos antes y después de cada test
# Garantiza aislamiento total entre pruebas (tests independientes)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def limpiar_repositorio():
    """Vacía el repositorio en memoria antes y después de cada test."""
    db_encuestas.clear()
    yield
    db_encuestas.clear()


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: Health Check
# ══════════════════════════════════════════════════════════════════════════════

def test_health_check_retorna_200():
    """GET / debe retornar 200 con estado 'activo'."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "activo"
    assert "documentacion_swagger" in data


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: POST /encuestas/
# ══════════════════════════════════════════════════════════════════════════════

class TestCrearEncuesta:
    """Pruebas para el endpoint POST /encuestas/."""

    def test_crear_encuesta_valida_retorna_201(self):
        """Payload válido debe retornar 201 Created con el objeto completo."""
        response = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        assert response.status_code == 201
        data = response.json()
        assert "id_encuesta" in data
        assert "fecha_registro" in data
        assert data["encuestado"]["nombre"] == "Laura Daniela Jiménez"

    def test_crear_encuesta_genera_id_automatico(self):
        """El servidor debe asignar un UUID aunque el cliente no lo provea."""
        response = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        data = response.json()
        assert data["id_encuesta"] is not None
        assert len(data["id_encuesta"]) == 36  # UUID estándar

    def test_crear_encuesta_edad_invalida_retorna_422(self):
        """Edad 200 debe ser rechazada con HTTP 422."""
        payload = {
            **ENCUESTA_VALIDA,
            "encuestado": {**ENCUESTA_VALIDA["encuestado"], "edad": 200},
        }
        response = client.post("/encuestas/", json=payload)
        assert response.status_code == 422

    def test_crear_encuesta_error_422_estructura_personalizada(self):
        """El handler personalizado debe retornar JSON con 'detalle_errores'."""
        payload = {
            **ENCUESTA_VALIDA,
            "encuestado": {**ENCUESTA_VALIDA["encuestado"], "estrato": 9},
        }
        response = client.post("/encuestas/", json=payload)
        assert response.status_code == 422
        data = response.json()
        # Verificar estructura del handler personalizado (RF4)
        assert "detalle_errores" in data
        assert "descripcion" in data
        assert "sugerencia" in data
        assert data["codigo_http"] == 422

    def test_crear_encuesta_departamento_invalido_rechazado(self):
        """Departamento inexistente debe retornar 422."""
        payload = {
            **ENCUESTA_VALIDA,
            "encuestado": {**ENCUESTA_VALIDA["encuestado"], "departamento": "Nárnia"},
        }
        response = client.post("/encuestas/", json=payload)
        assert response.status_code == 422

    def test_crear_encuesta_likert_fuera_de_rango_rechazado(self):
        """Valor Likert=7 debe generar HTTP 422."""
        payload = {
            **ENCUESTA_VALIDA,
            "respuestas": [
                {
                    "pregunta_id": 1,
                    "enunciado": "Satisfacción",
                    "tipo_pregunta": "likert",
                    "valor": 7,  # Fuera de escala
                }
            ],
        }
        response = client.post("/encuestas/", json=payload)
        assert response.status_code == 422

    def test_crear_encuesta_se_almacena_en_repositorio(self):
        """Después del POST, la encuesta debe estar accesible vía GET."""
        post_response = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        id_enc = post_response.json()["id_encuesta"]
        get_response = client.get(f"/encuestas/{id_enc}")
        assert get_response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: GET /encuestas/
# ══════════════════════════════════════════════════════════════════════════════

class TestListarEncuestas:
    """Pruebas para el endpoint GET /encuestas/."""

    def test_listar_repositorio_vacio_retorna_lista_vacia(self):
        """Con el repositorio vacío, debe retornar [] con status 200."""
        response = client.get("/encuestas/")
        assert response.status_code == 200
        assert response.json() == []

    def test_listar_retorna_encuesta_creada(self):
        """Después de crear una encuesta, debe aparecer en la lista."""
        client.post("/encuestas/", json=ENCUESTA_VALIDA)
        response = client.get("/encuestas/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_paginacion_skip_limit(self):
        """La paginación debe funcionar correctamente."""
        for _ in range(5):
            client.post("/encuestas/", json=ENCUESTA_VALIDA)
        response = client.get("/encuestas/?skip=2&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: GET /encuestas/{id}
# ══════════════════════════════════════════════════════════════════════════════

class TestObtenerEncuesta:
    """Pruebas para el endpoint GET /encuestas/{id}."""

    def test_obtener_encuesta_existente_retorna_200(self):
        """GET por ID de encuesta existente debe retornar 200 OK."""
        post_r = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        id_enc = post_r.json()["id_encuesta"]
        get_r = client.get(f"/encuestas/{id_enc}")
        assert get_r.status_code == 200
        assert get_r.json()["id_encuesta"] == id_enc

    def test_obtener_encuesta_inexistente_retorna_404(self):
        """GET con ID inexistente debe retornar 404 Not Found."""
        response = client.get("/encuestas/id-que-no-existe-en-ningun-lugar")
        assert response.status_code == 404

    def test_obtener_encuesta_datos_correctos(self):
        """Los datos retornados deben coincidir con los ingresados."""
        post_r = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        id_enc = post_r.json()["id_encuesta"]
        get_r = client.get(f"/encuestas/{id_enc}")
        data = get_r.json()
        assert data["encuestado"]["nombre"] == "Laura Daniela Jiménez"
        assert data["encuestado"]["edad"] == 32
        assert len(data["respuestas"]) == 2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: PUT /encuestas/{id}
# ══════════════════════════════════════════════════════════════════════════════

class TestActualizarEncuesta:
    """Pruebas para el endpoint PUT /encuestas/{id}."""

    def test_actualizar_encuesta_existente_retorna_200(self):
        """PUT con datos válidos debe retornar 200 OK con datos actualizados."""
        post_r = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        id_enc = post_r.json()["id_encuesta"]

        payload_actualizado = {
            **ENCUESTA_VALIDA,
            "encuestado": {**ENCUESTA_VALIDA["encuestado"], "edad": 40},
        }
        put_r = client.put(f"/encuestas/{id_enc}", json=payload_actualizado)
        assert put_r.status_code == 200
        assert put_r.json()["encuestado"]["edad"] == 40

    def test_actualizar_preserva_id_original(self):
        """El PUT no debe cambiar el ID — el servidor lo preserva."""
        post_r = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        id_original = post_r.json()["id_encuesta"]

        # Enviar con otro ID en el cuerpo — debe ignorarse
        payload = {**ENCUESTA_VALIDA, "id_encuesta": "id-diferente-intentado"}
        put_r = client.put(f"/encuestas/{id_original}", json=payload)
        assert put_r.json()["id_encuesta"] == id_original

    def test_actualizar_encuesta_inexistente_retorna_404(self):
        """PUT sobre ID inexistente debe retornar 404 Not Found."""
        response = client.put("/encuestas/id-fantasma", json=ENCUESTA_VALIDA)
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: DELETE /encuestas/{id}
# ══════════════════════════════════════════════════════════════════════════════

class TestEliminarEncuesta:
    """Pruebas para el endpoint DELETE /encuestas/{id}."""

    def test_eliminar_encuesta_existente_retorna_204(self):
        """DELETE sobre encuesta existente debe retornar 204 No Content."""
        post_r = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        id_enc = post_r.json()["id_encuesta"]
        del_r = client.delete(f"/encuestas/{id_enc}")
        assert del_r.status_code == 204

    def test_eliminar_remueve_del_repositorio(self):
        """Después del DELETE, el GET debe retornar 404."""
        post_r = client.post("/encuestas/", json=ENCUESTA_VALIDA)
        id_enc = post_r.json()["id_encuesta"]
        client.delete(f"/encuestas/{id_enc}")
        get_r = client.get(f"/encuestas/{id_enc}")
        assert get_r.status_code == 404

    def test_eliminar_encuesta_inexistente_retorna_404(self):
        """DELETE sobre ID inexistente debe retornar 404."""
        response = client.delete("/encuestas/id-que-no-existe")
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: Ciclo CRUD completo
# ══════════════════════════════════════════════════════════════════════════════

def test_ciclo_crud_completo():
    """
    Test de integración: crea → lee → actualiza → verifica cambio → elimina → verifica eliminación.
    Representa el flujo completo de una encuesta en el sistema.
    """
    # 1. CREAR
    r_create = client.post("/encuestas/", json=ENCUESTA_VALIDA)
    assert r_create.status_code == 201
    id_enc = r_create.json()["id_encuesta"]

    # 2. LEER
    r_get = client.get(f"/encuestas/{id_enc}")
    assert r_get.status_code == 200
    assert r_get.json()["encuestado"]["edad"] == 32

    # 3. ACTUALIZAR
    payload_nuevo = {
        **ENCUESTA_VALIDA,
        "encuestado": {**ENCUESTA_VALIDA["encuestado"], "edad": 50, "ocupacion": "Gerente"},
    }
    r_put = client.put(f"/encuestas/{id_enc}", json=payload_nuevo)
    assert r_put.status_code == 200
    assert r_put.json()["encuestado"]["edad"] == 50

    # 4. VERIFICAR ACTUALIZACIÓN
    r_get2 = client.get(f"/encuestas/{id_enc}")
    assert r_get2.json()["encuestado"]["ocupacion"] == "Gerente"

    # 5. ELIMINAR
    r_del = client.delete(f"/encuestas/{id_enc}")
    assert r_del.status_code == 204

    # 6. VERIFICAR ELIMINACIÓN
    r_get3 = client.get(f"/encuestas/{id_enc}")
    assert r_get3.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: GET /encuestas/estadisticas/
# ══════════════════════════════════════════════════════════════════════════════

class TestEstadisticas:
    """Pruebas para el endpoint de estadísticas."""

    def test_estadisticas_repositorio_vacio(self):
        """Con repositorio vacío debe retornar zeros sin error."""
        response = client.get("/encuestas/estadisticas/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_encuestas"] == 0
        assert data["edad_promedio"] == 0.0

    def test_estadisticas_con_una_encuesta(self):
        """Con una encuesta, edad_promedio debe coincidir con la edad del encuestado."""
        client.post("/encuestas/", json=ENCUESTA_VALIDA)
        response = client.get("/encuestas/estadisticas/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_encuestas"] == 1
        assert data["edad_promedio"] == 32.0
        assert data["edad_minima"] == 32
        assert data["edad_maxima"] == 32

    def test_estadisticas_distribucion_por_estrato(self):
        """La distribución por estrato debe reflejar los datos ingresados."""
        client.post("/encuestas/", json=ENCUESTA_VALIDA)  # estrato 3
        response = client.get("/encuestas/estadisticas/")
        data = response.json()
        assert "Estrato 3" in data["distribucion_por_estrato"]
        assert data["distribucion_por_estrato"]["Estrato 3"] == 1

    def test_estadisticas_campos_completos(self):
        """La respuesta debe incluir todos los campos del schema EstadisticasEncuesta."""
        client.post("/encuestas/", json=ENCUESTA_VALIDA)
        response = client.get("/encuestas/estadisticas/")
        data = response.json()
        campos_requeridos = [
            "total_encuestas", "edad_promedio", "edad_minima", "edad_maxima",
            "distribucion_por_estrato", "distribucion_por_departamento",
            "distribucion_por_genero", "distribucion_por_nivel_educativo",
            "promedio_respuestas_por_encuesta",
        ]
        for campo in campos_requeridos:
            assert campo in data, f"Campo '{campo}' faltante en la respuesta"
