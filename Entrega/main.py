# ╔════════════════════════════════════════════════════════════════════════╗
# ║  MI API DE ANÁLISIS — RIESGO CREDITICIO                               ║
# ║  Sistema Financiero Colombiano — Datos Abiertos Gov.co                ║
# ║  Proyecto Personal (Semanas 1-3)                                      ║
# ╠════════════════════════════════════════════════════════════════════════╣
# ║  Autor: Angela Rico · Sebastian Ramirez                               ║
# ║  Curso: Python para APIs e IA Aplicada                                ║
# ║  Universidad: Universidad Santo Tomás · 2026                          ║
# ║                                                                       ║
# ║  Ejecute con: uvicorn main:app --reload                               ║
# ║  Visite: http://127.0.0.1:8000/docs                                   ║
# ╠════════════════════════════════════════════════════════════════════════╣
# ║  CONCEPTOS APLICADOS EN ESTE ARCHIVO:                                 ║
# ║                                                                       ║
# ║  SEMANA 1:                                                            ║
# ║    · Pattern Matching (match/case) → clasificar_nivel_riesgo()        ║
# ║    · Decoradores simples → @registrar_ejecucion (decorators.py)       ║
# ║    · Type hints (Literal, Optional, List) → todo el código            ║
# ║                                                                       ║
# ║  SEMANA 2:                                                            ║
# ║    · Pydantic (BaseModel, Field, field_validator) → modelos I/O       ║
# ║    · OOP Herencia + Polimorfismo → AnalizadorMuestral                 ║
# ║    · Función pura → procesar_riesgo_crediticio()                      ║
# ║                                                                       ║
# ║  SEMANA 3:                                                            ║
# ║    · FastAPI → @app.get, @app.post, @app.delete                       ║
# ║    · CRUD completo → POST, GET, GET/{id}, DELETE/{id}                 ║
# ║    · async def → endpoints asíncronos                                 ║
# ║    · Swagger UI → documentación automática en /docs                   ║
# ╚════════════════════════════════════════════════════════════════════════╝

# ── Terceros ─────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
import numpy as np
import pandas as pd
from datetime import datetime
import os
import io

# ── Locales ──────────────────────────────────────────────────────────────
# CONCEPTO: Decorador simple (Semana 1) — importamos el decorador
# @registrar_ejecucion que mide tiempo de ejecución sin modificar
# el código de la función (principio Open/Closed).
from decorators import registrar_ejecucion

# CONCEPTO: OOP Herencia + Polimorfismo (Semana 2) — importamos
# AnalizadorMuestral que hereda de AnalizadorEstadistico y sobreescribe
# calcular_varianza() para usar ddof=1 (corrección de Bessel).
from modelos import AnalizadorMuestral


# ════════════════════════════════════════════════════════════════════════════════
# FASE 2 — MODELOS PYDANTIC
# ════════════════════════════════════════════════════════════════════════════════

class RiesgoCrediticioInput(BaseModel):
    """
    Modelo de ENTRADA para análisis de riesgo crediticio.
    
    DOMINIO: Sistema financiero colombiano — evaluación de cartera bancaria.
    
    VALIDACIONES IMPLEMENTADAS:
      - municipio: string, mín 2 caracteres (evita nombres vacíos)
      - cartera_a a cartera_e: floats ≥ 0 (no puede haber cartera negativa)
      - total_cartera: float > 0 (requiere cartera positiva para calcular)
      - total_captaciones: float ≥ 0, opcional (puede no tener datos)
    """
    
    municipio: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="Nombre del municipio a analizar",
        example="Bogotá D.C.",
    )
    
    cartera_a: float = Field(
        ...,
        ge=0,
        description="Cartera categoría A (normal) en COP",
        example=1500000000.0,
    )
    
    cartera_b: float = Field(
        ...,
        ge=0,
        description="Cartera categoría B (observación) en COP",
        example=200000000.0,
    )
    
    cartera_c: float = Field(
        ...,
        ge=0,
        description="Cartera categoría C (subestándar) en COP",
        example=50000000.0,
    )
    
    cartera_d: float = Field(
        ...,
        ge=0,
        description="Cartera categoría D (dudosa) en COP",
        example=25000000.0,
    )
    
    cartera_e: float = Field(
        ...,
        ge=0,
        description="Cartera categoría E (pérdida) en COP",
        example=10000000.0,
    )
    
    total_cartera: float = Field(
        ...,
        gt=0,
        description="Cartera total del municipio en COP (debe ser > 0)",
        example=1800000000.0,
    )
    
    total_captaciones: Optional[float] = Field(
        default=None,
        ge=0,
        description="Captaciones totales del municipio en COP (opcional)",
        example=2500000000.0,
    )
    
    @field_validator("municipio", mode="before")
    @classmethod
    def normalizar_municipio(cls, v: str) -> str:
        """Limpia nombre de municipio: '  BOGOTÁ  ' → 'Bogotá'."""
        return str(v).strip().title() if v else ""


class RiesgoCrediticioOutput(BaseModel):
    """
    Modelo de SALIDA con resultados del análisis.
    
    CAMPOS CALCULADOS (5+ campos numéricos):
      1. indice_riesgo: (C+D+E) / total_cartera — NPL Ratio
      2. ratio_liquidez: captaciones / cartera — salud financiera
      3. pct_cartera_sana: A / total — porcentaje saludable
      4. pct_cartera_mora: (C+D+E) / total — porcentaje en mora
      5. concentracion_riesgo: (D+E) / (C+D+E) — severidad de mora
      6. n_niveles: cantidad de categorías con valor > 0
    """
    
    id: int = Field(..., description="ID único del análisis")
    
    municipio: str = Field(..., description="Nombre del municipio")
    
    indice_riesgo: float = Field(
        ...,
        ge=0,
        le=1,
        description="Índice de riesgo NPL = (C+D+E) / total_cartera",
    )
    
    ratio_liquidez: Optional[float] = Field(
        None,
        ge=0,
        description="Ratio de liquidez = captaciones / cartera",
    )
    
    pct_cartera_sana: float = Field(
        ...,
        ge=0,
        le=100,
        description="Porcentaje de cartera sana (categoría A)",
    )
    
    pct_cartera_mora: float = Field(
        ...,
        ge=0,
        le=100,
        description="Porcentaje de cartera en mora (C+D+E)",
    )
    
    concentracion_riesgo: float = Field(
        ...,
        ge=0,
        le=100,
        description="Concentración de riesgo severo (D+E dentro de mora)",
    )
    
    n_niveles: int = Field(
        ...,
        ge=1,
        description="Cantidad de categorías con valor > 0",
    )
    
    nivel_riesgo: Literal[
        "sin_riesgo",
        "riesgo_bajo",
        "riesgo_moderado",
        "riesgo_alto",
        "riesgo_critico",
    ] = Field(..., description="Clasificación por umbrales")
    
    mensaje: str = Field(..., description="Mensaje interpretativo")
    
    fecha_analisis: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del análisis",
    )

class HistorialAnalisisResponse(BaseModel):
    """
    Modelo de SALIDA para un elemento del historial.
    Asegura que las respuestas del GET /historial/{id} estén tipadas.
    """
    id: int = Field(..., description="ID único del análisis")
    municipio: str = Field(..., description="Nombre del municipio")
    request: dict = Field(..., description="Datos originales de la petición")
    resultados: dict = Field(..., description="Resultados calculados del análisis")
    fecha_analisis: datetime = Field(..., description="Timestamp del análisis")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "municipio": "Bogotá D.C.",
                "request": {"municipio": "Bogotá D.C.", "total_cartera": 1800000000},
                "resultados": {"indice_riesgo": 0.0472, "nivel_riesgo": "riesgo_moderado"},
                "fecha_analisis": "2026-03-04T12:00:00"
            }
        }
    }


# ════════════════════════════════════════════════════════════════════════════════
# FASE 3 — FUNCIÓN DE PROCESAMIENTO (PURA, SIN FASTAPI)
# ════════════════════════════════════════════════════════════════════════════════

# CONCEPTO: Decorador simple (Semana 1)
# @registrar_ejecucion envuelve procesar_riesgo_crediticio() para:
#   1. Imprimir timestamp de inicio y fin
#   2. Medir duración en milisegundos
#   3. SIN modificar el código de la función (Open/Closed Principle)
#
# POR QUÉ DECORADORES Y NO UN print() DIRECTO:
#   - El decorador es REUTILIZABLE en cualquier función
#   - Se puede quitar/poner sin tocar la lógica de negocio
#   - Sigue el principio de responsabilidad única (SRP)

@registrar_ejecucion
def procesar_riesgo_crediticio(datos: dict, historical_npl: list[float] = None) -> dict:
    """
    Función PURA que procesa datos de riesgo crediticio.
    
    REQUISITOS CUMPLIDOS:
      ✓ Recibe datos validados y retorna diccionario con resultados
      ✓ Usa numpy para 5+ cálculos estadísticos
      ✓ Usa AnalizadorMuestral (OOP + Polimorfismo) para estadísticos
      ✓ Redondea todos los valores a 4 decimales
      ✓ Independiente de FastAPI (se puede probar sin el framework)
    
    CONCEPTOS USADOS AQUÍ:
      · @registrar_ejecucion → Decorador (Semana 1)
      · AnalizadorMuestral   → OOP Herencia + Polimorfismo (Semana 2)
      · np.array, np.sum     → NumPy para cálculos (Semana 2)
      · match/case           → Pattern Matching (Semana 1) vía clasificar_nivel_riesgo()
    
    Args:
        datos: diccionario con cartera_a, cartera_b, ..., total_cartera
    
    Returns:
        dict: resultados con todos los cálculos estadísticos
    """
    # Convertir a array numpy para cálculos (NumPy — Semana 2)
    cartera = np.array([
        datos.get("cartera_a", 0),
        datos.get("cartera_b", 0),
        datos.get("cartera_c", 0),
        datos.get("cartera_d", 0),
        datos.get("cartera_e", 0),
    ], dtype=float)
    
    total = datos.get("total_cartera", 0)
    captaciones = datos.get("total_captaciones")
    
    # ── Cálculos financieros ─────────────────────────────────────────────
    
    # Cálculo 1: Cartera en mora (C + D + E)
    cartera_mora = np.sum(cartera[2:])  # índices 2, 3, 4 = C, D, E
    
    # Cálculo 2: Índice de riesgo NPL (mora / total)
    indice_riesgo = round(float(cartera_mora / total), 4) if total > 0 else 0.0
    
    # Cálculo 3: Ratio de liquidez (captaciones / cartera)
    ratio_liquidez = None
    if captaciones is not None and total > 0:
        ratio_liquidez = round(float(captaciones / total), 4)
    
    # Cálculo 4: Porcentaje cartera sana (A / total)
    pct_cartera_sana = round(float((cartera[0] / total) * 100), 4) if total > 0 else 0.0
    
    # Cálculo 5: Porcentaje cartera en mora ((C+D+E) / total)
    pct_cartera_mora = round(float((cartera_mora / total) * 100), 4) if total > 0 else 0.0
    
    # Cálculo 6: Concentración de riesgo severo ((D+E) / (C+D+E))
    cartera_severa = np.sum(cartera[3:])  # D + E
    concentracion_riesgo = 0.0
    if cartera_mora > 0:
        concentracion_riesgo = round(float((cartera_severa / cartera_mora) * 100), 4)
    
    # Cálculo 7: Cantidad de niveles con valor > 0
    n_niveles = int(np.sum(cartera > 0))
    
    # ── Estadísticos con OOP (Herencia + Polimorfismo — Semana 2) ────────
    # En lugar de calcular varianza sobre las 5 bolsas del mismo municipio,
    # calculamos la varianza muestral sobre el histórico de NPLs de todos
    # los municipios evaluados hasta el momento (o el actual si es el primero).
    
    npls_a_evaluar = historical_npl.copy() if historical_npl else []
    npls_a_evaluar.append(indice_riesgo)
    
    analizador_npl = AnalizadorMuestral(
        nombre="Distribución de NPL Multirregional",
        datos=npls_a_evaluar,
    )
    resumen_oop = analizador_npl.resumen()
    
    # Cálculo 8-12: Extraer estadísticos del analizador OOP
    media_cartera = resumen_oop["media"]
    std_cartera = resumen_oop["std"]
    var_cartera = resumen_oop["varianza"]
    cv_cartera = resumen_oop["cv_pct"]
    
    # Cálculo 12: Índice de Herfindahl-Hirschman (concentración)
    # HHI = suma de (participación^2)
    participaciones = cartera / total if total > 0 else np.zeros(5)
    hhi = round(float(np.sum(participaciones ** 2)), 4)
    
    # ── Clasificación con Pattern Matching (Semana 1) ────────────────────
    nivel_riesgo = clasificar_nivel_riesgo(indice_riesgo)
    
    # Generar mensaje interpretativo
    mensajes = {
        "sin_riesgo": "[OK] Cartera perfectamente sana (NPL = 0%)",
        "riesgo_bajo": "[BAJO] Cartera sana -- monitoreo routine (NPL < 1%)",
        "riesgo_moderado": "[MODERADO] Alerta temprana -- revisar (NPL < 5%)",
        "riesgo_alto": "[ALTO] Deterioro -- accion requerida (NPL < 15%)",
        "riesgo_critico": "[CRITICO] Intervencion inmediata (NPL >= 15%)",
    }
    mensaje = mensajes.get(nivel_riesgo, "Análisis completado")
    
    return {
        "indice_riesgo": indice_riesgo,
        "ratio_liquidez": ratio_liquidez,
        "pct_cartera_sana": pct_cartera_sana,
        "pct_cartera_mora": pct_cartera_mora,
        "concentracion_riesgo": concentracion_riesgo,
        "n_niveles": n_niveles,
        "nivel_riesgo": nivel_riesgo,
        "mensaje": mensaje,
        # Estadísticos calculados con OOP (AnalizadorMuestral)
        "media_cartera": media_cartera,
        "std_cartera": std_cartera,
        "var_cartera": var_cartera,
        "cv_cartera": cv_cartera,
        "hhi": hhi,
        # Metadata del análisis OOP
        "tipo_analisis": resumen_oop["tipo"],  # "muestral" (ddof=1)
    }


def clasificar_nivel_riesgo(indice: float) -> str:
    """
    Clasifica el nivel de riesgo usando Pattern Matching (Python 3.10+).
    
    UMBRALES (Basel II/III, Circular 98 Superfinanciera):
      sin_riesgo     : NPL = 0%
      riesgo_bajo    : NPL < 1%
      riesgo_mod     : NPL < 5%
      riesgo_alto    : NPL < 15%
      riesgo_critico : NPL >= 15%
    """
    if indice is None:
        return "sin_datos"
    
    match indice:
        case 0.0:
            return "sin_riesgo"
        case default_val if default_val < 0.01:
            return "riesgo_bajo"
        case default_val if default_val < 0.05:
            return "riesgo_moderado"
        case default_val if default_val < 0.15:
            return "riesgo_alto"
        case _:
            return "riesgo_critico"


# ════════════════════════════════════════════════════════════════════════════════
# FASE 4 — APP FASTAPI + ENDPOINTS CRUD
# ════════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="API de Análisis de Riesgo Crediticio",
    description="""
## Sistema Financiero Colombiano — Datos Abiertos Gov.co

Esta API permite:
- **Analizar** riesgo crediticio de municipios colombianos
- **Consultar** historial de análisis realizados
- **Eliminar** análisis específicos

### Dominio
Evaluación de cartera bancaria usando el índice NPL (Non-Performing Loans).

### Validaciones
- Cartera debe ser ≥ 0 (no hay cartera negativa)
- Total cartera debe ser > 0 (requiere cartera para calcular)
- Municipio debe tener ≥ 2 caracteres
    """,
    version="1.0.0",
    contact={
        "name": "Angela Rico · Sebastian Ramirez",
        "url": "https://github.com/angelaricortega/Python",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configurar CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos (HTML, CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", tags=["UI"], include_in_schema=True)
async def home():
    """
    **Interfaz Web Principal** — Dashboard interactivo para análisis de riesgo crediticio.
    
    Características:
    - Carga de archivos CSV/Excel
    - Formulario manual de entrada
    - Visualización de resultados con gráficos
    - Historial de análisis
    - Explicación educativa del NPL
    """
    from fastapi.responses import FileResponse
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"mensaje": "🌸 Interfaz en construcción - Usa /docs para Swagger UI"}

# Base de datos en memoria (diccionario)
historial_analisis: dict[int, dict] = {}
contador_id: int = 0

@app.get(
    "/health",
    tags=["Health Check"],
    summary="Mensaje de bienvenida",
)
async def raiz():
    """
    **Health check** — Verifica que la API está funcionando.
    """
    return {
        "mensaje": "🏦 API de Riesgo Crediticio · Sistema Financiero Colombiano",
        "version": "1.0.0",
        "documentacion": "/docs",
    }


@app.post(
    "/analizar",
    response_model=RiesgoCrediticioOutput,
    status_code=status.HTTP_201_CREATED,
    tags=["Análisis"],
    summary="Crear nuevo análisis",
)
async def analizar_riesgo(datos: RiesgoCrediticioInput) -> RiesgoCrediticioOutput:
    """
    **Crea un nuevo análisis de riesgo crediticio.**
    
    Proceso:
    1. Recibe datos validados por Pydantic
    2. Procesa con función pura (numpy, 5+ cálculos)
    3. Guarda en historial (memoria)
    4. Retorna resultado con interpretación
    
    **Cálculos realizados:**
    - Índice de riesgo NPL
    - Ratio de liquidez
    - Porcentaje cartera sana/mora
    - Concentración de riesgo
    - Estadísticos (media, std, var, CV, HHI)
    """
    global contador_id
    
    # Extraer NPLs historicos para el cálculo estadístico muestral multirregional
    historical_npls = [a["resultados"]["indice_riesgo"] for a in historial_analisis.values()]
    
    # Procesar datos con función pura
    resultados = procesar_riesgo_crediticio(datos.model_dump(), historical_npls)
    
    # Guardar en historial
    contador_id += 1
    historial_analisis[contador_id] = {
        "id": contador_id,
        "municipio": datos.municipio,
        "request": datos.model_dump(),
        "resultados": resultados,
        "fecha_analisis": datetime.now(),
    }
    
    # Retornar respuesta
    return RiesgoCrediticioOutput(
        id=contador_id,
        municipio=datos.municipio,
        indice_riesgo=resultados["indice_riesgo"],
        ratio_liquidez=resultados["ratio_liquidez"],
        pct_cartera_sana=resultados["pct_cartera_sana"],
        pct_cartera_mora=resultados["pct_cartera_mora"],
        concentracion_riesgo=resultados["concentracion_riesgo"],
        n_niveles=resultados["n_niveles"],
        nivel_riesgo=resultados["nivel_riesgo"],
        mensaje=resultados["mensaje"],
        fecha_analisis=historial_analisis[contador_id]["fecha_analisis"],
    )


@app.post(
    "/upload",
    tags=["Análisis"],
    summary="Cargar archivo para análisis masivo",
)
async def cargar_archivo(file: UploadFile = File(...)):
    """
    **Carga un archivo CSV o Excel para análisis masivo.**
    
    Proceso:
    1. Lee el archivo (CSV o Excel)
    2. Intenta mapear columnas (colocaciones, captaciones, municipio)
    3. Procesa cada fila y guarda en historial
    4. Retorna resumen del procesamiento
    """
    global contador_id
    content = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(400, "Formato de archivo no soportado. Use CSV o Excel.")
            
        # Normalizar nombres de columnas (quitar acentos, espacios, lower)
        df.columns = [str(c).strip().lower().replace('ó', 'o').replace('á', 'a') for c in df.columns]
        
        # Mapeo flexible de columnas
        mapeo = {
            "municipio": ["municipio", "nombre", "ciudad", "territorio"],
            "cartera_a": ["cartera_a", "colocaciones_a", "clase_a"],
            "cartera_b": ["cartera_b", "colocaciones_b", "clase_b"],
            "cartera_c": ["cartera_c", "colocaciones_c", "clase_c"],
            "cartera_d": ["cartera_d", "colocaciones_d", "clase_d"],
            "cartera_e": ["cartera_e", "colocaciones_e", "clase_e"],
            "total_cartera": ["total_cartera", "colocaciones", "total_colocaciones"],
            "total_captaciones": ["total_captaciones", "captaciones", "depositos", "ahorros"]
        }
        
        results = []
        for _, row in df.iterrows():
            # Extraer datos con el mapeo flexible
            data_dict = {}
            for key, aliases in mapeo.items():
                col_found = next((c for c in df.columns if c in aliases), None)
                data_dict[key] = row.get(col_found) if col_found else (0 if key != "municipio" else "Desconocido")
            
            try:
                # Validar y procesar cada fila
                input_data = RiesgoCrediticioInput(**data_dict)
                historical_npls = [a["resultados"]["indice_riesgo"] for a in historial_analisis.values()]
                res = procesar_riesgo_crediticio(input_data.model_dump(), historical_npls)
                
                contador_id += 1
                historial_analisis[contador_id] = {
                    "id": contador_id,
                    "municipio": input_data.municipio,
                    "request": input_data.model_dump(),
                    "resultados": res,
                    "fecha_analisis": datetime.now(),
                }
                results.append(contador_id)
            except Exception as e:
                print(f"Error procesando fila: {e}")
                continue
                
        return {
            "mensaje": f"Se procesaron {len(results)} registros correctamente.",
            "ids_creados": results
        }
    except Exception as e:
        raise HTTPException(500, f"Error al procesar el archivo: {str(e)}")


@app.get(
    "/historial",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    tags=["Historial"],
    summary="Listar todos los análisis",
)
async def listar_historial():
    """
    **Lista todos los análisis guardados.**
    
    Retorna lista vacía si no hay análisis.
    """
    if not historial_analisis:
        return []
    
    return [
        {
            "id": a["id"],
            "municipio": a["municipio"],
            "indice_riesgo": a["resultados"]["indice_riesgo"],
            "nivel_riesgo": a["resultados"]["nivel_riesgo"],
            "fecha_analisis": a["fecha_analisis"].isoformat(),
        }
        for a in historial_analisis.values()
    ]


@app.get(
    "/historial/{analisis_id}",
    response_model=HistorialAnalisisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Historial"],
    summary="Obtener análisis específico",
    responses={404: {"description": "Análisis no encontrado"}},
)
async def obtener_analisis(analisis_id: int):
    """
    **Obtiene un análisis específico por ID.**
    
    Args:
        analisis_id: ID único del análisis
    
    Raises:
        HTTPException 404: Si el análisis no existe
    """
    if analisis_id not in historial_analisis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Análisis con ID {analisis_id} no encontrado. "
                   f"IDs válidos: 1 a {contador_id}",
        )
    
    analisis = historial_analisis[analisis_id]
    return {
        "id": analisis["id"],
        "municipio": analisis["municipio"],
        "request": analisis["request"],
        "resultados": analisis["resultados"],
        "fecha_analisis": analisis["fecha_analisis"].isoformat(),
    }


@app.delete(
    "/historial/{analisis_id}",
    status_code=status.HTTP_200_OK,
    tags=["Historial"],
    summary="Eliminar análisis",
    responses={404: {"description": "Análisis no encontrado"}},
)
async def eliminar_analisis(analisis_id: int):
    """
    **Elimina un análisis del historial.**
    
    Args:
        analisis_id: ID único del análisis a eliminar
    
    Raises:
        HTTPException 404: Si el análisis no existe
    """
    if analisis_id not in historial_analisis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Análisis con ID {analisis_id} no encontrado",
        )
    
    del historial_analisis[analisis_id]
    
    return {
        "mensaje": f"✅ Análisis {analisis_id} eliminado exitosamente",
        "id_eliminado": analisis_id,
        "analisis_restantes": len(historial_analisis),
    }


# ════════════════════════════════════════════════════════════════════════════════
# SERVIDOR DE DESARROLLO
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 65)
    print("  API DE ANÁLISIS DE RIESGO CREDITICIO")
    print("  Sistema Financiero Colombiano · FastAPI")
    print("=" * 65)
    print("\n  Iniciando servidor de desarrollo...")
    print("\n  URLs disponibles:")
    print("    * http://127.0.0.1:8000       -> Health check")
    print("    * http://127.0.0.1:8000/docs  -> Swagger UI interactivo")
    print("    * http://127.0.0.1:8000/redoc -> ReDoc")
    print("\n  Presione Ctrl+C para detener el servidor")
    print("=" * 65)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
