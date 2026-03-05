"""
api_fastapi.py — API REST con FastAPI para Análisis de Riesgo Crediticio
==========================================================================
Semana 3: FastAPI, endpoints CRUD, documentación Swagger automática.

CONCEPTOS CLAVE DE FASTAPI:
  1. Decoradores de ruta: @app.get, @app.post, @app.delete
     - Mapean URLs a funciones Python
     - Análogo a la función de verosimilitud: asigna contexto de ejecución

  2. Validación automática con Pydantic:
     - Los tipos en la firma definen el schema de validación
     - FastAPI valida automáticamente request/response
     - Retorna HTTP 422 si los datos no cumplen el schema

  3. Documentación Swagger UI automática (/docs):
     - FastAPI genera OpenAPI schema automáticamente
     - Interfaz gráfica interactiva para probar endpoints
     - Cualquier miembro del equipo puede usar sin documentación extra

  4. Síncrono vs Asíncrono:
     - async def: para operaciones I/O (BD, APIs externas, archivos)
     - def: para cálculos CPU (NumPy, Pandas, ML)

  5. Inyección de dependencias (Depends):
     - Desacopla lógica de negocio de la lógica de ruta
     - Reutiliza código (config, session, validaciones)

ENDPOINTS IMPLEMENTADOS (CRUD completo):
  GET  /              → Mensaje de bienvenida (health check)
  GET  /historial     → Listar todos los análisis guardados
  GET  /historial/{id} → Obtener análisis específico (404 si no existe)
  POST /analizar      → Crear nuevo análisis (valida con Pydantic)
  DELETE /historial/{id} → Eliminar análisis (404 si no existe)

USO:
  uvicorn api_fastapi:app --reload --host 0.0.0.0 --port 8000

  Luego visitar:
    http://127.0.0.1:8000       → Mensaje de bienvenida
    http://127.0.0.1:8000/docs  → Swagger UI interactivo
"""

# ── Librería estándar ────────────────────────────────────────────────────
from datetime import datetime
from typing import Optional, List

# ── Terceros ─────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# ── Locales ──────────────────────────────────────────────────────────────
from config import (
    API_TITULO,
    API_VERSION,
    API_DESCRIPCION,
    API_CONTACTO,
    API_LICENSE,
    PALETA,
)
from modelos import MunicipioFinanciero, NivelRiesgo


# ══════════════════════════════════════════════════════════════════════════
# 1. MODELOS PYDANTIC PARA LA API
# ══════════════════════════════════════════════════════════════════════════

class AnalisisRequest(BaseModel):
    """
    Modelo de entrada para crear un nuevo análisis.

    VALIDACIÓN AUTOMÁTICA:
      - municipio: string, obligatorio, mín 2 caracteres
      - total_cartera: float opcional, ≥ 0
      - total_captaciones: float opcional, ≥ 0
      - cartera_a a cartera_e: floats opcionales, ≥ 0

    FastAPI valida automáticamente el request body contra este schema.
    Si los datos no cumplen, retorna HTTP 422 Unprocessable Entity.
    """

    municipio: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="Nombre del municipio a analizar",
        example="Bogotá D.C.",
    )

    cartera_a: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera categoría A (normal) en COP",
        example=1500000000.0,
    )
    cartera_b: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera categoría B (observación) en COP",
        example=200000000.0,
    )
    cartera_c: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera categoría C (subestándar) en COP",
        example=50000000.0,
    )
    cartera_d: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera categoría D (dudosa) en COP",
        example=25000000.0,
    )
    cartera_e: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera categoría E (pérdida) en COP",
        example=10000000.0,
    )

    total_cartera: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera total del municipio en COP",
        example=1800000000.0,
    )

    total_captaciones: Optional[float] = Field(
        default=None,
        ge=0,
        description="Captaciones totales del municipio en COP",
        example=2500000000.0,
    )


class AnalisisResponse(BaseModel):
    """
    Modelo de salida para un análisis completado.

    CAMPOS CALCULADOS:
      - indice_riesgo: (C+D+E) / total_cartera
      - ratio_liquidez: captaciones / cartera
      - nivel_riesgo: clasificación por umbrales (Pattern Matching)

    Este modelo se usa para serializar la respuesta JSON automáticamente.
    """

    id: int = Field(..., description="ID único del análisis")
    municipio: str = Field(..., description="Nombre del municipio")
    indice_riesgo: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Índice de riesgo NPL = (C+D+E) / total_cartera",
    )
    ratio_liquidez: Optional[float] = Field(
        None,
        ge=0,
        description="Ratio de liquidez = captaciones / cartera",
    )
    nivel_riesgo: Optional[NivelRiesgo] = Field(
        None,
        description="Nivel de riesgo clasificado por umbrales",
    )
    mensaje: str = Field(..., description="Mensaje de estado del análisis")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "municipio": "Bogotá D.C.",
                "indice_riesgo": 0.0425,
                "ratio_liquidez": 1.35,
                "nivel_riesgo": "riesgo_moderado",
                "mensaje": "Análisis completado exitosamente",
            }
        }
    }


class HistorialItem(BaseModel):
    """
    Modelo para ítems del historial de análisis.
    """

    id: int
    municipio: str
    indice_riesgo: Optional[float]
    nivel_riesgo: Optional[NivelRiesgo]
    fecha_analisis: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "municipio": "Medellín",
                "indice_riesgo": 0.0312,
                "nivel_riesgo": "riesgo_moderado",
                "fecha_analisis": "2026-02-28T10:30:00",
            }
        }
    }


class MensajeBienvenida(BaseModel):
    """
    Modelo para el endpoint raíz (health check).
    """

    mensaje: str
    version: str
    documentacion: str
    endpoints: List[str]


# ══════════════════════════════════════════════════════════════════════════
# 2. BASE DE DATOS EN MEMORIA (para demo)
# ══════════════════════════════════════════════════════════════════════════

# En producción, esto sería una base de datos real (PostgreSQL, SQLite)
# Usamos un diccionario en memoria para simplificar la demo

DB_ANALISIS: dict[int, dict] = {}
CONTADOR_ID: int = 0


# ══════════════════════════════════════════════════════════════════════════
# 3. APLICACIÓN FASTAPI
# ══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=API_TITULO,
    version=API_VERSION,
    description=API_DESCRIPCION,
    contact=API_CONTACTO,
    license_info=API_LICENSE,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc (documentación alternativa)
    openapi_url="/openapi.json",
)


# ══════════════════════════════════════════════════════════════════════════
# 4. ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

@app.get(
    "/",
    response_model=MensajeBienvenida,
    status_code=status.HTTP_200_OK,
    tags=["Health Check"],
    summary="Mensaje de bienvenida",
    description="Endpoint raíz para verificar que la API está funcionando.",
)
async def raiz() -> MensajeBienvenida:
    """
    **Mensage de bienvenida y health check.**

    Este endpoint:
      - Verifica que la API está corriendo
      - Muestra la versión del sistema
      - Proporciona enlaces a la documentación

    **No requiere autenticación.**
    """
    return MensajeBienvenida(
        mensaje="🏦 API de Análisis de Riesgo Crediticio · Sistema Financiero Colombiano",
        version=API_VERSION,
        documentacion="/docs",
        endpoints=[
            "GET  /              → Health check",
            "GET  /historial     → Listar análisis",
            "GET  /historial/{id} → Obtener análisis específico",
            "POST /analizar      → Crear nuevo análisis",
            "DELETE /historial/{id} → Eliminar análisis",
        ],
    )


@app.get(
    "/historial",
    response_model=List[HistorialItem],
    status_code=status.HTTP_200_OK,
    tags=["Historial"],
    summary="Listar todos los análisis",
    description="Retorna una lista con todos los análisis guardados en la sesión.",
)
async def listar_historial() -> List[HistorialItem]:
    """
    **Lista todos los análisis guardados.**

    Retorna:
      - Lista vacía si no hay análisis
      - Lista con ítems si existen análisis

    **Ejemplo de respuesta:**
    ```json
    [
      {
        "id": 1,
        "municipio": "Bogotá D.C.",
        "indice_riesgo": 0.0425,
        "nivel_riesgo": "riesgo_moderado",
        "fecha_analisis": "2026-02-28T10:30:00"
      }
    ]
    ```
    """
    if not DB_ANALISIS:
        return []

    return [
        HistorialItem(
            id=analisis["id"],
            municipio=analisis["municipio"],
            indice_riesgo=analisis["indice_riesgo"],
            nivel_riesgo=analisis["nivel_riesgo"],
            fecha_analisis=analisis["fecha_analisis"],
        )
        for analisis in DB_ANALISIS.values()
    ]


@app.get(
    "/historial/{analisis_id}",
    response_model=HistorialItem,
    status_code=status.HTTP_200_OK,
    tags=["Historial"],
    summary="Obtener análisis específico",
    description="Obtiene los detalles de un análisis por su ID.",
    responses={
        404: {"description": "Análisis no encontrado"},
    },
)
async def obtener_analisis(analisis_id: int) -> HistorialItem:
    """
    **Obtiene un análisis específico por ID.**

    Args:
        analisis_id: ID único del análisis a consultar

    Returns:
        HistorialItem con los datos del análisis

    Raises:
        HTTPException 404: Si el análisis no existe
    """
    if analisis_id not in DB_ANALISIS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Análisis con ID {analisis_id} no encontrado",
        )

    analisis = DB_ANALISIS[analisis_id]
    return HistorialItem(
        id=analisis["id"],
        municipio=analisis["municipio"],
        indice_riesgo=analisis["indice_riesgo"],
        nivel_riesgo=analisis["nivel_riesgo"],
        fecha_analisis=analisis["fecha_analisis"],
    )


@app.post(
    "/analizar",
    response_model=AnalisisResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Análisis"],
    summary="Crear nuevo análisis",
    description="Crea un nuevo análisis de riesgo crediticio para un municipio.",
    responses={
        201: {"description": "Análisis creado exitosamente"},
        422: {"description": "Datos inválidos (validación Pydantic)"},
    },
)
async def crear_analisis(request: AnalisisRequest) -> AnalisisResponse:
    """
    **Crea un nuevo análisis de riesgo crediticio.**

    Este endpoint:
      1. Recibe datos del municipio (valida con Pydantic)
      2. Calcula indicadores (índice de riesgo, liquidez)
      3. Clasifica nivel de riesgo (Pattern Matching)
      4. Guarda en memoria y retorna resultado

    Args:
        request: AnalisisRequest con datos del municipio

    Returns:
        AnalisisResponse con indicadores calculados

    **Cálculos realizados:**
      - indice_riesgo = (cartera_c + cartera_d + cartera_e) / total_cartera
      - ratio_liquidez = total_captaciones / total_cartera
      - nivel_riesgo = clasificación por umbrales (0%, 1%, 5%, 15%)

    **Ejemplo de request:**
    ```json
    {
      "municipio": "Bogotá D.C.",
      "cartera_a": 1500000000,
      "cartera_c": 50000000,
      "cartera_d": 25000000,
      "cartera_e": 10000000,
      "total_cartera": 1800000000,
      "total_captaciones": 2500000000
    }
    ```
    """
    global CONTADOR_ID

    # Calcular indicadores
    cartera_mora = sum([
        request.cartera_c or 0,
        request.cartera_d or 0,
        request.cartera_e or 0,
    ])

    indice_riesgo: Optional[float] = None
    ratio_liquidez: Optional[float] = None
    nivel_riesgo: Optional[NivelRiesgo] = None

    if request.total_cartera and request.total_cartera > 0:
        indice_riesgo = cartera_mora / request.total_cartera

        if request.total_captaciones:
            ratio_liquidez = request.total_captaciones / request.total_cartera

        # Clasificar nivel de riesgo (Pattern Matching)
        nivel_riesgo = clasificar_nivel_riesgo(indice_riesgo)

    # Crear registro en "base de datos"
    CONTADOR_ID += 1
    DB_ANALISIS[CONTADOR_ID] = {
        "id": CONTADOR_ID,
        "municipio": request.municipio,
        "request": request.model_dump(),
        "indice_riesgo": indice_riesgo,
        "ratio_liquidez": ratio_liquidez,
        "nivel_riesgo": nivel_riesgo,
        "fecha_analisis": datetime.now(),
    }

    # Determinar mensaje según nivel de riesgo
    if nivel_riesgo:
        mensajes = {
            "sin_riesgo": "✅ Cartera perfectamente sana",
            "riesgo_bajo": "🟢 Cartera sana (monitoreo routine)",
            "riesgo_moderado": "🟡 Alerta temprana (revisar)",
            "riesgo_alto": "🟠 Deterioro (acción requerida)",
            "riesgo_critico": "🔴 Crítico (intervención inmediata)",
            "sin_datos": "⚪ Sin datos para clasificar",
        }
        mensaje = mensajes.get(nivel_riesgo, "Análisis completado")
    else:
        mensaje = "⚠️ No se pudo calcular índice (falta total_cartera)"

    return AnalisisResponse(
        id=CONTADOR_ID,
        municipio=request.municipio,
        indice_riesgo=indice_riesgo,
        ratio_liquidez=ratio_liquidez,
        nivel_riesgo=nivel_riesgo,
        mensaje=mensaje,
    )


@app.delete(
    "/historial/{analisis_id}",
    status_code=status.HTTP_200_OK,
    tags=["Historial"],
    summary="Eliminar análisis",
    description="Elimina un análisis específico por su ID.",
    responses={
        200: {"description": "Análisis eliminado exitosamente"},
        404: {"description": "Análisis no encontrado"},
    },
)
async def eliminar_analisis(analisis_id: int) -> dict:
    """
    **Elimina un análisis del historial.**

    Args:
        analisis_id: ID único del análisis a eliminar

    Returns:
        Diccionario con mensaje de confirmación

    Raises:
        HTTPException 404: Si el análisis no existe
    """
    if analisis_id not in DB_ANALISIS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Análisis con ID {analisis_id} no encontrado",
        )

    del DB_ANALISIS[analisis_id]

    return {
        "mensaje": f"Análisis {analisis_id} eliminado exitosamente",
        "id_eliminado": analisis_id,
    }


# ══════════════════════════════════════════════════════════════════════════
# 5. UTILIDADES
# ══════════════════════════════════════════════════════════════════════════

def clasificar_nivel_riesgo(indice_riesgo: Optional[float]) -> NivelRiesgo:
    """
    Clasifica el nivel de riesgo usando Pattern Matching (Python 3.10+).

    UMBRALES (Basel II/III, Circular 98 Superfinanciera):
      sin_riesgo     : NPL = 0%
      riesgo_bajo    : NPL < 1%
      riesgo_mod     : NPL < 5%
      riesgo_alto    : NPL < 15%
      riesgo_critico : NPL >= 15%

    Args:
        indice_riesgo: valor del índice NPL [0, 1] o None

    Returns:
        NivelRiesgo: clasificación correspondiente
    """
    if indice_riesgo is None:
        return "sin_datos"

    match indice_riesgo:
        case 0.0:
            return "sin_riesgo"
        case default if default < 0.01:
            return "riesgo_bajo"
        case default if default < 0.05:
            return "riesgo_moderado"
        case default if default < 0.15:
            return "riesgo_alto"
        case _:
            return "riesgo_critico"


# ══════════════════════════════════════════════════════════════════════════
# 6. SERVIDOR DE DESARROLLO
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 65)
    print("  API DE ANÁLISIS DE RIESGO CREDITICIO")
    print("  Sistema Financiero Colombiano · FastAPI")
    print("=" * 65)
    print("\n  Iniciando servidor de desarrollo...")
    print("\n  URLs disponibles:")
    print("    · http://127.0.0.1:8000       → Health check")
    print("    · http://127.0.0.1:8000/docs  → Swagger UI interactivo")
    print("    · http://127.0.0.1:8000/redoc → ReDoc")
    print("\n  Presione Ctrl+C para detener el servidor")
    print("=" * 65)

    uvicorn.run(
        "api_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info",
    )
