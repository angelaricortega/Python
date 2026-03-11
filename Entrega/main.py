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

# CONCEPTO: Modularización (Semana 1) — importamos funciones puras
# para limpieza de DataFrames: eliminar_duplicados, imputar_nulos,
# detectar_outliers_iqr, limpieza_completa
from limpieza import limpieza_completa, eliminar_duplicados, detectar_outliers_iqr


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

### 📊 ¿Qué hace esta API?

Esta API **NO es solo un visor de datos**. Realiza **cálculos estadísticos y financieros** sobre los datos que proporcionas:

| Lo que tú ingresas | Lo que la API calcula |
|-------------------|----------------------|
| Cartera A, B, C, D, E (en COP) | **Índice NPL** = (C+D+E) / Total Cartera |
| Total de cartera (en COP) | **Porcentaje cartera sana** = A / Total × 100 |
| Total de captaciones (en COP, opcional) | **Porcentaje cartera en mora** = (C+D+E) / Total × 100 |
| | **Concentración de riesgo** = (D+E) / (C+D+E) × 100 |
| | **Índice HHI** (Herfindahl-Hirschman) para concentración |
| | **Estadísticos muestrales** (media, varianza, std, CV) |

### 🔢 Unidades de Medida

**Todos los valores monetarios deben estar en PESOS COLOMBIANOS (COP):**

- `cartera_a`, `cartera_b`, `cartera_c`, `cartera_d`, `cartera_e`: Valor de la cartera en cada categoría (COP)
- `total_cartera`: Suma total de la cartera (COP)
- `total_captaciones`: Total de depósitos/captaciones del municipio (COP)

**Ejemplo:**
```json
{
  "municipio": "Bogotá D.C.",
  "cartera_a": 1500000000,      // 1.500 millones de pesos
  "cartera_b": 200000000,       // 200 millones de pesos
  "cartera_c": 50000000,        // 50 millones de pesos
  "cartera_d": 25000000,        // 25 millones de pesos
  "cartera_e": 10000000,        // 10 millones de pesos
  "total_cartera": 1785000000,  // Suma total
  "total_captaciones": 2500000000  // 2.500 millones en captaciones
}
```

### 🏛️ Fuente de Datos

**Datos Abiertos Colombia (datos.gov.co)**

Esta API está diseñada para trabajar con el dataset oficial del Gobierno Colombiano:

- **Dataset**: "Saldo de las captaciones y colocaciones por municipios"
- **Fuente**: Sistema Financiero Colombiano
- **Plataforma**: [www.datos.gov.co](https://www.datos.gov.co/)
- **Entidad responsable**: Superintendencia Financiera de Colombia

### 📁 Tratamiento de Datos del datos.gov.co

Cuando cargas el archivo CSV del datos.gov.co, la API realiza el siguiente proceso:

#### 1. **Lectura y Validación**
```
┌─────────────────────────────────────────────────────────────┐
│  Archivo CSV (80 columnas)                                  │
│  Saldo_de_las_captaciones_y_colocaciones_por_municipios.csv │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Verificación de columnas requeridas:                       │
│  ✓ Nombre del municipio                                     │
│  ✓ Cartera de créditos                                      │
│  ✓ Categoría A riesgo normal                                │
│  ✓ Categoría B riesgo aceptable                             │
│  ✓ Categoría C riesgo apreciable                            │
│  ✓ Categoría D riesgo significativo                         │
│  ✓ Categoría E riesgo de Incobrabilidad                     │
└─────────────────────────────────────────────────────────────┘
```

#### 2. **Limpieza de Datos**
```
┌─────────────────────────────────────────────────────────────┐
│  Problemas detectados y corregidos:                         │
│  • Valores nulos → Imputados con 0                          │
│  • Formato "1.234.567,89" → Convertido a 1234567.89         │
│  • Símbolos "$", "COP" → Eliminados                         │
│  • Municipios duplicados → Se conserva el primero           │
│  • Filas sin municipio → Eliminadas                         │
│  • Total cartera = 0 → Fila descartada                      │
└─────────────────────────────────────────────────────────────┘
```

#### 3. **Transformación**
```
Columnas originales (datos.gov.co)  →  Columnas API
─────────────────────────────────────────────────────
Nombre del municipio                →  municipio
Cartera de créditos                 →  total_cartera
Categoría A riesgo normal           →  cartera_a
Categoría B riesgo aceptable        →  cartera_b
Categoría C riesgo apreciable       →  cartera_c
Categoría D riesgo significativo    →  cartera_d
Categoría E riesgo de Incobrabilidad→  cartera_e
Depósitos en cuenta corriente       →  (suma para)
Depósitos simples                   →  (suma para)
Certificados de depósito a término  →   total_captaciones
Depósitos de ahorro                 →  (suma para)
... (otras columnas de depósitos)   →
```

#### 4. **Cálculo de Indicadores**
```
Para CADA municipio procesado:

  Índice NPL = (cartera_c + cartera_d + cartera_e) / total_cartera
  
  Porcentaje Sana = cartera_a / total_cartera × 100
  
  Porcentaje Mora = (cartera_c + cartera_d + cartera_e) / total_cartera × 100
  
  Concentración Riesgo = (cartera_d + cartera_e) / (cartera_c + cartera_d + cartera_e) × 100
  
  Índice HHI = Σ(participación_i)²
  
  Clasificación = match(NPL):
    - 0% → sin_riesgo
    - <1% → riesgo_bajo
    - <5% → riesgo_moderado
    - <15% → riesgo_alto
    - ≥15% → riesgo_critico
```

### ✅ Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/analizar` | POST | Análisis manual de un municipio |
| `/upload` | POST | Carga masiva de CSV/Excel genérico |
| `/datos-gov/cargar` | POST | Carga específica del archivo datos.gov.co |
| `/datos-gov/info` | GET | Información del formato esperado |
| `/historial` | GET | Listar todos los análisis |
| `/historial/{id}` | GET | Obtener análisis específico |
| `/historial/{id}` | DELETE | Eliminar análisis |
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
    2. Aplica pipeline de limpieza (Semana 1): eliminar duplicados, imputar nulos, detectar outliers
    3. Intenta mapear columnas (colocaciones, captaciones, municipio)
    4. Procesa cada fila y guarda en historial
    5. Retorna resumen del procesamiento

    CONCEPTO SEMANA 1 — Modularización:
      Usa el módulo limpieza.py para aplicar funciones puras de limpieza
      antes de procesar los datos.
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
        df.columns = [str(c).strip().lower().replace('ó', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ú', 'u') for c in df.columns]

        # ═══════════════════════════════════════════════════════════════════════════
        # FASE 1 — LIMPIEZA DE DATOS (Semana 1)
        # ═══════════════════════════════════════════════════════════════════════════
        # Aplicar pipeline de limpieza con funciones puras del módulo limpieza.py
        columnas_numericas = ['cartera_a', 'cartera_b', 'cartera_c', 'cartera_d', 'cartera_e', 'total_cartera', 'total_captaciones']
        df_limpio = limpieza_completa(
            df,
            columnas_numericas=columnas_numericas,
            columna_municipio='municipio',
            estrategia_imputacion='mediana'
        )
        # ═══════════════════════════════════════════════════════════════════════════

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
        for _, row in df_limpio.iterrows():  # Usar df_limpio en lugar de df
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
# ENDPOINT PARA DATOS.GOV.CO — CAPTACIONES Y COLOCACIONES
# ════════════════════════════════════════════════════════════════════════════════

@app.post(
    "/datos-gov/cargar",
    status_code=status.HTTP_200_OK,
    tags=["Datos.gov.co"],
    summary="Cargar archivo CSV de Datos.gov.co",
)
async def cargar_datos_gov(file: UploadFile = File(...)):
    """
    **Carga el archivo CSV de captaciones y colocaciones de Datos.gov.co**

    Este endpoint está diseñado específicamente para el archivo:
    `Saldo_de_las_captaciones_y_colocaciones_por_municipios_*.csv`

    El archivo contiene:
      - 80 columnas con información detallada del sistema financiero
      - Categorías de riesgo A, B, C, D, E
      - Depósitos, captaciones y colocaciones por municipio

    Proceso:
      1. Lee el archivo CSV
      2. Mapea columnas del formato gov.co al formato de la API
      3. Aplica limpieza de datos
      4. Procesa cada municipio
      5. Guarda en historial

    Returns:
        dict: Resumen del procesamiento con IDs creados
    """
    global contador_id

    content = await file.read()

    try:
        # Leer CSV
        df = pd.read_csv(io.BytesIO(content), encoding='utf-8', nrows=1000)

        # ═══════════════════════════════════════════════════════════════════════════
        # MAPEO DE COLUMNAS - Formato Datos.gov.co → Formato API
        # ═══════════════════════════════════════════════════════════════════════════

        # Columnas del archivo gov.co
        COL_MUNICIPIO = "Nombre del municipio"
        COL_CARTERA_CREDITOS = "Cartera de créditos"
        
        # Categorías de riesgo (columnas principales)
        COL_CAT_A = "Categoría A riesgo normal"
        COL_CAT_B = "Categoría B riesgo aceptable"
        COL_CAT_C = "Categoría C riesgo apreciable"
        COL_CAT_D = "Categoría D riesgo significativo"
        COL_CAT_E = "Categoría E riesgo de Incobrabilidad"

        # Columnas de depósitos/captaciones (sumar para total)
        COLS_CAPTACIONES = [
            "Depósitos en cuenta corriente bancaria",
            "Depósitos simples",
            "Certificados de depósito a término",
            "Depósitos de ahorro",
            "Cuenta de ahorros de valor real",
            "Cuentas de ahorro especial",
            "Certificado de ahorro valor real",
            "Títulos de inversión en circulación",
        ]

        # Verificar columnas requeridas
        columnas_requeridas = [
            COL_MUNICIPIO, COL_CARTERA_CREDITOS,
            COL_CAT_A, COL_CAT_B, COL_CAT_C, COL_CAT_D, COL_CAT_E
        ]

        columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
        if columnas_faltantes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Columnas faltantes en el archivo: {columnas_faltantes}"
            )

        # ═══════════════════════════════════════════════════════════════════════════
        # TRANSFORMACIÓN DE DATOS
        # ═══════════════════════════════════════════════════════════════════════════

        # Función para limpiar valores monetarios (ej: "1.500.000,00" → 1500000.00)
        def limpiar_moneda(valor, permitir_cero=True):
            """
            Limpia y convierte valores monetarios a float.
            
            Args:
                valor: Valor a limpiar (puede ser string, int, float, None)
                permitir_cero: Si False, retorna None para valores 0 o vacíos
            
            Returns:
                float o None: Valor limpio, o None si está vacío y no se permite cero
            """
            # Manejo de valores nulos o vacíos
            if valor is None:
                return 0.0 if permitir_cero else None
            if pd.isna(valor):
                return 0.0 if permitir_cero else None
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == '' or valor.upper() == 'NAN':
                    return 0.0 if permitir_cero else None
            if isinstance(valor, (int, float)) and valor == 0:
                return 0.0 if permitir_cero else None
            
            try:
                # Convertir a string y limpiar
                s = str(valor).strip()
                # Quitar símbolos de moneda y espacios
                s = s.replace('$', '').replace('COP', '').replace(' ', '')
                # Manejar formato colombiano: 1.234.567,89 → 1234567.89
                s = s.replace('.', '').replace(',', '.')
                return float(s)
            except (ValueError, TypeError, AttributeError):
                return 0.0 if permitir_cero else None

        # Función para validar que una fila tenga datos mínimos requeridos
        def fila_valida(row):
            """Verifica que la fila tenga al menos municipio y total_cartera > 0"""
            # Municipio válido
            if not row['municipio'] or pd.isna(row['municipio']):
                return False, "Municipio vacío"
            if str(row['municipio']).strip() in ['', 'nan', 'NAN', 'None']:
                return False, "Municipio inválido"
            
            # Total de cartera debe ser mayor a 0
            if not row['total_cartera'] or row['total_cartera'] <= 0:
                return False, "Total cartera inválido o cero"
            
            return True, None

        # Crear DataFrame transformado
        df_transformado = pd.DataFrame()

        # Municipio - manejar valores faltantes
        df_transformado['municipio'] = df[COL_MUNICIPIO].apply(
            lambda x: str(x).strip() if pd.notna(x) and str(x).strip() not in ['', 'nan', 'NAN', 'None'] else None
        )

        # Cartera por categoría (limpiar valores monetarios)
        df_transformado['cartera_a'] = df[COL_CAT_A].apply(limpiar_moneda)
        df_transformado['cartera_b'] = df[COL_CAT_B].apply(limpiar_moneda)
        df_transformado['cartera_c'] = df[COL_CAT_C].apply(limpiar_moneda)
        df_transformado['cartera_d'] = df[COL_CAT_D].apply(limpiar_moneda)
        df_transformado['cartera_e'] = df[COL_CAT_E].apply(limpiar_moneda)

        # Total cartera - crítico, no puede ser cero o nulo
        df_transformado['total_cartera'] = df[COL_CARTERA_CREDITOS].apply(
            lambda x: limpiar_moneda(x, permitir_cero=False)
        )

        # Total captaciones (suma de todas las columnas de depósitos)
        cols_disp = [c for c in COLS_CAPTACIONES if c in df.columns]
        if cols_disp:
            # Sumar columnas de captaciones, reemplazando nulos con 0
            df_transformado['total_captaciones'] = df[cols_disp].apply(
                lambda row: sum(limpiar_moneda(row[c]) for c in cols_disp),
                axis=1
            )
        else:
            df_transformado['total_captaciones'] = None

        # ═══════════════════════════════════════════════════════════════════════════
        # FILTRAR FILAS INVÁLIDAS ANTES DE LIMPIEZA
        # ═══════════════════════════════════════════════════════════════════════════
        
        # Contar filas antes de filtrar
        filas_antes = len(df_transformado)
        
        # Aplicar validación de filas
        mask_validas = df_transformado.apply(
            lambda row: fila_valida(row)[0], axis=1
        )
        df_filtrado = df_transformado[mask_validas].copy()
        
        # Registrar filas filtradas
        filas_filtradas = filas_antes - len(df_filtrado)
        if filas_filtradas > 0:
            print(f"    Filas filtradas (datos incompletos): {filas_filtradas}")

        # ═══════════════════════════════════════════════════════════════════════════
        # LIMPIEZA DE DATOS (Semana 1)
        # ═══════════════════════════════════════════════════════════════════════════

        columnas_numericas = ['cartera_a', 'cartera_b', 'cartera_c',
                              'cartera_d', 'cartera_e', 'total_cartera',
                              'total_captaciones']

        # Imputar nulos en columnas de cartera con 0 (no tiene sentido usar mediana para ceros)
        for col in ['cartera_a', 'cartera_b', 'cartera_c', 'cartera_d', 'cartera_e']:
            if col in df_filtrado.columns:
                n_nulos = df_filtrado[col].isna().sum()
                if n_nulos > 0:
                    df_filtrado[col] = df_filtrado[col].fillna(0)
                    print(f"    {col}: {n_nulos} valores faltantes imputados con 0")
        
        # Imputar total_captaciones con 0 si es nulo
        if 'total_captaciones' in df_filtrado.columns:
            n_nulos = df_filtrado['total_captaciones'].isna().sum()
            if n_nulos > 0:
                df_filtrado['total_captaciones'] = df_filtrado['total_captaciones'].fillna(0)
                print(f"    total_captaciones: {n_nulos} valores faltantes imputados con 0")

        df_limpio = eliminar_duplicados(df_filtrado, subset=['municipio'])
        
        # Solo detectar outliers, no reasignar (la funcion retorna un Series, no un DataFrame)
        detectar_outliers_iqr(df_limpio, 'total_cartera')

        # Resetear índice para evitar problemas con índices originales
        df_limpio = df_limpio.reset_index(drop=True)

        # ═══════════════════════════════════════════════════════════════════════════
        # PROCESAMIENTO
        # ═══════════════════════════════════════════════════════════════════════════

        results = []
        errores = []

        for idx, row in df_limpio.iterrows():
            try:
                # Saltar filas con municipio inválido
                municipio_str = str(row['municipio']).strip()
                if not municipio_str or municipio_str == 'nan':
                    continue

                # Saltar filas con total_cartera <= 0
                total_cartera_val = float(row['total_cartera']) if row['total_cartera'] else 0.0
                if total_cartera_val <= 0:
                    continue

                # Preparar datos para validación Pydantic
                data_dict = {
                    'municipio': municipio_str.title(),
                    'cartera_a': float(row['cartera_a']) if row['cartera_a'] and float(row['cartera_a']) > 0 else 0.0,
                    'cartera_b': float(row['cartera_b']) if row['cartera_b'] and float(row['cartera_b']) > 0 else 0.0,
                    'cartera_c': float(row['cartera_c']) if row['cartera_c'] and float(row['cartera_c']) > 0 else 0.0,
                    'cartera_d': float(row['cartera_d']) if row['cartera_d'] and float(row['cartera_d']) > 0 else 0.0,
                    'cartera_e': float(row['cartera_e']) if row['cartera_e'] and float(row['cartera_e']) > 0 else 0.0,
                    'total_cartera': total_cartera_val,
                    'total_captaciones': float(row['total_captaciones']) if row['total_captaciones'] and float(row['total_captaciones']) > 0 else None,
                }

                # Validar con Pydantic
                input_data = RiesgoCrediticioInput(**data_dict)
                
                # Obtener NPLs históricos para cálculo estadístico
                historical_npls = [a["resultados"]["indice_riesgo"] for a in historial_analisis.values()]
                
                # Procesar
                res = procesar_riesgo_crediticio(input_data.model_dump(), historical_npls)

                # Guardar en historial
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
                errores.append({
                    "fila": int(idx),
                    "municipio": str(row.get('municipio', 'Desconocido')),
                    "error": str(e)
                })
                continue

        # ═══════════════════════════════════════════════════════════════════════════
        # RESUMEN
        # ═══════════════════════════════════════════════════════════════════════════

        return {
            "mensaje": f"✅ Se procesaron {len(results)} municipios correctamente",
            "ids_creados": results,
            "total_filas": len(df_limpio),
            "errores": len(errores),
            "detalle_errores": errores[:5] if errores else None,  # Mostrar primeros 5 errores
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error completo:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el archivo: {str(e)}"
        )


@app.get(
    "/datos-gov/info",
    tags=["Datos.gov.co"],
    summary="Información del archivo Datos.gov.co",
)
async def info_datos_gov():
    """
    **Muestra información sobre el formato esperado del archivo CSV**

    El archivo debe ser: `Saldo_de_las_captaciones_y_colocaciones_por_municipios_*.csv`

    Columnas requeridas:
      - Nombre del municipio
      - Cartera de créditos
      - Categoría A riesgo normal
      - Categoría B riesgo aceptable
      - Categoría C riesgo apreciable
      - Categoría D riesgo significativo
      - Categoría E riesgo de Incobrabilidad

    Columnas opcionales (para captaciones):
      - Depósitos en cuenta corriente bancaria
      - Depósitos simples
      - Certificados de depósito a término
      - Depósitos de ahorro
      - etc.
    """
    return {
        "fuente": "Datos.gov.co - Sistema Financiero Colombiano",
        "archivo_esperado": "Saldo_de_las_captaciones_y_colocaciones_por_municipios_*.csv",
        "columnas_requeridas": [
            "Nombre del municipio",
            "Cartera de créditos",
            "Categoría A riesgo normal",
            "Categoría B riesgo aceptable",
            "Categoría C riesgo apreciable",
            "Categoría D riesgo significativo",
            "Categoría E riesgo de Incobrabilidad",
        ],
        "columnas_captaciones": [
            "Depósitos en cuenta corriente bancaria",
            "Depósitos simples",
            "Certificados de depósito a término",
            "Depósitos de ahorro",
        ],
        "endpoint_carga": "/datos-gov/cargar",
        "metodo": "POST",
        "ejemplo_uso": "curl -X POST -F 'file=@archivo.csv' http://127.0.0.1:8000/datos-gov/cargar",
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
