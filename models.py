"""
models.py — Modelos Pydantic para el sistema de encuestas poblacionales.

Jerarquía de modelos (RF1 - Modelos anidados con tipos complejos):

    EncuestaCompleta          ← Modelo contenedor (nivel raíz)
    ├── Encuestado            ← Perfil demográfico del respondente
    └── List[RespuestaEncuesta]  ← Respuestas individuales (mínimo 1)

Tipos complejos utilizados:
    - List[RespuestaEncuesta]   → lista de objetos anidados
    - Union[int, float, str]    → valor polimórfico según tipo de pregunta
    - Optional[str]             → campos opcionales (observaciones)
    - Literal[...]              → enumeraciones cerradas (género, tipo de pregunta)
    - Annotated[int, Field()]   → constraints inline con metadatos
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Annotated

from validators import (
    DEPARTAMENTOS_COLOMBIA,
    validar_departamento,
    validar_edad,
    validar_estrato,
    validar_porcentaje,
    validar_rango_likert,
)


# ══════════════════════════════════════════════════════════════════════════════
# MODELO 1: RespuestaEncuesta
# Representa la respuesta del encuestado a una pregunta específica.
# El campo `valor` es polimórfico: int (Likert/si_no), float (porcentaje), str.
# ══════════════════════════════════════════════════════════════════════════════

class RespuestaEncuesta(BaseModel):
    """
    Respuesta a una pregunta individual de la encuesta.

    Soporta cuatro tipos de escala estadística:
    - likert:       Escala ordinal 1-5 (tipo int)
    - porcentaje:   Escala de razón 0.0-100.0 (tipo float)
    - texto_abierto: Respuesta cualitativa libre (tipo str)
    - si_no:        Variable dicotómica "si" o "no" (tipo str)
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pregunta_id": 1,
                "enunciado": "¿Qué tan satisfecho está con el servicio de salud en su municipio?",
                "tipo_pregunta": "likert",
                "valor": 4,
                "observacion": "La atención mejoró, pero aún hay problemas con medicamentos.",
            }
        }
    )

    pregunta_id: Annotated[
        int, Field(ge=1, description="Identificador único de la pregunta (entero positivo)")
    ]
    enunciado: str = Field(
        ..., min_length=5, max_length=500,
        description="Texto completo de la pregunta tal como fue formulada"
    )
    tipo_pregunta: Literal["likert", "porcentaje", "texto_abierto", "si_no"] = Field(
        ...,
        description=(
            "Tipo de escala de medición: "
            "likert (1-5 ordinal), porcentaje (0-100 razón), "
            "texto_abierto (cualitativa), si_no (dicotómica)"
        ),
    )
    # Union[int, float, str]: valor polimórfico según tipo de pregunta
    valor: Union[int, float, str] = Field(
        ...,
        description=(
            "Respuesta del encuestado: "
            "int para likert, float para porcentaje, str para texto_abierto/si_no"
        ),
    )
    observacion: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Comentario adicional del encuestado (opcional)",
    )

    @field_validator("valor", mode="before")
    @classmethod
    def limpiar_valor_entrada(cls, v: Union[int, float, str]) -> Union[int, float, str]:
        """
        mode='before': Se ejecuta ANTES de que Pydantic convierta tipos.

        Propósito estadístico: errores de digitación frecuentes en campo manual
        (ej. el operador ingresa "4 " con espacio, o "3,5" con coma decimal).
        Este validator limpia el valor ANTES de la validación cruzada posterior.

        Transformaciones aplicadas:
            "4 "  → 4    (strip + conversión a int)
            "3,5" → 3.5  (normalización decimal + conversión a float)
            "si"  → "si" (solo strip, preserva texto genuino)
        """
        if isinstance(v, str):
            v_clean = v.strip()
            # Intentar conversión a entero primero (más restrictivo)
            try:
                return int(v_clean)
            except ValueError:
                pass
            # Luego intentar float con normalización de coma decimal
            try:
                return float(v_clean.replace(",", "."))
            except ValueError:
                pass
            # Es texto genuino (texto_abierto o si_no)
            return v_clean
        return v

    @model_validator(mode="after")
    def validar_coherencia_tipo_valor(self) -> "RespuestaEncuesta":
        """
        mode='after': Validación cruzada DESPUÉS de construir el objeto.

        Verifica la coherencia entre tipo_pregunta y el tipo/rango del valor.
        Esta es la validación estadística central: garantiza que los datos
        sean coherentes con la escala de medición declarada.

        Restricciones por tipo:
            likert       → int en [1, 5]
            porcentaje   → float/int en [0.0-100.0]
            si_no        → str "si" o "no" (normaliza "sí")
            texto_abierto → str no vacío
        """
        tipo = self.tipo_pregunta
        v = self.valor

        if tipo == "likert":
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(
                    f"Tipo 'likert' requiere un entero. "
                    f"Recibido: {type(v).__name__} = {v!r}. "
                    f"Ejemplo válido: 4"
                )
            validar_rango_likert(v)

        elif tipo == "porcentaje":
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ValueError(
                    f"Tipo 'porcentaje' requiere un número. "
                    f"Recibido: {type(v).__name__} = {v!r}. "
                    f"Ejemplo válido: 75.5"
                )
            self.valor = validar_porcentaje(float(v))

        elif tipo == "si_no":
            if not isinstance(v, str):
                raise ValueError(
                    f"Tipo 'si_no' requiere texto 'si' o 'no'. "
                    f"Recibido: {type(v).__name__} = {v!r}"
                )
            v_norm = v.lower().strip().replace("sí", "si")
            if v_norm not in ("si", "no"):
                raise ValueError(
                    f"Tipo 'si_no' solo acepta 'si' o 'no'. "
                    f"Recibido: {v!r}"
                )
            self.valor = v_norm

        elif tipo == "texto_abierto":
            if not isinstance(v, str) or len(str(v).strip()) == 0:
                raise ValueError(
                    "Tipo 'texto_abierto' requiere una cadena de texto no vacía."
                )

        return self


# ══════════════════════════════════════════════════════════════════════════════
# MODELO 2: Encuestado
# Perfil demográfico del participante. Aplica restricciones estadísticas
# y geográficas específicas del contexto colombiano.
# ══════════════════════════════════════════════════════════════════════════════

class Encuestado(BaseModel):
    """
    Datos demográficos del participante de la encuesta poblacional.

    Restricciones estadísticas aplicadas:
    - edad:     axioma biológico [0, 120] años
    - estrato:  clasificación socioeconómica colombiana [1, 6]
    - departamento: catálogo DANE (32 departamentos + Bogotá D.C.)
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "María Camila García",
                "edad": 34,
                "genero": "femenino",
                "estrato": 3,
                "departamento": "Cundinamarca",
                "municipio": "Bogotá",
                "nivel_educativo": "universitario",
                "ocupacion": "Docente universitaria",
            }
        }
    )

    nombre: str = Field(
        ..., min_length=2, max_length=100,
        description="Nombre completo del encuestado"
    )
    edad: Annotated[
        int,
        Field(
            ge=0, le=120,
            description="Edad en años — restricción biológica (0-120). "
                        "Edades fuera de rango indican error de captura.",
        ),
    ]
    genero: Literal["masculino", "femenino", "no_binario", "prefiero_no_decir"] = Field(
        ..., description="Género del encuestado según categorías del formulario"
    )
    estrato: Annotated[
        int,
        Field(
            ge=1, le=6,
            description="Estrato socioeconómico colombiano: 1=bajo-bajo, 6=alto. "
                        "Clasificación oficial del DANE.",
        ),
    ]
    departamento: str = Field(
        ...,
        description="Departamento colombiano de residencia (catálogo DANE)",
    )
    municipio: str = Field(
        ..., min_length=2, max_length=100,
        description="Municipio de residencia actual"
    )
    nivel_educativo: Literal[
        "ninguno", "primaria", "secundaria", "tecnico", "universitario", "posgrado", "otro"
    ] = Field(..., description="Nivel de escolaridad más alto alcanzado")
    ocupacion: Optional[str] = Field(
        default=None, max_length=100,
        description="Ocupación o actividad económica principal (opcional)"
    )

    @field_validator("departamento", mode="before")
    @classmethod
    def normalizar_y_validar_departamento(cls, v: str) -> str:
        """
        mode='before': Se ejecuta antes de la asignación del campo.

        Normaliza variaciones de escritura frecuentes en encuestas manuales:
            'ANTIOQUIA' → 'Antioquia'
            'cundinamarca' → 'Cundinamarca'
            'Cordoba' → 'Córdoba'  (sin tilde → con tilde oficial)

        Valida contra catálogo DANE de 33 entidades territoriales.
        Garantiza integridad referencial para análisis estadístico regional.
        """
        if not isinstance(v, str):
            raise ValueError("El departamento debe ser texto.")
        return validar_departamento(v)

    @field_validator("nombre", mode="before")
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        """
        mode='before': Normaliza el nombre antes de almacenarlo.

        Limpieza aplicada:
            '  Carlos   López  ' → 'Carlos López'
        Previene duplicados por espacios extras en análisis de frecuencias.
        """
        if not isinstance(v, str):
            raise ValueError("El nombre debe ser texto.")
        return " ".join(v.strip().split())  # Colapsa espacios múltiples

    @field_validator("edad", mode="after")
    @classmethod
    def auditar_restriccion_biologica(cls, v: int) -> int:
        """
        mode='after': Verificación post-conversión del axioma estadístico.

        La restricción [0, 120] es un axioma biológico en estadística demográfica:
        ningún ser humano documentado ha superado 122 años.
        Valores fuera de rango (ej. 999) son invariablemente errores de digitación
        que contaminarían cualquier análisis de tendencia central.
        """
        return validar_edad(v)

    @field_validator("estrato", mode="after")
    @classmethod
    def auditar_clasificacion_socioeconomica(cls, v: int) -> int:
        """
        mode='after': Verificación post-conversión de la clasificación DANE.

        El estrato socioeconómico en Colombia es una política pública de
        subsidios cruzados. Valores fuera de [1,6] indicarían error de captura
        que afectaría análisis de segmentación socioeconómica.
        """
        return validar_estrato(v)


# ══════════════════════════════════════════════════════════════════════════════
# MODELO 3: EncuestaCompleta
# Modelo contenedor que anida Encuestado + List[RespuestaEncuesta].
# Es el payload principal del endpoint POST /encuestas/.
# ══════════════════════════════════════════════════════════════════════════════

class EncuestaCompleta(BaseModel):
    """
    Unidad atómica de la encuesta poblacional.

    Combina el perfil demográfico (Encuestado) con el conjunto de respuestas
    (List[RespuestaEncuesta]). El servidor asigna automáticamente el ID único
    y el timestamp de registro.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "encuestado": {
                    "nombre": "Carlos Andrés Rodríguez",
                    "edad": 28,
                    "genero": "masculino",
                    "estrato": 2,
                    "departamento": "Antioquia",
                    "municipio": "Medellín",
                    "nivel_educativo": "universitario",
                    "ocupacion": "Ingeniero de sistemas",
                },
                "respuestas": [
                    {
                        "pregunta_id": 1,
                        "enunciado": "¿Qué tan satisfecho está con el servicio de salud?",
                        "tipo_pregunta": "likert",
                        "valor": 3,
                        "observacion": None,
                    },
                    {
                        "pregunta_id": 2,
                        "enunciado": "¿Cuál es su nivel de confianza en las instituciones?",
                        "tipo_pregunta": "porcentaje",
                        "valor": 45.5,
                        "observacion": "Desconfianza por casos de corrupción recientes.",
                    },
                    {
                        "pregunta_id": 3,
                        "enunciado": "¿Ha utilizado servicios digitales del Estado en el último mes?",
                        "tipo_pregunta": "si_no",
                        "valor": "si",
                        "observacion": None,
                    },
                ],
                "observaciones_generales": "Encuesta aplicada en zona urbana, modalidad presencial.",
            }
        }
    )

    id_encuesta: Optional[str] = Field(
        default=None,
        description="UUID asignado automáticamente por el servidor al momento del registro",
    )
    fecha_registro: Optional[datetime] = Field(
        default=None,
        description="Timestamp ISO 8601 asignado automáticamente por el servidor",
    )
    # Modelo anidado: Encuestado
    encuestado: Encuestado = Field(
        ..., description="Perfil demográfico del respondente"
    )
    # Lista de modelos anidados: List[RespuestaEncuesta]
    respuestas: List[RespuestaEncuesta] = Field(
        default_factory=list,
        min_length=0,  # Ahora es opcional (puede ser 0)
        description="Lista de respuestas (opcional)",
    )
    observaciones_generales: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Notas sobre condiciones del levantamiento (modalidad, zona, etc.)",
    )

    @model_validator(mode="after")
    def asignar_metadatos_servidor(self) -> "EncuestaCompleta":
        """
        Genera automáticamente el ID único (UUID4) y el timestamp de registro
        si no fueron provistos. Esto asegura que el servidor controla estos
        campos — el cliente no puede falsificar ni predecir IDs.
        """
        if not self.id_encuesta:
            self.id_encuesta = str(uuid4())
        if not self.fecha_registro:
            self.fecha_registro = datetime.now()
        return self

    @model_validator(mode="after")
    def validar_preguntas_sin_duplicados(self) -> "EncuestaCompleta":
        """
        Verifica que no existan pregunta_id duplicados dentro de la misma encuesta.

        Invariante estadístico: cada pregunta debe aparecer exactamente una vez
        por encuestado. Duplicados indicarían error en el formulario o en el
        proceso de digitación y contaminarían el análisis de consistencia interna.
        """
        ids_preguntas = [r.pregunta_id for r in self.respuestas]
        if len(ids_preguntas) != len(set(ids_preguntas)):
            duplicados = [p for p in ids_preguntas if ids_preguntas.count(p) > 1]
            raise ValueError(
                f"Las respuestas contienen pregunta_id duplicados: {list(set(duplicados))}. "
                f"Cada pregunta debe responderse exactamente una vez por encuesta."
            )
        return self


# ══════════════════════════════════════════════════════════════════════════════
# MODELOS DE RESPUESTA (Response Schemas)
# Schemas especializados para respuestas de endpoints GET y estadísticas.
# ══════════════════════════════════════════════════════════════════════════════

class EstadisticasEncuesta(BaseModel):
    """
    Resumen estadístico agregado del repositorio de encuestas.
    Generado dinámicamente por el endpoint GET /encuestas/estadisticas/.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_encuestas": 42,
                "edad_promedio": 35.7,
                "edad_minima": 18,
                "edad_maxima": 72,
                "distribucion_por_estrato": {
                    "Estrato 1": 8, "Estrato 2": 12, "Estrato 3": 15,
                    "Estrato 4": 5, "Estrato 5": 2, "Estrato 6": 0,
                },
                "distribucion_por_departamento": {"Antioquia": 18, "Cundinamarca": 24},
                "distribucion_por_genero": {"masculino": 20, "femenino": 22},
                "distribucion_por_nivel_educativo": {"universitario": 30, "secundaria": 12},
                "promedio_respuestas_por_encuesta": 4.2,
            }
        }
    )

    total_encuestas: int = Field(description="Número total de encuestas registradas")
    edad_promedio: float = Field(description="Media aritmética de las edades de los encuestados")
    edad_minima: int = Field(description="Edad mínima en el repositorio")
    edad_maxima: int = Field(description="Edad máxima en el repositorio")
    distribucion_por_estrato: Dict[str, int] = Field(
        description="Frecuencia absoluta de encuestados por estrato socioeconómico"
    )
    distribucion_por_departamento: Dict[str, int] = Field(
        description="Frecuencia absoluta de encuestados por departamento"
    )
    distribucion_por_genero: Dict[str, int] = Field(
        description="Frecuencia absoluta de encuestados por género"
    )
    distribucion_por_nivel_educativo: Dict[str, int] = Field(
        description="Frecuencia absoluta de encuestados por nivel educativo"
    )
    promedio_respuestas_por_encuesta: float = Field(
        description="Promedio de preguntas respondidas por encuesta"
    )


class MensajeRespuesta(BaseModel):
    """Respuesta simple de confirmación para operaciones de escritura."""

    mensaje: str
    id_encuesta: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# MODELO: GoogleFormsPayload
# Payload plano enviado por Google Apps Script al webhook /encuestas/google-forms/
# Más simple que EncuestaCompleta: sin objetos anidados, facilita la
# construcción del JSON en Apps Script (JavaScript sin tipado).
# El endpoint receptor convierte este payload → EncuestaCompleta.
# ══════════════════════════════════════════════════════════════════════════════

class GoogleFormsPayload(BaseModel):
    """
    Payload recibido desde Google Apps Script (integración Google Forms).

    Estructura plana que simplifica la construcción del JSON en Apps Script.
    El servidor normaliza y convierte los valores antes de validar con Pydantic.

    Mapeo de tipos de respuesta desde Google Forms:
        Escala lineal (1-5)  → tipo_pregunta: "likert"
        Respuesta corta num. → tipo_pregunta: "porcentaje"
        Opción múltiple Si/No → tipo_pregunta: "si_no"
        Párrafo / texto       → tipo_pregunta: "texto_abierto"
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "María García",
                "edad": 34,
                "genero": "femenino",
                "estrato": 3,
                "departamento": "Antioquia",
                "municipio": "Medellín",
                "nivel_educativo": "universitario",
                "ocupacion": "Docente",
                "respuestas": [
                    {
                        "pregunta_id": 1,
                        "enunciado": "Satisfacción con el servicio de salud en su municipio",
                        "tipo_pregunta": "likert",
                        "valor": 4,
                    },
                    {
                        "pregunta_id": 2,
                        "enunciado": "Nivel de confianza en las instituciones colombianas (%)",
                        "tipo_pregunta": "porcentaje",
                        "valor": 65.0,
                    },
                    {
                        "pregunta_id": 3,
                        "enunciado": "¿Ha utilizado servicios digitales del Estado en el último mes?",
                        "tipo_pregunta": "si_no",
                        "valor": "si",
                    },
                ],
                "observaciones_generales": "Encuesta aplicada vía Google Forms.",
                "fuente": "google_forms",
            }
        }
    )

    # ── Datos demográficos (planos) ──
    nombre: str = Field(..., min_length=2, max_length=100)
    edad: Union[int, str] = Field(..., description="Edad — se acepta como número o texto")
    genero: str = Field(..., description="Género — se normaliza al guardar")
    estrato: Union[int, str] = Field(..., description="Estrato — se acepta '1 - Bajo-bajo' o '1'")
    departamento: str = Field(..., description="Departamento colombiano")
    municipio: str = Field(..., min_length=2, max_length=100)
    nivel_educativo: str = Field(..., description="Nivel educativo — se normaliza al guardar")
    ocupacion: Optional[str] = Field(default=None, max_length=100)

    # ── Respuestas (lista de dicts — misma estructura que RespuestaEncuesta) ──
    respuestas: List[dict] = Field(..., min_length=1)

    # ── Metadatos ──
    observaciones_generales: Optional[str] = Field(default=None, max_length=500)
    fuente: str = Field(default="google_forms", description="Origen del dato")

    @field_validator("edad", mode="before")
    @classmethod
    def parsear_edad(cls, v: Union[int, str]) -> int:
        """Convierte edad de string a int (Apps Script puede enviarla como texto)."""
        try:
            return int(str(v).strip())
        except (ValueError, TypeError):
            raise ValueError(f"Edad inválida: {v!r}. Debe ser un número entero.")

    @field_validator("estrato", mode="before")
    @classmethod
    def parsear_estrato(cls, v: Union[int, str]) -> int:
        """
        Extrae el número del estrato aunque venga como '3 - Medio-bajo'.
        Google Forms envía el texto completo de la opción seleccionada.
        """
        v_str = str(v).strip()
        import re
        match = re.match(r"^(\d)", v_str)
        if match:
            return int(match.group(1))
        try:
            return int(v_str)
        except ValueError:
            raise ValueError(f"Estrato inválido: {v!r}. Use un valor entre 1 y 6.")

    @field_validator("genero", mode="before")
    @classmethod
    def normalizar_genero(cls, v: str) -> str:
        """Normaliza variaciones de Google Forms: 'Masculino' → 'masculino', etc."""
        mapa = {
            "masculino":           "masculino",
            "femenino":            "femenino",
            "no binario":          "no_binario",
            "no_binario":          "no_binario",
            "prefiero no decir":   "prefiero_no_decir",
            "prefiero_no_decir":   "prefiero_no_decir",
        }
        key = v.lower().strip()
        if key in mapa:
            return mapa[key]
        raise ValueError(
            f"Género '{v}' no reconocido. "
            f"Valores válidos: masculino, femenino, no binario, prefiero no decir."
        )

    @field_validator("nivel_educativo", mode="before")
    @classmethod
    def normalizar_nivel(cls, v: str) -> str:
        """Normaliza nivel educativo ignorando tildes y capitalización."""
        mapa = {
            "ninguno":       "ninguno",
            "primaria":      "primaria",
            "secundaria":    "secundaria",
            "tecnico":       "tecnico",
            "técnico":       "tecnico",
            "universitario": "universitario",
            "posgrado":      "posgrado",
        }
        key = v.lower().strip()
        if key in mapa:
            return mapa[key]
        # Intentar sin tildes
        sin_tildes = key.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
        if sin_tildes in mapa:
            return mapa[sin_tildes]
        raise ValueError(
            f"Nivel educativo '{v}' no reconocido. "
            f"Valores válidos: ninguno, primaria, secundaria, tecnico, universitario, posgrado."
        )


# ══════════════════════════════════════════════════════════════════════════════
# MODELOS PARA EXPORTACIÓN (Bonificación +0.1 JSON vs Pickle)
# ══════════════════════════════════════════════════════════════════════════════

class ExportResultado(BaseModel):
    """Resultado de operación de exportación."""
    total_exportados: int
    formato: str
    mensaje: str
