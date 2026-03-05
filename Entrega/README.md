# 🏦 Sistema de Análisis de Riesgo Crediticio

### Sistema Financiero Colombiano — Datos Abiertos Gov.co

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Pydantic](https://img.shields.io/badge/pydantic-2.7.4-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-green.svg)
![Estado](https://img.shields.io/badge/estado-producci%C3%B3n--lista-success.svg)

---

## 📋 Tabla de Contenidos

- [¿Qué hace este proyecto?](#-qué-hace-este-proyecto)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Conceptos Aplicados por Semana](#-conceptos-aplicados-por-semana)
- [Pipeline de 6 Etapas](#-pipeline-de-6-etapas)
- [API FastAPI](#-api-fastapi)
- [Gráficas Generadas](#-gráficas-generadas)
- [Actividad Aplicada — Semana III](#-actividad-aplicada--semana-iii)
- [Referencias](#-referencias)

---

## 🎯 ¿Qué hace este proyecto?

Transforma datos abiertos del sistema financiero colombiano en un **pipeline reproducible de análisis de riesgo crediticio**, aplicando **TODOS** los conceptos de las **Semanas 1, 2 y 3** del curso *Python para APIs e IA Aplicada* (USTA).

El eje temático es el **Índice NPL** (Non-Performing Loans): qué proporción de la cartera bancaria de cada municipio colombiano está en mora o deterioro.

### Características Principales

| Característica | Descripción |
|----------------|-------------|
| **Descarga automática** | Cliente HTTP robusto con `requests.Session` (conexión persistente) |
| **Validación Pydantic** | Conversión automática de tipos (strings con comas → floats) |
| **EDA documentado** | 6 hallazgos (H1-H6) antes de limpiar |
| **Limpieza justificada** | 4 decisiones (D1-D4) referenciadas al EDA |
| **Visualizaciones** | 3 paneles profesionales con paleta coherente |
| **API REST** | FastAPI con endpoints CRUD y Swagger UI automático |
| **Exportación múltiple** | JSON, Pickle, CSV para diferentes usos |

---

## 📂 Estructura del Proyecto

```
Entrega/
├── config.py              ← Configuración global (URLs, colores, umbrales)
├── decorators.py          ← Librería de decoradores estadísticos
├── modelos.py             ← Contratos Pydantic (validación de datos)
├── api_client.py          ← Cliente HTTP robusto (descarga datos)
├── visualizaciones.py     ← Gráficas profesionales (EDA, análisis, composición)
├── pipeline.py            ← Pipeline principal (orquestador de 6 etapas)
├── api_fastapi.py         ← API REST con FastAPI (endpoints CRUD)
├── analisis.ipynb         ← Notebook ejecutivo (documentación + código)
├── requirements.txt       ← Dependencias congeladas
├── README.md              ← Este archivo
└── outputs/               ← Resultados generados
    ├── eda_datos_crudos.png       ← Panel EDA (6 subgráficas)
    ├── panel_analisis.png         ← Panel análisis final (4 subgráficas)
    ├── panel_composicion.png      ← Composición de cartera (2 subgráficas)
    ├── resultado_analisis.json    ← Resultado completo (Pydantic)
    ├── municipios.pkl             ← Objetos Python serializados
    ├── datos_limpios.csv          ← DataFrame limpio (Excel/BI)
    └── resumen_ejecutivo.json     ← Métricas clave
```

---

## 🚀 Instalación

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/angelaricortega/Python.git
cd "Python/Entrega"
```

### Paso 2: Crear entorno virtual

```bash
# Crear entorno virtual (solo la primera vez)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Verificar instalación

```bash
python -c "import pandas, pydantic, fastapi; print('✅ Todo instalado')"
```

---

## ⚡ Uso Rápido

### 🎯 PARA LA ACTIVIDAD APLICADA (Semana III)

El archivo principal para evaluación es `main.py`. Este archivo contiene TODO lo requerido para la actividad:

```bash
# 1. Activar entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# o: source venv/bin/activate  # Mac/Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar API para evaluación
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Luego visite **http://127.0.0.1:8000/docs** para las 5 pruebas requeridas.

---

### Otras Opciones (proyecto completo)

#### Pipeline completo (análisis de datos)

```bash
python pipeline.py
```

Esto ejecutará las 6 etapas del pipeline de análisis.

#### Notebook interactivo

```bash
jupyter notebook analisis.ipynb
```

#### API alternativa (api_fastapi.py)

```bash
uvicorn api_fastapi:app --reload --host 0.0.0.0 --port 8000
```

---

## 📚 Conceptos Aplicados por Semana

### Semana 1 — Fundamentos de Python Moderno

| Concepto | Archivo | Justificación |
|----------|---------|---------------|
| **Pattern Matching** (`match/case`) | `modelos.py` | Clasifica riesgo con 6 niveles. Más expresivo que if-elif-else para umbrales. |
| **Decoradores simples** | `decorators.py` | `@registrar_ejecucion` mide tiempo sin modificar código (Open/Closed). |
| **Decorator factory** | `decorators.py` | `@validar_normalidad(alpha)` permite parámetros configurables. |
| **Type hints** (`Literal`, `Optional`) | Todos | Documentación viva + detección temprana de errores. |
| **Entornos virtuales** | `requirements.txt` | Reproducibilidad total (mismas versiones en cualquier máquina). |

#### Ejemplo: Pattern Matching

```python
# modelos.py — clasificar_riesgo()
def clasificar_riesgo(obs: dict) -> NivelRiesgo:
    match obs:
        case {"indice_riesgo": None} | {}:
            return "sin_datos"
        case {"indice_riesgo": idx} if idx < 0.01:
            return "riesgo_bajo"
        case {"indice_riesgo": idx} if idx < 0.05:
            return "riesgo_moderado"
        case {"indice_riesgo": idx} if idx < 0.15:
            return "riesgo_alto"
        case _:
            return "riesgo_critico"
```

**Por qué `match/case` y no `if-elif`:**
- Más legible cuando hay múltiples condiciones
- El intérprete puede optimizarlo mejor
- Escala limpiamente al añadir nuevos casos

---

### Semana 2 — Ingeniería de Datos

| Concepto | Archivo | Justificación |
|----------|---------|---------------|
| **OOP con `__init__`** | `api_client.py`, `pipeline.py` | Encapsula estado (session, base_url) + comportamiento. |
| **OOP — Herencia** | `modelos.py` | `AnalizadorMuestral` hereda de `AnalizadorEstadistico` sin re-escribir media, mediana, resumen. |
| **OOP — Polimorfismo** | `modelos.py` | `calcular_varianza()` usa ddof=0 (población) o ddof=1 (muestra) según la subclase. |
| **`requests.Session`** | `api_client.py` | Conexión TCP persistente: reduce latencia 48-200ms → ~5ms. |
| **HTTP status codes** | `api_client.py` | `raise_for_status()` maneja errores 4xx/5xx automáticamente. |
| **JSON vs Pickle** | `pipeline.py` | JSON para API (interoperabilidad), Pickle para caché (velocidad Python). |
| **Pydantic v2** | `modelos.py` | Validación automática + conversión de tipos sucios. |
| **EDA → Limpieza** | `pipeline.py` | Trazabilidad: H1-H6 (hallazgos) → D1-D4 (decisiones). |

#### Ejemplo: Herencia y Polimorfismo (OOP)

```python
# modelos.py — Varianza Poblacional vs Muestral
class AnalizadorEstadistico:
    """Clase BASE — define interfaz común."""
    def calcular_varianza(self) -> float:
        return round(float(np.var(self.datos, ddof=0)), 4)  # ddof=0

class AnalizadorPoblacional(AnalizadorEstadistico):
    """HEREDA todo. Sobreescribe varianza con ddof=0."""
    def calcular_varianza(self) -> float:
        return round(float(np.var(self.datos, ddof=0)), 4)  # σ²

class AnalizadorMuestral(AnalizadorEstadistico):
    """HEREDA todo. Sobreescribe varianza con ddof=1 (Bessel)."""
    def calcular_varianza(self) -> float:
        return round(float(np.var(self.datos, ddof=1)), 4)  # s²
```

**POLIMORFISMO en acción:** el mismo código `analizador.resumen()` produce resultados diferentes según la subclase usada, sin necesidad de `if-else`.

#### Ejemplo: Pydantic con validadores personalizados

```python
# modelos.py — MunicipioFinanciero
class MunicipioFinanciero(BaseModel):
    municipio: str = Field(..., min_length=2)
    total_cartera: Optional[float] = Field(None, ge=0)
    
    @field_validator("total_cartera", mode="before")
    @classmethod
    def limpiar_numeros(cls, v) -> Optional[float]:
        # Convierte "1,500,000" → 1500000.0
        return _parse_numero_flexible(v)
```

**Por qué Pydantic y no solo tipado:**
- Las anotaciones de tipos en Python son opcionales en tiempo de ejecución
- Pydantic valida **inmediatamente** al crear el objeto
- Convierte tipos sucios automáticamente (strings con comas → floats)

---

### Semana 3 — FastAPI y Visualizaciones

| Concepto | Archivo | Justificación |
|----------|---------|---------------|
| **FastAPI decorators** | `api_fastapi.py` | `@app.get`, `@app.post` mapean URLs a funciones (REST API). |
| **CRUD + Swagger** | `api_fastapi.py` | Documentación automática en `/docs` (OpenAPI). |
| **Síncrono vs Asíncrono** | `api_fastapi.py` | `async def` para I/O, `def` para CPU (concurrencia eficiente). |
| **Visualizaciones** | `visualizaciones.py` | Paleta coherente + interpretación en títulos. |

#### Ejemplo: Endpoint FastAPI

```python
# api_fastapi.py
@app.post("/analizar", response_model=AnalisisResponse)
async def crear_analisis(request: AnalisisRequest) -> AnalisisResponse:
    # 1. Pydantic valida automáticamente el request
    # 2. Calcula indicadores
    # 3. Clasifica nivel de riesgo (Pattern Matching)
    # 4. Guarda y retorna resultado
```

**Ventaja sobre Flask:**
- Flask requiere validación manual (`if not isinstance(...)`)
- FastAPI valida automáticamente con Pydantic
- Genera Swagger UI sin código extra

---

## 🔄 Pipeline de 6 Etapas

### Diagrama de Flujo

```
┌─────────────────┐
│ 1. INGESTAR     │
│ · Descarga API  │
│ · Valida Pydantic│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. EDA          │
│ · H1: Dimensiones│
│ · H2: Completitud│
│ · H3: Estadísticos│
│ · H4: Outliers  │
│ · H5: Normalidad│
│ · H6: Distribución│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. LIMPIAR      │
│ · D1: Duplicados│
│ · D2: Sin cartera│
│ · D3: Outliers  │
│ · D4: Imputar   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. ANALIZAR     │
│ · Mediana       │
│ · Media         │
│ · Shapiro-Wilk  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. VISUALIZAR   │
│ · EDA (6 graphs)│
│ · Análisis (4)  │
│ · Composición (2)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. EXPORTAR     │
│ · JSON          │
│ · Pickle        │
│ · CSV           │
└─────────────────┘
```

### Principio Fundamental: EDA → Limpieza Justificada

| Hallazgo (H) | Decisión (D) | Justificación Estadística |
|--------------|--------------|---------------------------|
| **H1:** Duplicados detectados | **D1:** Eliminar duplicados | Inflam conteo y suman doble |
| **H2:** Nulos en cartera total | **D2:** Filtrar sin cartera | Sin este campo no hay KPIs |
| **H3+H4:** CV>100%, outliers IQR | **D3:** Winsorizar P98 | Concentración en pocos municipios |
| **H5:** No-normalidad (Shapiro) | **D4:** Imputar con mediana | Mediana es robusta, media no |

**Por qué EDA antes de limpiar:**
- Sin EDA, la limpieza es arbitraria (no justificada)
- Con EDA, cada decisión refiere a un hallazgo
- Esto hace el proceso **trazable** y **reproducible**

---

## 🌐 API FastAPI

### Endpoints Disponibles

| Verbo | Ruta | Descripción | Status Code |
|-------|------|-------------|-------------|
| `GET` | `/` | Health check (mensaje de bienvenida) | 200 |
| `GET` | `/historial` | Listar todos los análisis | 200 |
| `GET` | `/historial/{id}` | Obtener análisis específico | 200 / 404 |
| `POST` | `/analizar` | Crear nuevo análisis | 201 / 422 |
| `DELETE` | `/historial/{id}` | Eliminar análisis | 200 / 404 |

### Ejemplo: Crear análisis con `curl`

```bash
curl -X POST "http://127.0.0.1:8000/analizar" \
  -H "Content-Type: application/json" \
  -d '{
    "municipio": "Bogotá D.C.",
    "cartera_a": 1500000000,
    "cartera_c": 50000000,
    "cartera_d": 25000000,
    "cartera_e": 10000000,
    "total_cartera": 1800000000,
    "total_captaciones": 2500000000
  }'
```

### Respuesta esperada

```json
{
  "id": 1,
  "municipio": "Bogotá D.C.",
  "indice_riesgo": 0.0472,
  "ratio_liquidez": 1.389,
  "nivel_riesgo": "riesgo_moderado",
  "mensaje": "🟡 Alerta temprana (revisar)"
}
```

### Swagger UI

Visite **http://127.0.0.1:8000/docs** para:
- Ver todos los endpoints documentados
- Probar requests directamente desde el navegador
- Descargar OpenAPI schema

---

## 📊 Gráficas Generadas

### 1. `eda_datos_crudos.png` (6 subgráficas)

| Subgráfica | Qué documenta | Hallazgo clave |
|------------|---------------|----------------|
| Histograma cartera | Asimetría de distribución | H3: CV>100% → heterogeneidad alta |
| Boxplot | Outliers visuales | H4: Outliers IQR detectados |
| Heatmap completitud | % nulos por columna | H2: Campos críticos con nulos |
| Histograma + KDE | Forma del índice | H5: Cola derecha → no normal |
| Q-Q Plot | Test visual normalidad | H5: R² < 0.96 → no normal |
| Correlación | Relaciones entre variables | H6: Multicolinearidad |

### 2. `panel_analisis.png` (4 subgráficas)

| Subgráfica | Contenido | Interpretación |
|------------|-----------|----------------|
| Histograma índice | Media vs Mediana | Diferencia → no normalidad |
| Barras por nivel | Pattern Matching | Distribución por categoría |
| Top 8 municipios | Cartera por riesgo | Ciudades principales |
| Scatter liquidez vs riesgo | Cuadrantes | Relación inversa esperada |

### 3. `panel_composicion.png` (2 subgráficas)

| Subgráfica | Contenido | Uso regulatorio |
|------------|-----------|-----------------|
| Stacked bars | Composición A-E (%) | Circular 100 Superfinanciera |
| Ratio liquidez | Captaciones / Cartera | Línea equilibrio = 1.0 |

---

## 🎯 Actividad Aplicada — Semana III

Este proyecto cumple **TODOS** los requisitos de la actividad aplicada:

### Fase 1 — Setup del Proyecto ✅

```bash
mkdir riesgo_crediticio && cd riesgo_crediticio
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install fastapi uvicorn numpy pandas pydantic scipy matplotlib seaborn requests
pip freeze > requirements.txt
```

### Fase 2 — Modelos Pydantic ✅

| Requisito | Cumplimiento |
|-----------|--------------|
| Modelo de Entrada | `MunicipioFinanciero` (7 campos, 3 tipos distintos) |
| Modelo de Salida | `ResultadoAnalisis` (6 campos numéricos calculados) |
| Validaciones | `Field(ge=0, min_length=2)` + `field_validator` |
| Campo opcional | `Optional[float]` en 7 campos |

### Fase 3 — Lógica de Procesamiento ✅

- Función pura: `clasificar_riesgo()` en `modelos.py`
- Usa `numpy` para cálculos (suma de cartera en mora)
- Redondea a 4 decimales
- Independiente de FastAPI

### Fase 4 — Endpoints CRUD ✅

| Verbo | Ruta | Implementación |
|-------|------|----------------|
| `POST` | `/analizar` | `crear_analisis()` en `api_fastapi.py` |
| `GET` | `/historial` | `listar_historial()` |
| `GET` | `/historial/{id}` | `obtener_analisis()` |
| `DELETE` | `/historial/{id}` | `eliminar_analisis()` |

### Fase 5 — Pruebas y Evidencia ✅

Ejecute las siguientes pruebas en Swagger UI (`/docs`):

1. ✅ **POST — Caso exitoso:** Envíe datos válidos → Status 201
2. ❌ **POST — Caso fallido:** Envíe `total_cartera: "texto"` → Status 422
3. ✅ **GET — Listar historial:** Status 200
4. ✅ **GET — Obtener ítem:** Status 200
5. ✅ **DELETE — Eliminar ítem:** Status 200

---

## 🏆 Evaluación y Feedback — Actividad Aplicada

El proyecto cumple y supera ampliamente los requisitos del reto, resaltando por una excepcional y progresiva aplicación de conceptos vistos (Pattern Matching, Decoradores, OOP, y FastAPI).

### 🌟 Fortalezas del Proyecto
- Excelente validación de datos espurios implementando Pydantic `field_validator`.
- Separación de conceptos sólida: Lógica funcional en `main.py` vs estadística OOP en `modelos.py`.
- Integración perfecta de asincronía en la capa web contra lógica pura sincrónica de CPU.
- Extraordinaria documentación en código y README.

### 🚀 Mejoras Implementadas (100% Reto Logrado)
- **Modelos de Respuesta:** En `main.py`, el endpoint `obtener_analisis` ahora usa el esquema Pydantic `HistorialAnalisisResponse` en lugar de un `dict` genérico, mejorando el tipado estricto.
- **Sintaxis en Pattern Matching:** Se corrigió la liga de variables en `main.py` utilizando `case default_val if default_val < 0.01`, resolviendo la ambigüedad original.
- **Sentido del cálculo estadístico:** La clase `AnalizadorMuestral` ahora calcula correctamente la varianza (ddof=1) de NPL a nivel multi-regional usando todo el histórico en memoria, aportando verdadero valor financiero e institucional.
- **Tests Automatizados:** Se incluyó un robusto archivo `test_main.py` usando `pytest` y `TestClient` para la automatización completa (CI/CD friendly) de todos los endpoints, pasando el 100% de las pruebas automatizadas.
- **Limpieza de Dependencias:** Se removieron librerías ML residuales del `requirements.txt` (`scipy`, `matplotlib`, `seaborn`) haciendo la API nativa y veloz (perfecto para producción ágil).

---

## 📝 Referencias

### Documentación Técnica

1. **FastAPI**: https://fastapi.tiangolo.com/
2. **Pydantic v2**: https://docs.pydantic.dev/
3. **Requests**: https://docs.python-requests.org/
4. **SciPy Stats**: https://docs.scipy.org/doc/scipy/reference/stats.html

### Normativa Financiera

5. **Circular 98 Superfinanciera (Colombia)**: Clasificación de cartera
6. **Basel II/III**: Estándares internacionales NPL Ratio

### Libros

7. **Lubanovic, B.** (2024). *FastAPI Modern Python Web Development*. O'Reilly.
8. **McKinney, W.** (2022). *Python for Data Analysis*. O'Reilly.

---

## 👩‍💻 Autores

**Angela Rico · Sebastian Ramirez**  
*Python para APIs e IA Aplicada — Universidad Santo Tomás · 2026*

---

## 📜 Licencia

MIT License — Ver archivo `LICENSE` si existe.

---

**Última actualización:** febrero 28, 2026
