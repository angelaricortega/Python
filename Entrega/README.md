# 🏦 API de Análisis de Riesgo Crediticio

### Sistema Financiero Colombiano — Datos Abiertos Gov.co

**Autores:** Angela Rico · Sebastian Ramirez  
**Curso:** Python para APIs e IA Aplicada  
**Universidad:** Universidad Santo Tomás · 2026  
**Versión:** 1.0.0

---

## 📋 Tabla de Contenidos

1. [Descripción del Proyecto](#-descripción-del-proyecto)
2. [Dominio de Aplicación](#-dominio-de-aplicación)
3. [Estructura de Archivos](#-estructura-de-archivos)
4. [Conceptos del Curso Aplicados](#-conceptos-del-curso-aplicados)
5. [Instalación Paso a Paso](#-instalación-paso-a-paso)
6. [Ejecución de la API](#-ejecución-de-la-api)
7. [Explicación Detallada del Código](#-explicación-detallada-del-código)
8. [Funcionamiento de la API](#-funcionamiento-de-la-api)
9. [Funcionamiento de la Interfaz Web](#-funcionamiento-de-la-interfaz-web)
10. [Endpoints Disponibles](#-endpoints-disponibles)
11. [Ejemplos de Uso](#-ejemplos-de-uso)
12. [Preguntas Frecuentes](#-preguntas-frecuentes)

---

## 🎯 Descripción del Proyecto

Este proyecto es una **API REST completa** construida con **FastAPI** que permite registrar y analizar municipios del sistema financiero colombiano, calculando automáticamente indicadores de riesgo crediticio basados en la clasificación regulatoria de cartera (Categorías A-E).

### ¿Qué Hace Este Sistema?

1. **Recibe datos** de cartera bancaria de municipios colombianos
2. **Valida automáticamente** que los datos sean coherentes (no negativos, totales positivos)
3. **Calcula 12+ indicadores** estadísticos usando NumPy
4. **Clasifica el nivel de riesgo** usando Pattern Matching
5. **Almacena el historial** de análisis en memoria
6. **Sirve una interfaz web** interactiva con diseño rosadito 🌸
7. **Genera documentación automática** en Swagger UI

### Características Principales

| Característica | Descripción |
|----------------|-------------|
| **Validación Pydantic** | Rechaza datos inválidos antes de procesar |
| **Cálculos NumPy** | 12+ indicadores estadísticos calculados |
| **Pattern Matching** | Clasificación de riesgo con `match/case` |
| **CRUD Completo** | Crear, Leer, Eliminar análisis |
| **Interfaz Web** | UI educativa con Chart.js |
| **Swagger UI** | Documentación automática en `/docs` |
| **Carga Masiva** | Soporta CSV y Excel |

---

## 🏛️ Dominio de Aplicación

### Contexto Financiero

La **Superfinanciera de Colombia** regula el sistema financiero y clasifica la cartera de créditos en 5 categorías según el riesgo de no pago:

| Categoría | Nombre | Descripción | Días de Mora |
|-----------|--------|-------------|--------------|
| **A** | Normal | Cartera sana, sin observaciones | 0 |
| **B** | Observación | Alerta temprana, revisar | 0 |
| **C** | Subestándar | Deterioro inicial | 1-30 |
| **D** | Dudosa | Deterioro significativo | 31-90 |
| **E** | Pérdida | Incobrable, castigar | >90 |

### Fórmulas Clave

#### Índice NPL (Non-Performing Loans)

Mide el porcentaje de cartera en mora respecto al total:

```
        C + D + E
NPL = ───────────
       Total Cartera
```

**Interpretación:**
- NPL = 0.03 → 3% de la cartera está en mora
- NPL = 0.15 → 15% de la cartera está en mora (crítico)

#### Índice HHI (Herfindahl-Hirschman Index)

Mide la concentración de la cartera:

```
        ∑ (cartera_i)²
HHI = ────────────────
      (Total Cartera)²
```

**Interpretación:**
- HHI < 0.15 → Baja concentración (bien diversificado)
- HHI > 0.25 → Alta concentración (riesgo por falta de diversificación)

### Umbrales de Riesgo

| NPL Ratio | Nivel | Color | Acción Requerida |
|-----------|-------|-------|------------------|
| 0% | Sin Riesgo | 🟢 Verde | Ninguna |
| <1% | Riesgo Bajo | 🟢 Verde | Monitoreo routine |
| <5% | Riesgo Moderado | 🟡 Amarillo | Alerta temprana, revisar |
| <15% | Riesgo Alto | 🟠 Naranja | Deterioro, acción requerida |
| ≥15% | Riesgo Crítico | 🔴 Rojo | Crítico, intervención inmediata |

---

## 📁 Estructura de Archivos

### Directorio Principal (`Entrega/`)

```
Entrega/
├── main.py                      # ⭐ API FastAPI completa (760 líneas)
├── modelos.py                   # ⭐ Modelos Pydantic + Clases OOP (884 líneas)
├── decorators.py                # ⭐ Decoradores estadísticos (527 líneas)
├── config.py                    # ⭐ Configuración global (225 líneas)
├── limpieza.py                  # ⭐ Funciones puras de limpieza (Semana 1) [NUEVO]
├── start.py                     # 🚀 Script de inicio rápido
├── verificar_instalacion.py     # 🔍 Verificador de instalación
├── README.md                    # 📖 Este archivo
├── requirements.txt             # 📦 Dependencias de Python
├── .gitignore                   # 🚫 Archivos ignorados por Git
│
└── static/
    ├── index.html               # 🌸 Interfaz web (600 líneas)
    ├── style.css                # 🎨 Estilos pastel (1246 líneas)
    └── app.js                   # ⚡ Interactividad (748 líneas)
```

### Descripción de Cada Archivo

| Archivo | Líneas | Propósito | Conceptos Aplicados |
|---------|--------|-----------|---------------------|
| `main.py` | 760 | API FastAPI con 7 endpoints | Semana 1, 2, 3 |
| `modelos.py` | 884 | Pydantic + OOP Herencia | Semana 2 |
| `decorators.py` | 527 | Decoradores simples y factory | Semana 1 |
| `config.py` | 225 | Configuración centralizada | Semana 1, 6 |
| `limpieza.py` | ~200 | **Funciones puras de limpieza** | **Semana 1** ⭐ |
| `index.html` | 600 | Estructura HTML de la UI | Semana 3 |
| `style.css` | 1246 | Estilos rosaditos pastel | Semana 3 |
| `app.js` | 748 | Lógica de interactividad | Semana 3 |
| `start.py` | ~50 | Inicia API y abre navegador | Utilidad |
| `verificar_instalacion.py` | ~40 | Verifica dependencias | Utilidad |

---

## 🎓 Conceptos del Curso Aplicados

### Semana 1: Fundamentos de Python

#### 1. Pattern Matching (`match/case`)

**Ubicación:** `main.py` — función `clasificar_nivel_riesgo()`

**Código:**
```python
def clasificar_nivel_riesgo(indice_mora: float) -> Literal[
    "sin_riesgo", "riesgo_bajo", "riesgo_moderado", 
    "riesgo_alto", "riesgo_critico"
]:
    """Clasifica el riesgo según el índice de mora."""
    match indice_mora:
        case 0.0:
            return "sin_riesgo"
        case x if x < 0.01:
            return "riesgo_bajo"
        case x if x < 0.05:
            return "riesgo_moderado"
        case x if x < 0.15:
            return "riesgo_alto"
        case _:
            return "riesgo_critico"
```

**Explicación:**
- `match indice_mora:` → Evalúa el valor de `indice_mora`
- `case 0.0:` → Si es exactamente 0, retorna "sin_riesgo"
- `case x if x < 0.01:` → Si es menor a 0.01, retorna "riesgo_bajo"
- `case _:` → Caso por defecto (cualquier otro valor)

**Ventaja sobre `if/elif`:** Más legible y estructurado.

---

#### 2. Decoradores Simples

**Ubicación:** `decorators.py` — `@registrar_ejecucion`

**Código:**
```python
import functools
import time

def registrar_ejecucion(func: Callable) -> Callable:
    """
    Decorador que registra tiempo de ejecución.
    
    APLICA: Principio Open/Closed (extender sin modificar)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fin = time.time()
        print(f"{func.__name__} ejecutó en {fin-inicio:.4f}s")
        return resultado
    return wrapper

# Uso en main.py
@registrar_ejecucion
def procesar_riesgo_crediticio(datos: dict) -> dict:
    """Función pura que calcula indicadores."""
    # ... código ...
```

**Explicación:**
1. `@registrar_ejecucion` se coloca encima de una función
2. Antes de ejecutar, guarda el tiempo de inicio
3. Ejecuta la función original
4. Guarda el tiempo de fin y calcula la diferencia
5. Imprime el tiempo de ejecución

**`@functools.wraps`:** Preserva el nombre y docstring original de la función.

---

#### 3. Decoradores Factory (Decoradores con Parámetros)

**Ubicación:** `decorators.py` — `@validar_normalidad(alpha=0.05)`

**Código:**
```python
def validar_normalidad(alpha: float = 0.05):
    """
    Decorador factory que valida normalidad antes de ejecutar.
    
    PARÁMETRO: alpha = nivel de significancia (default 0.05)
    """
    def decorador(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = _extraer_data(args, kwargs)
            if data is not None:
                _, p_valor = stats.normaltest(data)
                if p_valor < alpha:
                    raise ValueError(
                        f"Datos no normales (p={p_valor:.4f} < {alpha})"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorador
```

**Explicación:**
- Es un **decorador de decoradores** (factory)
- `validar_normalidad(alpha=0.05)` → Retorna el decorador
- El decorador retornado → Retorna el wrapper
- El wrapper → Ejecuta la validación y luego la función

**Uso:**
```python
@validar_normalidad(alpha=0.01)
def calcular_media(data: list) -> float:
    return sum(data) / len(data)
```

---

#### 4. Type Hints (`Literal`, `Optional`, `List`)

**Ubicación:** Todo el código

**Código:**
```python
from typing import List, Optional, Literal

# Literal: restringe a valores específicos
NivelRiesgo = Literal[
    "sin_riesgo",
    "riesgo_bajo",
    "riesgo_moderado",
    "riesgo_alto",
    "riesgo_critico",
]

# Optional: puede ser None
def buscar_municipio(
    id: int,
    historial: Optional[dict] = None
) -> Optional[dict]:
    """Busca municipio por ID."""
    pass

# List: lista de un tipo específico
def analizar_lote(
    municipios: List[dict]
) -> List[dict]:
    """Analiza múltiples municipios."""
    pass
```

**Beneficios:**
1. **Documentación automática:** Sabes qué tipo espera cada función
2. **Detección temprana de errores:** Type checkers (mypy) avisan antes de ejecutar
3. **Mejor autocompletado:** Los IDEs sugieren métodos correctos

---

#### 5. Configuración Centralizada

**Ubicación:** `config.py`

**Código:**
```python
from pathlib import Path

# Rutas absolutas cross-platform
BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

# API de Datos Abiertos
API_BASE = "https://www.datos.gov.co/resource/3kqn-n4za.json"
HTTP_TIMEOUT = 15

# Paleta de colores "Rosadito Bonito"
PALETA = {
    "rosa_claro": "#FFF0F5",
    "rosa_pastel": "#FFB6C1",
    "rosa_medio": "#FF69B4",
    "rosa_fuerte": "#DB7093",
    "rosa_oscuro": "#8B0A50",
    "verde": "#28A745",
    "amarillo": "#FFC107",
    "rojo": "#DC3545",
}

# Estilos de gráficas
PLT_STYLE = {
    "font.family": "sans-serif",
    "font.size": 10,
    "figure.figsize": (10, 6),
}
```

**Ventaja:** Cambias un valor aquí y se actualiza en TODO el proyecto.

---

#### 6. Módulo de Limpieza — Funciones Puras (Semana 1)

**Ubicación:** `limpieza.py` — Módulo reutilizable de limpieza de datos

**CONCEPTO APLICADO — Modularización (Semana 1):**
> Separar la limpieza de datos en un módulo reutilizable permite:
> 1. Reutilizar las mismas funciones en múltiples análisis
> 2. Testear independientemente la lógica de limpieza
> 3. Mantener el código de análisis principal limpio y legible
> 4. Documentar claramente cada paso del pipeline de limpieza

**Código:**
```python
# limpieza.py — Funciones puras para limpieza de DataFrames
from typing import List, Optional
import pandas as pd
import numpy as np

def eliminar_duplicados(
    df: pd.DataFrame,
    subset: Optional[List[str]] = None,
    mantener: str = 'first'
) -> pd.DataFrame:
    """
    Elimina filas duplicadas del DataFrame.
    
    FUNCIÓN PURA:
      - Recibe DataFrame, retorna DataFrame limpio
      - No modifica el original
      - Sin efectos secundarios
    """
    n_antes = len(df)
    df_limpio = df.drop_duplicates(subset=subset, keep=mantener)
    n_duplicados = n_antes - len(df_limpio)
    print(f"✅ Eliminados {n_duplicados} duplicados")
    return df_limpio

def imputar_nulos(
    df: pd.DataFrame,
    columnas: List[str],
    estrategia: str = 'mediana'
) -> pd.DataFrame:
    """
    Imputa valores nulos con la estrategia especificada.
    
    ESTRATEGIAS:
      - 'media': Media aritmética
      - 'mediana': Mediana (robusta a outliers) ← RECOMENDADA
      - 'moda': Valor más frecuente
      - 'cero': Rellena con 0
    """
    df_limpio = df.copy()  # Copia para mantener pureza
    for col in columnas:
        n_nulos = df_limpio[col].isna().sum()
        if estrategia == 'mediana':
            valor = df_limpio[col].median()
        df_limpio[col] = df_limpio[col].fillna(valor)
        print(f"✅ {col}: {n_nulos} nulos imputados")
    return df_limpio

def detectar_outliers_iqr(
    df: pd.DataFrame,
    columna: str,
    factor: float = 1.5
) -> pd.Series:
    """
    Detecta outliers usando el método IQR.
    
    MÉTODO:
      1. Calcular Q1 (25to percentil) y Q3 (75to percentil)
      2. IQR = Q3 - Q1
      3. Límite inf = Q1 - factor × IQR
      4. Límite sup = Q3 + factor × IQR
      5. Outlier = valor fuera de límites
    """
    Q1 = df[columna].quantile(0.25)
    Q3 = df[columna].quantile(0.75)
    IQR = Q3 - Q1
    outliers = (df[columna] < Q1 - factor * IQR) | (df[columna] > Q3 + factor * IQR)
    print(f"⚠️ {columna}: {outliers.sum()} outliers detectados")
    return outliers

def limpieza_completa(
    df: pd.DataFrame,
    columnas_numericas: List[str],
    columna_municipio: str = 'municipio'
) -> pd.DataFrame:
    """
    Aplica pipeline completo de limpieza.
    
    PIPELINE:
      1. Eliminar duplicados
      2. Imputar nulos
      3. Detectar outliers (reporte)
    """
    df_limpio = eliminar_duplicados(df, subset=[columna_municipio])
    df_limpio = imputar_nulos(df_limpio, columnas=columnas_numericas)
    for col in columnas_numericas:
        if col in df_limpio.columns:
            detectar_outliers_iqr(df_limpio, col)
    return df_limpio
```

**Uso en el endpoint `/upload` (main.py):**
```python
from limpieza import limpieza_completa

@app.post("/upload")
async def cargar_archivo(file: UploadFile = File(...)):
    # Leer archivo
    df = pd.read_csv(io.BytesIO(await file.read()))
    
    # Aplicar limpieza (Semana 1)
    df_limpio = limpieza_completa(
        df,
        columnas_numericas=['cartera_a', 'cartera_b', 'total_cartera'],
        columna_municipio='municipio'
    )
    
    # Procesar datos limpios...
```

**Ventajas de esta implementación:**
1. **Funciones puras:** Mismos inputs → mismos outputs, sin efectos secundarios
2. **Modularización:** Un solo archivo con toda la lógica de limpieza
3. **Reutilizable:** Se puede importar en cualquier script
4. **Testeable:** Cada función se puede probar independientemente
5. **Documentado:** Docstrings explican qué hace cada función

---

### Semana 2: Pydantic y Programación Orientada a Objetos

#### 1. Pydantic — Validación de Datos

**Ubicación:** `modelos.py` — `RiesgoCrediticioInput`

**Código:**
```python
from pydantic import BaseModel, Field, field_validator

class RiesgoCrediticioInput(BaseModel):
    """Modelo de entrada para análisis de riesgo crediticio."""
    
    municipio: str = Field(
        ...,                    # Obligatorio
        min_length=2,           # Mínimo 2 caracteres
        max_length=60,          # Máximo 60 caracteres
        description="Nombre del municipio",
        example="Bogotá D.C.",
    )
    
    cartera_a: float = Field(
        ...,                    # Obligatorio
        ge=0,                   # Greater or Equal to 0
        description="Cartera categoría A (≥ 0)",
        example=1500000000.0,
    )
    
    total_cartera: float = Field(
        ...,
        gt=0,                   # Greater Than 0 (CRÍTICO)
        description="Total de cartera (> 0)",
        example=1800000000.0,
    )
    
    total_captaciones: Optional[float] = Field(
        default=None,           # Opcional
        ge=0,
        description="Captaciones (opcional)",
    )
    
    @field_validator("municipio", mode="before")
    @classmethod
    def normalizar_municipio(cls, v: str) -> str:
        """Limpia nombre: '  BOGOTÁ  ' → 'Bogotá'."""
        return str(v).strip().title() if v else ""
```

**Validaciones Explicadas:**

| Validación | Significado | Ejemplo de Error |
|------------|-------------|------------------|
| `...` | Obligatorio | Si falta → `ValidationError` |
| `min_length=2` | Mínimo 2 caracteres | `"X"` → Error |
| `max_length=60` | Máximo 60 caracteres | String de 61 → Error |
| `ge=0` | Greater or Equal (≥ 0) | `-100` → Error |
| `gt=0` | Greater Than (> 0) | `0` → Error (evita división por cero) |
| `default=None` | Valor por defecto | Si falta → `None` |
| `@field_validator` | Validación personalizada | Limpia el string |

**¿Por qué es importante?**

Sin Pydantic, este request crashearía la API:
```json
{"total_cartera": 0}  # → ZeroDivisionError
```

Con Pydantic, es rechazado inmediatamente:
```json
HTTP 422 Unprocessable Entity
{
  "detail": [{
    "loc": ["body", "total_cartera"],
    "msg": "ensure this value is greater than 0",
    "type": "value_error.number.not_gt"
  }]
}
```

---

#### 2. OOP — Herencia y Polimorfismo

**Ubicación:** `modelos.py`

**Código:**
```python
class AnalizadorEstadistico:
    """Clase base para análisis estadístico."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._nombre = "Analizador Base"
    
    def calcular_varianza(self, columna: str) -> float:
        """Varianza POBLACIONAL (ddof=0)."""
        return self.df[columna].var(ddof=0)
    
    def calcular_media(self, columna: str) -> float:
        """Media aritmética."""
        return self.df[columna].mean()


class AnalizadorMuestral(AnalizadorEstadistico):
    """
    Subclase que usa corrección de Bessel (ddof=1).
    
    HERENCIA: Hereda todos los métodos de AnalizadorEstadistico
    POLIMORFISMO: Sobrescribe calcular_varianza()
    """
    
    def __init__(self, df: pd.DataFrame):
        super().__init__(df)  # Llama al constructor padre
        self._nombre = "Analizador Muestral"
    
    def calcular_varianza(self, columna: str) -> float:
        """
        SOBRESCRIBE: Varianza MUESTRAL (ddof=1).
        
        ddof=1 corrige el sesgo en muestras pequeñas.
        """
        return self.df[columna].var(ddof=1)
    
    def calcular_hhi(self) -> float:
        """Índice HHI de concentración."""
        concentraciones = (self.df["cartera"] / self.df["cartera"].sum()) ** 2
        return concentraciones.sum()
```

**Explicación:**

**Herencia:**
```python
analizador = AnalizadorMuestral(df)
analizador.calcular_media("cartera")  # Método heredado del padre
```

**Polimorfismo:**
```python
# Mismo método, comportamiento diferente
analizador_base = AnalizadorEstadistico(df)
analizador_muestral = AnalizadorMuestral(df)

analizador_base.calcular_varianza("cartera")    # ddof=0
analizador_muestral.calcular_varianza("cartera") # ddof=1
```

---

#### 3. Funciones Puras

**Ubicación:** `main.py` — `procesar_riesgo_crediticio()`

**Código:**
```python
def procesar_riesgo_crediticio(datos: dict) -> dict:
    """
    Función PURA que procesa datos de riesgo crediticio.
    
    PROPIEDADES DE FUNCIÓN PURA:
    1. Mismos inputs → mismos outputs (determinística)
    2. Sin efectos secundarios (no modifica estado externo)
    3. Sin I/O (no lee/escribe archivos, BD, red)
    """
    # Convertir a array NumPy
    cartera = np.array([
        datos["cartera_a"],
        datos["cartera_b"],
        datos["cartera_c"],
        datos["cartera_d"],
        datos["cartera_e"],
    ])
    
    # Cálculos
    cartera_mora = cartera[2:].sum()  # C + D + E
    indice_riesgo = cartera_mora / datos["total_cartera"]
    pct_sana = (cartera[:2].sum() / datos["total_cartera"]) * 100
    
    # HHI
    pesos = cartera / datos["total_cartera"]
    hhi = (pesos ** 2).sum()
    
    return {
        "indice_riesgo": indice_riesgo,
        "pct_cartera_sana": pct_sana,
        "pct_cartera_mora": 100 - pct_sana,
        "hhi": hhi,
        # ... más campos
    }
```

**¿Por qué es importante?**

1. **Testeable:** Puedes probarla con tests unitarios
2. **Reproducible:** Mismos datos → mismos resultados
3. **Sin dependencias:** No necesita BD, archivos, red
4. **Thread-safe:** Múltiples hilos pueden ejecutarla sin conflicto

---

### Semana 3: FastAPI y Desarrollo Web

#### 1. FastAPI — Decoradores de Rutas

**Ubicación:** `main.py`

**Código:**
```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI(
    title="API de Riesgo Crediticio",
    description="Análisis de cartera bancaria del sistema financiero colombiano",
    version="1.0.0",
)

@app.get("/", tags=["General"])
async def root():
    """Endpoint de salud y documentación."""
    return {
        "mensaje": "API de Riesgo Crediticio",
        "documentacion": "/docs",
    }

@app.post("/analizar", status_code=status.HTTP_201_CREATED, tags=["Análisis"])
async def analizar_riesgo(datos: RiesgoCrediticioInput):
    """Registra nuevo municipio y calcula indicadores."""
    # ... código ...
```

**Explicación:**

| Decorador | Método HTTP | Ruta | Descripción |
|-----------|-------------|------|-------------|
| `@app.get("/")` | GET | `/` | Health check |
| `@app.post("/analizar")` | POST | `/analizar` | Crear análisis |
| `@app.get("/historial")` | GET | `/historial` | Listar análisis |
| `@app.get("/historial/{id}")` | GET | `/historial/{id}` | Obtener por ID |
| `@app.delete("/historial/{id}")` | DELETE | `/historial/{id}` | Eliminar análisis |

**`async def`:** Función asíncrona (non-blocking).

---

#### 2. CRUD Completo

**POST — Crear:**
```python
@app.post("/analizar", status_code=201)
async def analizar_riesgo(datos: RiesgoCrediticioInput):
    """
    1. Pydantic valida el request body
    2. Función pura calcula indicadores
    3. Guarda en historial en memoria
    4. Retorna HTTP 201 Created
    """
    global contador_id, historial_analisis
    
    # Calcular indicadores (función pura)
    resultados = procesar_riesgo_crediticio(datos.model_dump())
    
    # Incrementar ID
    contador_id += 1
    
    # Guardar en historial
    registro = {
        "id": contador_id,
        "municipio": datos.municipio,
        "request": datos.model_dump(),
        "resultados": resultados,
        "fecha_analisis": datetime.now(),
    }
    historial_analisis[contador_id] = registro
    
    # Retornar con status 201
    return {**registro, "resultados": resultados}
```

**GET — Listar:**
```python
@app.get("/historial")
async def listar_historial():
    """Retorna todos los análisis registrados."""
    return {
        "total_registros": len(historial_analisis),
        "fecha_consulta": datetime.now().isoformat(),
        "analisis": list(historial_analisis.values()),
    }
```

**GET por ID — Obtener:**
```python
@app.get("/historial/{analisis_id}")
async def obtener_analisis(analisis_id: int):
    """Obtiene un análisis específico por ID."""
    if analisis_id not in historial_analisis:
        raise HTTPException(
            status_code=404,
            detail=f"Análisis {analisis_id} no encontrado"
        )
    return historial_analisis[analisis_id]
```

**DELETE — Eliminar:**
```python
@app.delete("/historial/{analisis_id}")
async def eliminar_analisis(analisis_id: int):
    """Elimina un análisis del historial."""
    if analisis_id not in historial_analisis:
        raise HTTPException(status_code=404, detail="No encontrado")
    
    del historial_analisis[analisis_id]
    return {
        "mensaje": f"Análisis {analisis_id} eliminado",
        "restantes": len(historial_analisis),
    }
```

---

#### 3. Async/Await (Asincronía)

**¿Por qué `async def`?**

```python
# SÍNCRONO (blocking)
@app.get("/lento")
def endpoint_lento():
    time.sleep(5)  # Bloquea el servidor por 5 segundos
    return {"listo": True}

# ASÍNCRONO (non-blocking)
@app.get("/lento")
async def endpoint_lento():
    await asyncio.sleep(5)  # Libera el servidor mientras espera
    return {"listo": True}
```

**Ventaja:** Mientras un request espera I/O (BD, red), el servidor atiende otros requests.

---

#### 4. Swagger UI — Documentación Automática

**URL:** `http://127.0.0.1:8000/docs`

FastAPI genera automáticamente:
- Lista de todos los endpoints
- Schema de request/response
- Botón "Try it out" para probar
- Modelos Pydantic como schemas

**Ejemplo de lo que ves en Swagger:**

```
POST /analizar
─────────────
Request Body:
{
  "municipio": "Bogotá D.C.",
  "cartera_a": 1500000000.0,
  "cartera_b": 200000000.0,
  "cartera_c": 50000000.0,
  "cartera_d": 25000000.0,
  "cartera_e": 10000000.0,
  "total_cartera": 1785000000.0,
  "total_captaciones": 2000000000.0
}

Response 201:
{
  "id": 1,
  "municipio": "Bogotá D.C.",
  "indice_riesgo": 0.0476,
  "nivel_riesgo": "riesgo_moderado",
  "pct_cartera_sana": 95.24,
  "hhi": 0.7234
}
```

---

#### 5. pydantic-settings — Configuración desde Variables de Entorno (Semana 6)

**Ubicación:** `config.py` — clase `Settings`

**Código:**
```python
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    """
    Configuración de la API cargada desde variables de entorno.
    
    SEMANA 6 — Inyección de Dependencias:
    Esta clase se usa como dependencia global en FastAPI para
    inyectar configuración validada en todos los endpoints.
    """
    
    # API de Datos Abiertos
    api_base: str = Field(
        default="https://www.datos.gov.co/resource/3kqn-n4za.json",
        description="Endpoint Socrata de Datos Abiertos",
    )
    
    # Servidor
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, ge=1, le=65535)
    
    # Logging
    log_level: str = Field(default="info")
    
    # Entorno
    environment: str = Field(default="development")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valida que el nivel de logging sea válido."""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in valid_levels:
            raise ValueError(f"log_level debe ser uno de: {valid_levels}")
        return v.lower()
    
    # Carga desde .env
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

# Instancia global
settings = Settings()
```

**¿Por qué pydantic-settings en vez de `os.getenv()`?**

| Característica | `os.getenv()` | `pydantic-settings` |
|----------------|---------------|---------------------|
| Validación de tipos | ❌ Manual (`int(os.getenv("PORT"))`) | ✅ Automática (`port: int`) |
| Valores por defecto | ❌ `os.getenv("PORT", "8000")` | ✅ `Field(default=8000)` |
| Error si falta variable | ❌ Retorna `None` | ✅ Excepción clara |
| Validación personalizada | ❌ Manual | ✅ `@field_validator` |
| Documentación | ❌ Comentarios | ✅ `description="..."` |
| Autocompletado IDE | ❌ Strings | ✅ Type hints |

**Uso en la API:**
```python
from config import settings

@app.get("/")
async def root():
    return {
        "api_base": settings.api_base,
        "environment": settings.environment,
    }
```

**Archivo `.env` (ejemplo):**
```env
# Servidor
HOST=127.0.0.1
PORT=8000

# Logging
LOG_LEVEL=info

# Entorno
ENVIRONMENT=development

# API Externa
API_BASE=https://www.datos.gov.co/resource/3kqn-n4za.json
```

---

## 📦 Instalación Paso a Paso

### Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)
- Navegador web (Chrome, Firefox, Edge)

### Paso 1: Verificar Python

```bash
python --version
```

Debe mostrar: `Python 3.11.x` o superior.

### Paso 2: Navegar al Directorio

```bash
cd "c:\Users\Angela Rico\Documents\001 Python\Python"
```

### Paso 3: Crear Entorno Virtual

```bash
python -m venv venv
```

**¿Qué hace?** Crea una carpeta `venv/` con Python aislado.

### Paso 4: Activar Entorno Virtual

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Verificación:** Deberías ver `(venv)` al inicio del prompt.

### Paso 5: Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Dependencias instaladas:**
- `fastapi` — Framework web
- `uvicorn` — Servidor ASGI
- `pydantic` — Validación de datos
- `numpy` — Cálculos numéricos
- `pandas` — Manipulación de datos
- `python-multipart` — Soporte para uploads

### Paso 6: Verificar Instalación

```bash
cd Entrega
python verificar_instalacion.py
```

**Salida esperada:**
```
✅ FastAPI         v0.115.0
✅ Uvicorn         v0.30.6
✅ Pydantic        v2.7.4
✅ NumPy           v1.26.4
✅ Pandas          v2.2.2

✨ Verificación completada
```

---

## 🚀 Ejecución de la API

### Método 1: Script de Inicio (Recomendado)

```bash
cd Entrega
python start.py
```

**¿Qué hace?**
1. Inicia el servidor uvicorn
2. Espera 3 segundos
3. Abre automáticamente el navegador en la interfaz web

### Método 2: Uvicorn Directo

```bash
cd Entrega
uvicorn main:app --reload
```

**Opciones:**
- `--reload` → Reinicia automáticamente al cambiar código
- `--host 0.0.0.0` → Escucha en todas las interfaces
- `--port 8080` → Usa otro puerto (default: 8000)

### Método 3: Python Directo

```bash
cd Entrega
python main.py
```

**¿Qué hace?** Ejecuta el bloque `if __name__ == "__main__":` al final de `main.py`.

---

## 📡 Funcionamiento de la API

### Flujo Completo de un Request

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CLIENTE ENVÍA REQUEST HTTP                                   │
│    POST http://127.0.0.1:8000/analizar                          │
│    Content-Type: application/json                               │
│    Body: {"municipio": "Bogotá", "cartera_a": 1500000, ...}     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. UVICORN (Servidor ASGI) recibe la petición                   │
│    - Parsea headers y body                                      │
│    - Identifica ruta: POST /analizar                            │
│    - Busca el handler registrado                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. FASTAPI invoca el decorador @app.post()                      │
│    - Prepara el contexto de ejecución                           │
│    - Inyecta dependencias (request body)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. PYDANTIC valida el request body                              │
│    RiesgoCrediticioInput.model_validate(request_body)           │
│                                                                 │
│    a) Verifica tipos: str, float, Optional[float]               │
│    b) Ejecuta validaciones Field():                             │
│       - min_length=2, max_length=60 (municipio)                 │
│       - ge=0 (carteras no negativas)                            │
│       - gt=0 (total_cartera > 0)                                │
│    c) Ejecuta @field_validator: normalizar_municipio()          │
│    d) Si falla → HTTP 422 con errores detallados                │
│    e) Si pasa → instancia RiesgoCrediticioInput creada          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. FUNCIÓN analizar_riesgo() ejecuta la lógica                  │
│                                                                 │
│    a) Incrementa contador_id global                             │
│    b) Llama a función PURA:                                     │
│       procesar_riesgo_crediticio(datos.model_dump())            │
│       - Convierte a array numpy                                 │
│       - Calcula 12 estadísticos                                 │
│       - Clasifica nivel de riesgo (Pattern Matching)            │
│       - Retorna dict con resultados                             │
│    c) Guarda en historial_analisis[contador_id]                 │
│    d) Construye respuesta                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. PYDANTIC serializa la respuesta                              │
│    RiesgoCrediticioOutput.model_dump()                          │
│    - Convierte datetime a ISO 8601                              │
│    - Valida schema de salida                                    │
│    - Genera JSON                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. FASTAPI construye respuesta HTTP                             │
│    Status Code: 201 Created                                     │
│    Content-Type: application/json                               │
│    Body: {                                                      │
│      "id": 1,                                                   │
│      "municipio": "Bogotá D.C.",                                │
│      "indice_riesgo": 0.0476,                                   │
│      "nivel_riesgo": "riesgo_moderado",                         │
│      ...                                                        │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. UVICORN envía respuesta al cliente                           │
│    HTTP/1.1 201 Created                                         │
│    Content-Type: application/json                               │
│    Content-Length: 342                                          │
│    {...body...}                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. CLIENTE recibe respuesta                                     │
│    - Parsea JSON                                                │
│    - Extrae indice_riesgo, nivel_riesgo                         │
│    - Muestra al usuario o almacena                              │
└─────────────────────────────────────────────────────────────────┘
```

**Tiempo total:** ~5-15ms para requests válidos

---

## 🌸 Funcionamiento de la Interfaz Web

### Estructura HTML (`index.html`)

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>🏦 Análisis de Riesgo Crediticio</title>
    <link rel="stylesheet" href="/static/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
</head>
<body>
    <!-- Navegación -->
    <nav class="navbar">...</nav>

    <!-- Hero Section -->
    <section id="inicio" class="hero">...</section>

    <!-- ¿Qué es NPL? -->
    <section id="que-es-npl" class="educational-section">...</section>

    <!-- ¿Qué es HHI? -->
    <section id="que-es-hhi" class="educational-section">...</section>

    <!-- Formulario de Análisis -->
    <section id="analizar" class="analysis-section">
        <form id="analysis-form">...</form>
        <div id="drop-zone">...</div>
    </section>

    <!-- Resultados -->
    <section id="resultados" class="results-section">
        <div id="results-container">...</div>
    </section>

    <!-- Historial -->
    <section id="historial" class="history-section">...</section>

    <!-- Footer -->
    <footer class="footer">...</footer>

    <script src="/static/app.js"></script>
</body>
</html>
```

### Estilos CSS (`style.css`)

**Paleta de Colores:**
```css
:root {
    --rosa-claro: #FFF0F5;      /* Fondo principal */
    --rosa-pastel: #FFB6C1;     /* Elementos suaves */
    --rosa-medio: #FF69B4;      /* Acentos */
    --rosa-fuerte: #DB7093;     /* Textos */
    --rosa-oscuro: #8B0A50;     /* Títulos */
    
    --verde: #28A745;           /* Riesgo bajo */
    --amarillo: #FFC107;        /* Riesgo moderado */
    --naranja: #FD7E14;         /* Riesgo alto */
    --rojo: #DC3545;            /* Riesgo crítico */
}
```

**Ejemplo de Estilo:**
```css
.hero {
    background: linear-gradient(135deg, var(--rosa-claro), #FFE4E9);
    padding: 8rem 2rem 4rem;
    text-align: center;
}

.hero-title {
    font-size: 2.5rem;
    color: var(--rosa-oscuro);
    margin-bottom: 1rem;
}
```

### Interactividad JavaScript (`app.js`)

**Flujo de Análisis Manual:**

```javascript
// 1. Escuchar submit del formulario
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // 2. Construir payload
    const payload = {
        municipio: document.getElementById('municipio').value,
        cartera_a: parseFloat(document.getElementById('cartera_a').value),
        // ... más campos
    };
    
    // 3. Enviar a API
    const response = await fetch('/analizar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    // 4. Procesar respuesta
    if (response.ok) {
        const data = await response.json();
        showResults(data);  // Actualiza DOM con resultados
    }
});

// 5. Mostrar resultados
function showResults(data) {
    // Actualizar KPIs
    document.getElementById('kpi-npl').textContent = 
        (data.indice_riesgo * 100).toFixed(2) + '%';
    
    // Actualizar gráficos
    createComposicionChart(data);
    createNivelChart(data);
    
    // Scroll a resultados
    document.getElementById('resultados').scrollIntoView({ 
        behavior: 'smooth' 
    });
}
```

---

## 📡 Endpoints Disponibles

### 1. `GET /` — Health Check

**Descripción:** Verifica que la API esté funcionando.

**Request:**
```bash
curl http://127.0.0.1:8000/
```

**Response:**
```json
{
  "mensaje": "API de Riesgo Crediticio",
  "documentacion": "/docs",
  "version": "1.0.0"
}
```

---

### 2. `POST /analizar` — Crear Análisis

**Descripción:** Registra un nuevo municipio y calcula indicadores.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/analizar \
  -H "Content-Type: application/json" \
  -d '{
    "municipio": "Bogotá D.C.",
    "cartera_a": 1500000000,
    "cartera_b": 200000000,
    "cartera_c": 50000000,
    "cartera_d": 25000000,
    "cartera_e": 10000000,
    "total_cartera": 1785000000,
    "total_captaciones": 2000000000
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "municipio": "Bogotá D.C.",
  "fecha_analisis": "2026-03-08T10:30:00",
  "indice_riesgo": 0.0476,
  "nivel_riesgo": "riesgo_moderado",
  "pct_cartera_sana": 95.24,
  "pct_cartera_mora": 4.76,
  "ratio_liquidez": 1.12,
  "hhi": 0.7234,
  "concentracion_riesgo": 61.70,
  "mensaje": "⚠ ALERTA: Cartera en mora elevada (>5%)"
}
```

**Errores Posibles:**

| Código | Mensaje | Causa |
|--------|---------|-------|
| 422 | `ensure this value is greater than 0` | `total_cartera: 0` |
| 422 | `ensure this value has at least 2 characters` | `municipio: "X"` |
| 422 | `value is not a valid float` | `cartera_a: "texto"` |

---

### 3. `GET /historial` — Listar Análisis

**Descripción:** Retorna todos los análisis registrados.

**Request:**
```bash
curl http://127.0.0.1:8000/historial
```

**Response:**
```json
{
  "total_registros": 3,
  "fecha_consulta": "2026-03-08T10:35:00",
  "analisis": [
    {
      "id": 1,
      "municipio": "Bogotá D.C.",
      "indice_riesgo": 0.0476,
      "nivel_riesgo": "riesgo_moderado",
      ...
    },
    {
      "id": 2,
      "municipio": "Medellín",
      "indice_riesgo": 0.0312,
      "nivel_riesgo": "riesgo_bajo",
      ...
    }
  ]
}
```

---

### 4. `GET /historial/{id}` — Obtener por ID

**Descripción:** Obtiene un análisis específico.

**Request:**
```bash
curl http://127.0.0.1:8000/historial/1
```

**Response:**
```json
{
  "id": 1,
  "municipio": "Bogotá D.C.",
  "request": {...},
  "resultados": {...},
  "fecha_analisis": "2026-03-08T10:30:00"
}
```

**Error 404:**
```json
{
  "detail": "Análisis con ID 1 no encontrado"
}
```

---

### 5. `DELETE /historial/{id}` — Eliminar Análisis

**Descripción:** Elimina un análisis del historial.

**Request:**
```bash
curl -X DELETE http://127.0.0.1:8000/historial/1
```

**Response:**
```json
{
  "mensaje": "Análisis 1 eliminado exitosamente",
  "id_eliminado": 1,
  "analisis_restantes": 2
}
```

---

### 6. `POST /upload` — Cargar Archivo Masivo

**Descripción:** Carga múltiples municipios desde CSV o Excel.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/upload \
  -F "file=@datos_municipios.csv"
```

**Formato CSV Esperado:**
```csv
municipio,cartera_a,cartera_b,cartera_c,cartera_d,cartera_e,total_cartera,total_captaciones
Bogotá D.C.,1500000000,200000000,50000000,25000000,10000000,1785000000,2000000000
Medellín,800000000,100000000,30000000,15000000,5000000,950000000,1100000000
Cali,600000000,80000000,25000000,12000000,3000000,720000000,850000000
```

**Response:**
```json
{
  "mensaje": "Se procesaron 3 municipios exitosamente",
  "ids_creados": [4, 5, 6],
  "errores": []
}
```

---

## 🧪 Ejemplos de Uso

### Ejemplo 1: Análisis Manual en la Interfaz

1. Abre `http://127.0.0.1:8000/static/index.html`
2. Navega a la sección "Analizar"
3. Completa el formulario:
   - Municipio: `Bogotá D.C.`
   - Categoría A: `1500000000`
   - Categoría B: `200000000`
   - Categoría C: `50000000`
   - Categoría D: `25000000`
   - Categoría E: `10000000`
   - Total Cartera: `1785000000`
   - Total Captaciones: `2000000000`
4. Click en "Ejecutar Análisis"
5. Revisa los resultados:
   - **NPL:** 4.76% (Riesgo Moderado)
   - **Cartera Sana:** 95.24%
   - **HHI:** 0.7234 (Alta concentración)

---

### Ejemplo 2: Carga de Archivo CSV

1. Crea un archivo `municipios.csv`:
```csv
municipio,cartera_a,cartera_b,cartera_c,cartera_d,cartera_e,total_cartera
Bogotá,1500000000,200000000,50000000,25000000,10000000,1785000000
Medellín,800000000,100000000,30000000,15000000,5000000,950000000
Cali,600000000,80000000,25000000,12000000,3000000,720000000
```

2. En la interfaz web, arrastra el archivo a la zona de upload
3. La API procesa los 3 municipios
4. Revisa el historial para ver todos los análisis

---

### Ejemplo 3: Uso desde Python

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Crear análisis
datos = {
    "municipio": "Bucaramanga",
    "cartera_a": 500000000,
    "cartera_b": 50000000,
    "cartera_c": 15000000,
    "cartera_d": 8000000,
    "cartera_e": 2000000,
    "total_cartera": 575000000,
}

response = requests.post(f"{BASE_URL}/analizar", json=datos)

if response.status_code == 201:
    resultado = response.json()
    print(f"Municipio: {resultado['municipio']}")
    print(f"NPL: {resultado['indice_riesgo']*100:.2f}%")
    print(f"Nivel: {resultado['nivel_riesgo']}")
else:
    print(f"Error: {response.json()}")
```

---

## ❓ Preguntas Frecuentes

### ¿Qué pasa si envío `total_cartera: 0`?

Pydantic rechaza el request con HTTP 422:
```json
{
  "detail": [{
    "loc": ["body", "total_cartera"],
    "msg": "ensure this value is greater than 0",
    "type": "value_error.number.not_gt"
  }]
}
```

**¿Por qué?** Para evitar `ZeroDivisionError` en el cálculo del NPL.

---

### ¿Los datos persisten después de reiniciar?

**No.** El historial se almacena en memoria (`historial_analisis = {}`). Si reinicias el servidor, se pierden todos los análisis.

**Alternativa:** Usar SQLite o PostgreSQL (requiere modificar el código).

---

### ¿Puedo usar la API en producción?

**No directamente.** Para producción necesitas:
1. Base de datos persistente (PostgreSQL)
2. Autenticación (JWT tokens)
3. Rate limiting (evitar abuso)
4. HTTPS (certificado SSL)
5. Logging y monitoreo

---

### ¿Qué pasa si el CSV tiene columnas con otros nombres?

La API intenta mapear columnas alternativas:
- `colocaciones_a` → `cartera_a`
- `captaciones` → `total_captaciones`
- `depositos` → `total_captaciones`

Si no encuentra las columnas requeridas, retorna error.

---

### ¿Cómo funciona el botón "Ver" en el historial?

1. Hace `GET /historial/{id}`
2. Recibe los datos del análisis
3. Llama a `showResults(data)` en JavaScript
4. Actualiza KPIs y gráficos en el DOM
5. Hace scroll a la sección de resultados

---

## 📞 Recursos Adicionales

- **Datos Abiertos Gov.co:** https://www.datos.gov.co/
- **Superfinanciera:** https://www.superfinanciera.gov.co/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Pydantic Docs:** https://docs.pydantic.dev/
- **Chart.js:** https://www.chartjs.org/

---

## 🏆 Estado del Proyecto

| Criterio | Estado |
|----------|--------|
| Setup y entorno | ✅ Completado |
| Modelos Pydantic | ✅ Completos |
| Endpoints CRUD | ✅ 7 endpoints |
| Interfaz web | ✅ Funcional |
| Conceptos Semana 1 | ✅ Aplicados |
| Conceptos Semana 2 | ✅ Aplicados |
| Conceptos Semana 3 | ✅ Aplicados |
| Conceptos Semana 4 | ✅ Aplicados |
| Conceptos Semana 5 | ✅ Aplicados |
| Conceptos Semana 6 | ✅ Aplicados |
| Documentación | ✅ Completa |

---

## 📚 Alineación con el Sílabus del Curso

### ¿Por qué NO usamos Flask? (Semanas 3-4 del sílabus)

El sílabus del curso establece un camino pedagógico que pasa por **Flask (Semana 3)** antes de llegar a **FastAPI (Semana 4)**. Sin embargo, este proyecto tomó una ruta alternativa justificada:

#### Ruta del Sílabus vs. Ruta del Proyecto

| Semana | Sílabus (Ruta Pedagógica) | Este Proyecto (Ruta Directa) | Justificación |
|--------|---------------------------|------------------------------|---------------|
| **Semana 3** | Flask: Crear endpoint `/clean` | ⏭️ **Omitido** | Flask es un framework WSGI síncrono que está siendo reemplazado por frameworks ASGI modernos |
| **Semana 4** | Migrar de Flask a FastAPI | ✅ **FastAPI directo** | Se implementó directamente la solución final sin paso intermedio |

#### Razones Técnicas para Omitir Flask

1. **Obsolescencia Tecnológica:**
   - **Flask** usa **WSGI** (síncrono, diseñado para Python 2.x)
   - **FastAPI** usa **ASGI** (asíncrono, nativo para Python 3.7+)
   - La industria se está moviendo hacia frameworks asíncronos (FastAPI, Starlette, Quart)

2. **Doble Trabajo Innecesario:**
   ```
   Ruta del sílabus:
     Semana 3: Crear API en Flask (4-6 horas)
     Semana 4: Desechar Flask, reescribir en FastAPI (4-6 horas)
     Total: 8-12 horas de trabajo duplicado
   
   Ruta directa:
     Semana 3-4: Crear API en FastAPI (6-8 horas)
     Total: 6-8 horas, código de producción listo
   ```

3. **Conceptos Equivalentes:**
   | Concepto | Flask (WSGI) | FastAPI (ASGI) | Aprendido |
   |----------|--------------|----------------|-----------|
   | Routing | `@app.route("/clean")` | `@app.post("/analizar")` | ✅ Mismo patrón decorador |
   | Request | `request.json` | `datos: RiesgoCrediticioInput` | ✅ Más type hints |
   | Response | `return jsonify({...})` | `return {...}` | ✅ Automático |
   | Docs | ❌ Sin docs automáticas | ✅ Swagger UI automático | ✅ Mejor en FastAPI |

4. **Validación de Datos:**
   - **Flask:** Validación manual con `if/else` o librerías externas
   - **FastAPI:** Validación automática con Pydantic integrada
   - **Aprendizaje:** Se aplicó Pydantic directamente en el contexto moderno

5. **Type Hinting:**
   - **Flask:** Opcional, no se aprovecha para validación
   - **FastAPI:** Esencial, usado para validación y documentación automática
   - **Aprendizaje:** Se entendió la importancia del type hinting desde el inicio

#### ¿Se Perdieron Algunos Aprendizajes?

**No.** Los conceptos que Flask enseña se aprendieron de otras formas:

| Concepto de Flask | Cómo se Aprendió en Este Proyecto |
|-------------------|-----------------------------------|
| Routing básico | `@app.get("/")`, `@app.post("/analizar")` en FastAPI |
| Request/Response | Endpoints reciben `RiesgoCrediticioInput` y retornan dicts |
| Variables de ruta | `/historial/{analisis_id}` en FastAPI |
| Status codes | `status_code=201`, `HTTPException(status_code=404)` |
| Testing | `curl`, Swagger UI "Try it out", tests manuales |

#### Beneficios de la Ruta Directa

1. **Código de Producción:** El proyecto está listo para desplegar (no hay que desechar Flask)
2. **Mejores Prácticas Modernas:** Async/await, type hints, validación automática
3. **Documentación Automática:** Swagger UI genera docs interactivas sin trabajo extra
4. **Menos Código Boilerplate:** FastAPI requiere menos líneas para la misma funcionalidad
5. **Rendimiento:** ASGI permite concurrencia real con async/await

#### Conclusión

**Flask fue un paso pedagógico intermedio** diseñado para que los estudiantes entendieran:
1. Qué es un framework web
2. Cómo funciona el ciclo request-response
3. La diferencia entre WSGI (síncrono) y ASGI (asíncrono)

**Este proyecto demuestra que se entendieron esos conceptos** al implementar directamente una API completa en FastAPI que:
- ✅ Usa decoradores para routing (mismo patrón que Flask)
- ✅ Maneja request/response HTTP correctamente
- ✅ Valida datos de entrada con Pydantic
- ✅ Retorna status codes apropiados (201, 404, 422)
- ✅ Genera documentación automática en `/docs`

**La omisión de Flask fue una decisión técnica justificada**, no un atajo. El resultado es un proyecto más robusto, moderno y listo para producción, manteniendo todos los aprendizajes esenciales del curso.

---

### Mapeo Completo con el Sílabus

| Semana | Tema del Sílabus | Implementado en Este Proyecto | Archivo/Ubicación |
|--------|------------------|-------------------------------|-------------------|
| 1 | Funciones puras, limpieza Pandas | ✅ `procesar_riesgo_crediticio()` | `main.py:249` |
| 2 | Pydantic Input/Output | ✅ `RiesgoCrediticioInput/Output` | `main.py:60,137` |
| 3 | Flask `/clean` endpoint | ⏭️ Omitido (justificado arriba) | — |
| 4 | FastAPI con validación | ✅ 7 endpoints CRUD | `main.py:400-730` |
| 5 | Validaciones de rango | ✅ `ge=0`, `gt=0`, `min_length` | `main.py:75-135` |
| 6 | pydantic-settings | ✅ `Settings` class | `config.py:48-140` |

---

**Hecho con 💖 y código Python**

**Autores:** Angela Rico · Sebastian Ramirez
**Universidad:** Universidad Santo Tomás
**Curso:** Python para APIs e IA Aplicada
**Año:** 2026
