"""
test_api.py — Tests unitarios para la API de Encuestas Poblacionales.

Bonificación +0.1: Implementación de 5+ tests con pytest que validan
modelos y endpoints.

Ejecución:
    pytest tests/test_api.py -v

Requisitos:
    pip install pytest httpx
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app, db_encuestas
from models import EncuestaCompleta, Encuestado, RespuestaEncuesta, EstadisticasEncuesta


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures de pytest
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """
    Fixture que proporciona un cliente de prueba para la API.
    
    TestClient de FastAPI simula requests HTTP sin necesidad de
    levantar un servidor real. Ideal para tests unitarios rápidos.
    """
    db_encuestas.clear()  # Limpiar antes de cada test
    with TestClient(app) as c:
        yield c
    db_encuestas.clear()  # Limpiar después de cada test


@pytest.fixture
def encuesta_valida():
    """Fixture con datos de encuesta válidos para reutilizar en tests."""
    return {
        "encuestado": {
            "nombre": "Juan Pérez",
            "edad": 35,
            "genero": "masculino",
            "estrato": 3,
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "nivel_educativo": "universitario",
            "ocupacion": "Ingeniero",
        },
        "respuestas": [
            {
                "pregunta_id": 1,
                "enunciado": "¿Satisfacción con el servicio de salud?",
                "tipo_pregunta": "likert",
                "valor": 4,
            },
            {
                "pregunta_id": 2,
                "enunciado": "¿Nivel de confianza en instituciones (%)?",
                "tipo_pregunta": "porcentaje",
                "valor": 75.5,
            },
            {
                "pregunta_id": 3,
                "enunciado": "¿Ha usado servicios digitales del Estado?",
                "tipo_pregunta": "si_no",
                "valor": "si",
            },
        ],
        "observaciones_generales": "Test unitario",
    }


# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE MODELOS PYDANTIC (RF1, RF2)
# ══════════════════════════════════════════════════════════════════════════════

class TestModelosPydantic:
    """Tests para validación de modelos Pydantic."""

    def test_encuestado_valido(self):
        """Test 1: Crear Encuestado con datos válidos."""
        encuestado = Encuestado(
            nombre="María García",
            edad=28,
            genero="femenino",
            estrato=2,
            departamento="Cundinamarca",
            municipio="Bogotá",
            nivel_educativo="universitario",
            ocupacion="Docente",
        )
        assert encuestado.nombre == "María García"
        assert encuestado.edad == 28
        assert encuestado.estrato == 2
        assert encuestado.departamento == "Cundinamarca"

    def test_encuestado_edad_invalida(self):
        """Test 2: Validador de edad debe rechazar valores fuera de [0-120]."""
        with pytest.raises(ValidationError) as exc_info:
            Encuestado(
                nombre="Carlos",
                edad=150,  # Edad inválida
                genero="masculino",
                estrato=3,
                departamento="Antioquia",
                municipio="Medellín",
                nivel_educativo="tecnico",
            )
        assert "edad" in str(exc_info.value).lower()

    def test_encuestado_estrato_invalido(self):
        """Test 3: Validador de estrato debe rechazar valores fuera de [1-6]."""
        with pytest.raises(ValidationError) as exc_info:
            Encuestado(
                nombre="Ana",
                edad=40,
                genero="femenino",
                estrato=7,  # Estrato inválido
                departamento="Valle del Cauca",
                municipio="Cali",
                nivel_educativo="secundaria",
            )
        assert "estrato" in str(exc_info.value).lower()

    def test_encuestado_departamento_invalido(self):
        """Test 4: Validador de departamento debe rechazar departamentos no DANE."""
        with pytest.raises(ValidationError) as exc_info:
            Encuestado(
                nombre="Luis",
                edad=25,
                genero="masculino",
                estrato=1,
                departamento="Atlántida",  # No existe en Colombia
                municipio="Barranquilla",
                nivel_educativo="primaria",
            )
        assert "departamento" in str(exc_info.value).lower()

    def test_respuesta_likert_valida(self):
        """Test 5: Respuesta Likert debe aceptar valores [1-5]."""
        respuesta = RespuestaEncuesta(
            pregunta_id=1,
            enunciado="¿Satisfacción con el servicio?",
            tipo_pregunta="likert",
            valor=4,
        )
        assert respuesta.valor == 4
        assert respuesta.tipo_pregunta == "likert"

    def test_respuesta_likert_invalida(self):
        """Test 6: Respuesta Likert debe rechazar valores fuera de [1-5]."""
        with pytest.raises(ValidationError) as exc_info:
            RespuestaEncuesta(
                pregunta_id=1,
                enunciado="¿Satisfacción?",
                tipo_pregunta="likert",
                valor=6,  # Inválido
            )
        assert "likert" in str(exc_info.value).lower()

    def test_respuesta_porcentaje_valida(self):
        """Test 7: Respuesta porcentaje debe aceptar valores [0-100]."""
        respuesta = RespuestaEncuesta(
            pregunta_id=2,
            enunciado="¿Confianza en instituciones (%)?",
            tipo_pregunta="porcentaje",
            valor=85.5,
        )
        assert respuesta.valor == 85.5

    def test_respuesta_porcentaje_invalida(self):
        """Test 8: Respuesta porcentaje debe rechazar valores < 0 o > 100."""
        with pytest.raises(ValidationError) as exc_info:
            RespuestaEncuesta(
                pregunta_id=2,
                enunciado="¿Confianza (%)?",
                tipo_pregunta="porcentaje",
                valor=150,  # Inválido
            )
        assert "porcentaje" in str(exc_info.value).lower()

    def test_encuesta_completa_anidacion(self):
        """Test 9: EncuestaCompleta debe anidar correctamente Encuestado + Respuestas."""
        encuesta = EncuestaCompleta(
            encuestado=Encuestado(
                nombre="Pedro Sánchez",
                edad=45,
                genero="masculino",
                estrato=4,
                departamento="Bogotá D.C.",
                municipio="Bogotá",
                nivel_educativo="posgrado",
            ),
            respuestas=[
                RespuestaEncuesta(
                    pregunta_id=1,
                    enunciado="¿Recomendaría el servicio?",
                    tipo_pregunta="likert",
                    valor=5,
                )
            ],
        )
        assert encuesta.encuestado.nombre == "Pedro Sánchez"
        assert len(encuesta.respuestas) == 1
        assert encuesta.respuestas[0].valor == 5
        assert encuesta.id_encuesta is not None  # UUID generado automáticamente


# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE ENDPOINTS (RF3)
# ══════════════════════════════════════════════════════════════════════════════

class TestEndpoints:
    """Tests para endpoints de la API REST."""

    def test_health_check(self, client):
        """Test 10: Health check debe retornar estado activo."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "activo"
        assert "documentacion" in data

    def test_crear_encuesta(self, client, encuesta_valida):
        """Test 11: POST /encuestas/ debe crear encuesta y retornar 201."""
        response = client.post("/encuestas/", json=encuesta_valida)
        assert response.status_code == 201
        data = response.json()
        assert data["id_encuesta"] is not None
        assert data["encuestado"]["nombre"] == "Juan Pérez"
        assert len(data["respuestas"]) == 3

    def test_listar_encuestas(self, client, encuesta_valida):
        """Test 12: GET /encuestas/ debe listar encuestas creadas."""
        # Crear una encuesta primero
        client.post("/encuestas/", json=encuesta_valida)
        
        response = client.get("/encuestas/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_obtener_encuesta_por_id(self, client, encuesta_valida):
        """Test 13: GET /encuestas/{id} debe retornar encuesta específica."""
        # Crear encuesta
        response_creacion = client.post("/encuestas/", json=encuesta_valida)
        id_encuesta = response_creacion.json()["id_encuesta"]
        
        # Consultar por ID
        response = client.get(f"/encuestas/{id_encuesta}")
        assert response.status_code == 200
        data = response.json()
        assert data["id_encuesta"] == id_encuesta
        assert data["encuestado"]["nombre"] == "Juan Pérez"

    def test_obtener_encuesta_id_no_existe(self, client):
        """Test 14: GET /encuestas/{id} debe retornar 404 si no existe."""
        response = client.get("/encuestas/id-que-no-existe")
        assert response.status_code == 404

    def test_actualizar_encuesta(self, client, encuesta_valida):
        """Test 15: PUT /encuestas/{id} debe actualizar encuesta."""
        # Crear encuesta
        response_creacion = client.post("/encuestas/", json=encuesta_valida)
        id_encuesta = response_creacion.json()["id_encuesta"]
        
        # Actualizar con nuevo nombre
        encuesta_valida["encuestado"]["nombre"] = "Juan Pérez Actualizado"
        response = client.put(f"/encuestas/{id_encuesta}", json=encuesta_valida)
        
        assert response.status_code == 200
        data = response.json()
        assert data["encuestado"]["nombre"] == "Juan Pérez Actualizado"

    def test_eliminar_encuesta(self, client, encuesta_valida):
        """Test 16: DELETE /encuestas/{id} debe eliminar y retornar 204."""
        # Crear encuesta
        response_creacion = client.post("/encuestas/", json=encuesta_valida)
        id_encuesta = response_creacion.json()["id_encuesta"]
        
        # Eliminar
        response = client.delete(f"/encuestas/{id_encuesta}")
        assert response.status_code == 204
        
        # Verificar que ya no existe
        response_get = client.get(f"/encuestas/{id_encuesta}")
        assert response_get.status_code == 404

    def test_estadisticas(self, client, encuesta_valida):
        """Test 17: GET /encuestas/estadisticas/ debe retornar estadísticas."""
        # Crear algunas encuestas
        client.post("/encuestas/", json=encuesta_valida)
        
        response = client.get("/encuestas/estadisticas/")
        assert response.status_code == 200
        data = response.json()
        assert "total_encuestas" in data
        assert "edad_promedio" in data
        assert "distribucion_por_estrato" in data
        assert "distribucion_por_genero" in data


# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE VALIDACIÓN DE ERRORES (RF4)
# ══════════════════════════════════════════════════════════════════════════════

class TestManejoErrores:
    """Tests para manejo de errores HTTP 422."""

    def test_error_validacion_edad(self, client, encuesta_valida):
        """Test 18: POST con edad inválida debe retornar 422."""
        encuesta_valida["encuestado"]["edad"] = 200  # Inválido
        
        response = client.post("/encuestas/", json=encuesta_valida)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "detalle_errores" in data

    def test_error_validacion_estrato(self, client, encuesta_valida):
        """Test 19: POST con estrato inválido debe retornar 422."""
        encuesta_valida["encuestado"]["estrato"] = 10  # Inválido
        
        response = client.post("/encuestas/", json=encuesta_valida)
        assert response.status_code == 422

    def test_error_validacion_respuestas_vacias(self, client, encuesta_valida):
        """Test 20: POST sin respuestas ahora es VÁLIDO (respuestas opcionales)."""
        encuesta_valida["respuestas"] = []  # Ahora es válido (min_length=0)

        response = client.post("/encuestas/", json=encuesta_valida)
        # Ahora debería ser 201, no 422, porque las respuestas son opcionales
        assert response.status_code == 201


# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE EXPORTACIÓN (Bonificación +0.1)
# ══════════════════════════════════════════════════════════════════════════════

class TestExportacion:
    """Tests para endpoints de exportación JSON/Pickle."""

    def test_export_json(self, client, encuesta_valida):
        """Test 21: GET /encuestas/export/json/ debe retornar JSON descargable."""
        # Crear datos
        client.post("/encuestas/", json=encuesta_valida)
        
        response = client.get("/encuestas/export/json/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "encuestas.json" in response.headers["content-disposition"]

    def test_export_pickle(self, client, encuesta_valida):
        """Test 22: GET /encuestas/export/pickle/ debe retornar Pickle descargable."""
        # Crear datos
        client.post("/encuestas/", json=encuesta_valida)
        
        response = client.get("/encuestas/export/pickle/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "encuestas.pkl" in response.headers["content-disposition"]


# ══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Permite ejecutar tests directamente con: python tests/test_api.py
    
    pytest descubre automáticamente funciones que empiezan con 'test_'
    y clases que empiezan con 'Test'.
    """
    pytest.main([__file__, "-v", "--tb=short"])
