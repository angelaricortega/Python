"""
tests/test_models.py — Pruebas unitarias para los modelos Pydantic.

Cubre:
    - Encuestado: validaciones de edad, estrato, departamento, nombre
    - RespuestaEncuesta: coherencia tipo-valor (Likert, porcentaje, si_no, texto)
    - EncuestaCompleta: generación de ID, timestamps, detección de duplicados

Ejecución:
    pytest tests/test_models.py -v
"""

import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path de importación
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pydantic import ValidationError

from models import Encuestado, EncuestaCompleta, RespuestaEncuesta


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures reutilizables
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def encuestado_base():
    """Encuestado válido para reutilizar en múltiples tests."""
    return {
        "nombre": "Ana María Torres",
        "edad": 29,
        "genero": "femenino",
        "estrato": 3,
        "departamento": "Antioquia",
        "municipio": "Medellín",
        "nivel_educativo": "universitario",
    }


@pytest.fixture
def respuesta_likert():
    """RespuestaEncuesta Likert válida."""
    return {
        "pregunta_id": 1,
        "enunciado": "¿Qué tan satisfecho está con el servicio de salud?",
        "tipo_pregunta": "likert",
        "valor": 4,
    }


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: Encuestado
# ══════════════════════════════════════════════════════════════════════════════

class TestEncuestado:
    """Pruebas unitarias para el modelo Encuestado."""

    def test_encuestado_valido_completo(self, encuestado_base):
        """Un encuestado con todos los campos correctos debe crearse sin errores."""
        enc = Encuestado(**encuestado_base)
        assert enc.nombre == "Ana María Torres"
        assert enc.edad == 29
        assert enc.estrato == 3
        assert enc.departamento == "Antioquia"

    def test_nombre_normaliza_espacios_extra(self, encuestado_base):
        """El validator mode='before' debe colapsar espacios múltiples en el nombre."""
        encuestado_base["nombre"] = "  Carlos   López  "
        enc = Encuestado(**encuestado_base)
        assert enc.nombre == "Carlos López"

    def test_departamento_case_insensitive(self, encuestado_base):
        """El validator debe aceptar variaciones de capitalización."""
        encuestado_base["departamento"] = "ANTIOQUIA"
        enc = Encuestado(**encuestado_base)
        assert enc.departamento == "Antioquia"  # Nombre oficial del catálogo DANE

    def test_departamento_sin_tilde_aceptado(self, encuestado_base):
        """'Cordoba' (sin tilde) debe resolverse a 'Córdoba' (oficial DANE)."""
        encuestado_base["departamento"] = "Cordoba"
        enc = Encuestado(**encuestado_base)
        assert enc.departamento == "Córdoba"

    def test_departamento_invalido_lanza_error(self, encuestado_base):
        """Un departamento inexistente debe lanzar ValidationError con mensaje claro."""
        encuestado_base["departamento"] = "Gondor"
        with pytest.raises(ValidationError) as exc_info:
            Encuestado(**encuestado_base)
        assert "Gondor" in str(exc_info.value)

    def test_edad_limite_inferior_valido(self, encuestado_base):
        """Edad 0 debe ser válida (recién nacidos pueden participar como sujetos)."""
        encuestado_base["edad"] = 0
        enc = Encuestado(**encuestado_base)
        assert enc.edad == 0

    def test_edad_limite_superior_valido(self, encuestado_base):
        """Edad 120 debe ser válida (límite biológico aceptado)."""
        encuestado_base["edad"] = 120
        enc = Encuestado(**encuestado_base)
        assert enc.edad == 120

    def test_edad_negativa_rechazada(self, encuestado_base):
        """Edad negativa viola restricción biológica — debe rechazarse."""
        encuestado_base["edad"] = -1
        with pytest.raises(ValidationError):
            Encuestado(**encuestado_base)

    def test_edad_mayor_120_rechazada(self, encuestado_base):
        """Edad > 120 es estadísticamente imposible — debe rechazarse."""
        encuestado_base["edad"] = 999
        with pytest.raises(ValidationError) as exc_info:
            Encuestado(**encuestado_base)
        assert "999" in str(exc_info.value) or "120" in str(exc_info.value)

    def test_estrato_minimo_valido(self, encuestado_base):
        """Estrato 1 (bajo-bajo) debe ser válido."""
        encuestado_base["estrato"] = 1
        enc = Encuestado(**encuestado_base)
        assert enc.estrato == 1

    def test_estrato_maximo_valido(self, encuestado_base):
        """Estrato 6 (alto) debe ser válido."""
        encuestado_base["estrato"] = 6
        enc = Encuestado(**encuestado_base)
        assert enc.estrato == 6

    def test_estrato_fuera_de_rango_rechazado(self, encuestado_base):
        """Estrato 7 no existe en Colombia — debe rechazarse."""
        encuestado_base["estrato"] = 7
        with pytest.raises(ValidationError):
            Encuestado(**encuestado_base)

    def test_estrato_cero_rechazado(self, encuestado_base):
        """Estrato 0 no existe en Colombia — debe rechazarse."""
        encuestado_base["estrato"] = 0
        with pytest.raises(ValidationError):
            Encuestado(**encuestado_base)

    def test_genero_opciones_validas(self, encuestado_base):
        """Todos los géneros del Literal deben aceptarse."""
        for genero in ["masculino", "femenino", "no_binario", "prefiero_no_decir"]:
            encuestado_base["genero"] = genero
            enc = Encuestado(**encuestado_base)
            assert enc.genero == genero

    def test_bogota_dc_aceptada(self, encuestado_base):
        """'Bogotá D.C.' debe reconocerse como entidad territorial válida."""
        encuestado_base["departamento"] = "Bogotá D.C."
        enc = Encuestado(**encuestado_base)
        assert enc.departamento == "Bogotá D.C."


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: RespuestaEncuesta
# ══════════════════════════════════════════════════════════════════════════════

class TestRespuestaEncuesta:
    """Pruebas unitarias para el modelo RespuestaEncuesta."""

    def test_likert_valido(self, respuesta_likert):
        """Valor Likert en rango [1,5] debe aceptarse."""
        r = RespuestaEncuesta(**respuesta_likert)
        assert r.valor == 4

    def test_likert_todos_los_valores_validos(self, respuesta_likert):
        """Todos los valores de la escala Likert (1-5) deben aceptarse."""
        for v in [1, 2, 3, 4, 5]:
            respuesta_likert["valor"] = v
            r = RespuestaEncuesta(**respuesta_likert)
            assert r.valor == v

    def test_likert_fuera_de_rango_rechazado(self, respuesta_likert):
        """Valor 6 en escala Likert debe rechazarse."""
        respuesta_likert["valor"] = 6
        with pytest.raises(ValidationError):
            RespuestaEncuesta(**respuesta_likert)

    def test_likert_cero_rechazado(self, respuesta_likert):
        """Valor 0 en escala Likert debe rechazarse (escala empieza en 1)."""
        respuesta_likert["valor"] = 0
        with pytest.raises(ValidationError):
            RespuestaEncuesta(**respuesta_likert)

    def test_likert_string_numerico_convertido(self, respuesta_likert):
        """El validator mode='before' debe convertir '4' → 4 automáticamente."""
        respuesta_likert["valor"] = "4"
        r = RespuestaEncuesta(**respuesta_likert)
        assert isinstance(r.valor, int)
        assert r.valor == 4

    def test_porcentaje_valido(self):
        """Porcentaje en rango [0, 100] debe aceptarse."""
        r = RespuestaEncuesta(
            pregunta_id=2,
            enunciado="Nivel de confianza en instituciones (%)",
            tipo_pregunta="porcentaje",
            valor=75.5,
        )
        assert r.valor == 75.5

    def test_porcentaje_limites_extremos(self):
        """0.0 y 100.0 son valores límite válidos para porcentaje."""
        for v in [0.0, 100.0]:
            r = RespuestaEncuesta(
                pregunta_id=1, enunciado="P", tipo_pregunta="porcentaje", valor=v
            )
            assert r.valor == v

    def test_porcentaje_negativo_rechazado(self):
        """Porcentaje negativo es estadísticamente imposible — debe rechazarse."""
        with pytest.raises(ValidationError):
            RespuestaEncuesta(
                pregunta_id=1, enunciado="P", tipo_pregunta="porcentaje", valor=-5.0
            )

    def test_porcentaje_mayor_100_rechazado(self):
        """Porcentaje > 100 es estadísticamente imposible — debe rechazarse."""
        with pytest.raises(ValidationError):
            RespuestaEncuesta(
                pregunta_id=1, enunciado="P", tipo_pregunta="porcentaje", valor=110.0
            )

    def test_porcentaje_con_coma_decimal_aceptado(self):
        """El validator mode='before' debe normalizar '75,5' → 75.5."""
        r = RespuestaEncuesta(
            pregunta_id=1, enunciado="P", tipo_pregunta="porcentaje", valor="75,5"
        )
        assert r.valor == 75.5

    def test_si_no_valido(self):
        """'si' y 'no' deben ser aceptados para tipo si_no."""
        for v in ["si", "no"]:
            r = RespuestaEncuesta(
                pregunta_id=1, enunciado="P", tipo_pregunta="si_no", valor=v
            )
            assert r.valor == v

    def test_si_con_tilde_normalizado(self):
        """'sí' (con tilde) debe normalizarse a 'si'."""
        r = RespuestaEncuesta(
            pregunta_id=1, enunciado="P", tipo_pregunta="si_no", valor="sí"
        )
        assert r.valor == "si"

    def test_si_no_valor_invalido(self):
        """'tal vez' no es una respuesta dicotómica válida — debe rechazarse."""
        with pytest.raises(ValidationError):
            RespuestaEncuesta(
                pregunta_id=1, enunciado="P", tipo_pregunta="si_no", valor="tal vez"
            )

    def test_texto_abierto_valido(self):
        """Texto no vacío debe aceptarse para tipo texto_abierto."""
        r = RespuestaEncuesta(
            pregunta_id=1,
            enunciado="Describa su experiencia",
            tipo_pregunta="texto_abierto",
            valor="Excelente atención y puntualidad",
        )
        assert r.valor == "Excelente atención y puntualidad"

    def test_texto_abierto_vacio_rechazado(self):
        """Cadena vacía no aporta información estadística — debe rechazarse."""
        with pytest.raises(ValidationError):
            RespuestaEncuesta(
                pregunta_id=1,
                enunciado="Comentarios",
                tipo_pregunta="texto_abierto",
                valor="   ",  # Solo espacios
            )


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: EncuestaCompleta
# ══════════════════════════════════════════════════════════════════════════════

class TestEncuestaCompleta:
    """Pruebas unitarias para el modelo contenedor EncuestaCompleta."""

    def _encuesta_payload(self, respuestas=None):
        """Construye un payload válido de encuesta completa."""
        if respuestas is None:
            respuestas = [
                {
                    "pregunta_id": 1,
                    "enunciado": "¿Satisfecho con el servicio de salud?",
                    "tipo_pregunta": "likert",
                    "valor": 3,
                }
            ]
        return {
            "encuestado": {
                "nombre": "Luis Fernando Gómez",
                "edad": 45,
                "genero": "masculino",
                "estrato": 4,
                "departamento": "Valle del Cauca",
                "municipio": "Cali",
                "nivel_educativo": "posgrado",
            },
            "respuestas": respuestas,
        }

    def test_encuesta_valida_genera_id_uuid(self):
        """El servidor debe asignar automáticamente un UUID al crear la encuesta."""
        enc = EncuestaCompleta(**self._encuesta_payload())
        assert enc.id_encuesta is not None
        assert len(enc.id_encuesta) == 36  # Formato UUID: 8-4-4-4-12

    def test_encuesta_valida_genera_timestamp(self):
        """El servidor debe asignar automáticamente la fecha de registro."""
        enc = EncuestaCompleta(**self._encuesta_payload())
        assert enc.fecha_registro is not None
        assert isinstance(enc.fecha_registro, type(enc.fecha_registro))

    def test_encuesta_sin_respuestas_rechazada(self):
        """Una encuesta sin respuestas viola el invariante mínimo — rechazada."""
        with pytest.raises(ValidationError):
            EncuestaCompleta(**self._encuesta_payload(respuestas=[]))

    def test_encuesta_detecta_preguntas_duplicadas(self):
        """Dos respuestas con el mismo pregunta_id deben rechazarse."""
        respuestas_duplicadas = [
            {"pregunta_id": 1, "enunciado": "P1", "tipo_pregunta": "likert", "valor": 3},
            {"pregunta_id": 1, "enunciado": "P1 duplicada", "tipo_pregunta": "likert", "valor": 4},
        ]
        with pytest.raises(ValidationError) as exc_info:
            EncuestaCompleta(**self._encuesta_payload(respuestas=respuestas_duplicadas))
        assert "duplicados" in str(exc_info.value).lower()

    def test_encuesta_multiples_respuestas_tipos_mixtos(self):
        """Una encuesta con respuestas de diferentes tipos debe ser válida."""
        respuestas_mixtas = [
            {"pregunta_id": 1, "enunciado": "Satisfacción", "tipo_pregunta": "likert", "valor": 5},
            {"pregunta_id": 2, "enunciado": "Confianza %", "tipo_pregunta": "porcentaje", "valor": 80.0},
            {"pregunta_id": 3, "enunciado": "¿Recomendaría?", "tipo_pregunta": "si_no", "valor": "si"},
            {"pregunta_id": 4, "enunciado": "Comentarios", "tipo_pregunta": "texto_abierto", "valor": "Muy bueno"},
        ]
        enc = EncuestaCompleta(**self._encuesta_payload(respuestas=respuestas_mixtas))
        assert len(enc.respuestas) == 4

    def test_encuesta_preserva_id_si_se_provee(self):
        """Si se provee un ID, el modelo lo preserva (útil para updates)."""
        payload = self._encuesta_payload()
        payload["id_encuesta"] = "mi-id-personalizado-123"
        enc = EncuestaCompleta(**payload)
        assert enc.id_encuesta == "mi-id-personalizado-123"
