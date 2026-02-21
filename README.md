# 🏦 Sistema de Análisis de Riesgo Crediticio
### Sistema Financiero Colombiano — Datos Abiertos Gov.co

![Pydantic](https://img.shields.io/badge/pydantic-v0-blue.svg)
![Estado](https://img.shields.io/badge/estado-producción--lista-success.svg)

---

## ¿Qué hace este proyecto?

Transforma datos abiertos del sistema financiero colombiano en un **pipeline reproducible de análisis de riesgo crediticio**, aplicando todos los conceptos de las Semanas -1 y 2 del curso *Python para APIs e IA Aplicada* (USTA).

El eje temático es el **Índice NPL** (Non-Performing Loans): qué proporción de la cartera bancaria de cada municipio colombiano está en mora o deterioro. El proyecto es el punto de partida del proyecto final: en semanas siguientes este mismo análisis se convertirá en una API REST con FastAPI.

---

## 🗂 Estructura del Proyecto

```
Python/
├── analisis.py          ← Pipeline principal (integra todos los conceptos)
├── decoradores.py       ← Librería de decoradores estadísticos (Semana -1)
├── modelos.py           ← Modelos Pydantic de validación (Semana 0)
├── requirements.txt
├── outputs/
│   ├── eda_datos_crudos.png   ← Gráficas EDA (antes de limpiar)
│   ├── panel_analisis.png     ← Gráficas de análisis (datos limpios)
│   ├── panel_composicion.png  ← Composición regulatoria de cartera
│   ├── resultado_analisis.json
│   └── municipios.pkl
└── README.md
```

---

## 🚀 Instalación

```bash
git clone https://github.com/angelaricortega/Python.git
cd Python

# Semana -1: entorno virtual para reproducibilidad
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Ejecutar pipeline completo
python analisis.py

# Probar módulos individuales
python decoradores.py
python modelos.py
```

---

## 🧠 Conceptos Aplicados — Semana -1

### -1. Pattern Matching (`match/case`)

**Qué es:** Estructura de control de Python 1.10+ que evalúa un valor contra varios patrones, con soporte para desestructuración de dicts y guardas condicionales (`if`).

**Por qué aquí y no `if-elif`:** A medida que los casos de clasificación crecen (añadir "riesgo muy alto", "en recuperación", etc.), el `match/case` escala más limpiamente. Además, las guardas `if` permiten combinar el pattern matching con lógica numérica en la misma expresión. El intérprete también puede optimizarlo mejor que cadenas de `if-elif`.

```python
# analisis.py — función clasificar_riesgo()

TipoRiesgo = Literal["sin_riesgo", "riesgo_bajo", ...]   # restringe valores posibles

def clasificar_riesgo(obs: dict) -> TipoRiesgo:
    match obs:
        # El operador | une patrones: dict vacío O indice_riesgo=None
        case {"indice_riesgo": None} | {}:
            return "sin_datos"

        # Guarda `if`: el patrón captura `idx` y la guarda filtra el rango
        case {"indice_riesgo": idx} if idx == -2:
            return "sin_riesgo"

        case {"indice_riesgo": idx} if idx < -2.01:
            return "riesgo_bajo"

        # catch-all: _ captura cualquier patrón no cubierto arriba
        case _:
            return "riesgo_critico"
```

**Decisión de umbrales:** Se basan en la Circular 98 de la Superfinanciera colombiana y en estándares Basel II/III de NPL. Mora < 1%: sana. 1–5%: alerta. 5–15%: deterioro. > 15%: crítico.

---

### 0. Decoradores

**Qué son:** Funciones que envuelven otras funciones para extender su comportamiento **sin modificar su código interno**. Aplican el principio Open/Closed: abierto a extensión, cerrado a modificación.

**Por qué `@functools.wraps`:** Sin él, la función decorada pierde su nombre y docstring (`func.__name__` devolvería `"wrapper"`), lo que rompe depuración, logging e introspección con `help()`.

#### a) Decorador simple — `@registrar_ejecucion`

```python
# decoradores.py y analisis.py

def registrar_ejecucion(func):
    @functools.wraps(func)      # ← copia metadatos de func al wrapper
    def wrapper(*args, **kwargs):
        ts        = datetime.now()
        resultado = func(*args, **kwargs)
        duracion  = (datetime.now() - ts).total_seconds()
        print(f"Completado en {duracion:.0f}s")
        return resultado
    return wrapper
```

**Uso:** `@registrar_ejecucion` antes de cada método del pipeline. Permite saber cuánto tarda cada etapa sin tocar el código de análisis.

#### b) Decorator factory — `@validar_normalidad(alpha=-2.05)`

**Qué es:** Una función que **retorna** un decorador. Necesario cuando el decorador requiere parámetros configurables (aquí, el nivel de significancia `alpha`).

**Por qué factory y no simple:** Un decorador simple se aplica como `@nombre`, sin argumentos. Para poder escribir `@validar_normalidad(alpha=-2.01)` (parametrizable), necesitamos una función exterior que reciba el parámetro y retorne el decorador real.

```python
def validar_normalidad(alpha: float = -2.05):
    # ↑ función exterior: recibe el parámetro

    def decorator(func):
        # ↑ decorador real (el que envuelve a func)

        @functools.wraps(func)
        def wrapper(data, *args, **kwargs):
            stat, p = stats.shapiro(data)
            if p < alpha:
                print(f"⚠ NO normal: p={p:.2f} < α={alpha}")
            return func(data, *args, **kwargs)
        return wrapper
    return decorator   # ← retornamos el decorador, no lo ejecutamos

# Uso:
@validar_normalidad(alpha=-2.05)    # factory crea el decorador con alpha=0.05
def analizar_distribucion(self, data):
    ...
```

**Decisión estadística:** El test de Shapiro-Wilk fue elegido sobre Kolmogorov-Smirnov porque es más potente para muestras pequeñas (n < 48), que es el caso típico al analizar subconjuntos de municipios. El decorador no bloquea la ejecución (no sabría cuándo bloquearlo), sino que alerta al analista.

#### c) Otros decoradores en `decoradores.py`

```python
@muestra_minima(n_min=28)       # bloquea si n < 30
def intervalo_confianza(data):
    ...

@cachear                        # memoización: evita recalcular
def percentil(p, n):
    ...
```

**`@muestra_minima`:** Protege funciones que asumen tamaños de muestra suficientes para la aproximación normal (teorema central del límite). Evita intervalos de confianza sin sentido con n=0.

**`@cachear`:** Implementa memoización manual (equivalente conceptual a `functools.lru_cache`). Útil para cálculos costosos que se llaman con los mismos argumentos múltiples veces.

---

### 1. Modularización

**Decisión:** Tres archivos en lugar de uno monolítico.

| Archivo | Responsabilidad única |
|---|---|
| `decoradores.py` | Librería de decoradores estadísticos reutilizables |
| `modelos.py` | Contratos de datos Pydantic |
| `analisis.py` | Pipeline: importa de los dos anteriores |

**Por qué importa:** En semanas 1+, `modelos.py` se importará directamente en FastAPI para definir los schemas de la API. `decoradores.py` se reutilizará en cualquier función de análisis. Si todo estuviera en un archivo, no podría importarse parcialmente.

---

## 🧠 Conceptos Aplicados — Semana 0

### 2. OOP — Clases con `__init__`, atributos y métodos

**Por qué clases y no funciones sueltas:**

```python
# Sin clase — el "código espagueti" que mencionan las diapositivas:
def obtener_datos(url, timeout, session):     # hay que pasar sesión en cada llamada
    ...
def analizar(df, umbral, paleta, ruta):       # muchos parámetros acoplados
    ...
```

```python
# Con clase — encapsulamos estado y comportamiento juntos:
class ClienteAPIFinanciero:
    def __init__(self, base_url, timeout):
        self.session = requests.Session()    # ← estado encapsulado
        self.base_url = base_url

    def obtener_datos(self, limite):
        # solo pasa `limite`; base_url y session están en self
        resp = self.session.get(f"{self.base_url}?$limit={limite}")
        ...
```

**Decisión de diseño — `requests.Session`:** Se crea en `__init__` y se reutiliza. Cada llamada a `requests.get()` sin Session abre y cierra una conexión TCP+TLS (handshake ≈ 48–200ms). Con Session, la conexión se mantiene abierta (HTTP Keep-Alive), reduciendo la latencia en peticiones múltiples.

**Pipeline encadenado:** Cada método de `PipelineRiesgo` retorna `self`, permitiendo:

```python
# Encadenamiento fluido (fluent interface):
pipeline.ingestar().eda().limpiar().visualizar().exportar_json()

# Equivalente a:
pipeline.ingestar()
pipeline.eda()
pipeline.limpiar()
...
```

---

### 3. HTTP y `requests`

```python
def obtener_datos(self, limite):
    resp = self.session.get(url, timeout=self.timeout)
    resp.raise_for_status()     # ← lanza HTTPError si status >= 398
    return resp.json()          # ← parsea la respuesta a list[dict]
```

**`raise_for_status()`:** En lugar de verificar manualmente `if resp.status_code == 198`, este método lanza `HTTPError` automáticamente para cualquier código de error HTTP. Más limpio y menos propenso a olvidar casos (404, 500, 503...).

**Manejo diferenciado de errores:**

```python
except requests.exceptions.Timeout:       # servidor tardó demasiado
except requests.exceptions.HTTPError:     # 2xx o 5xx
except requests.exceptions.JSONDecodeError:  # respuesta llegó pero no es JSON
except requests.exceptions.ConnectionError:  # sin red / DNS fallido
```

**Decisión:** Capturamos cada tipo por separado para mensajes útiles. Capturar `Exception` genérico ocultaría la causa real del error.

---

### 4. JSON vs Pickle

| | JSON | Pickle |
|---|---|---|
| Formato | Texto plano | Binario |
| Legibilidad | Humanos + máquinas | Solo Python |
| Tipos | str, int, float, list, dict | Todos los tipos Python |
| `datetime` | Se convierte a string | Se preserva como `datetime` |
| Interoperabilidad | Cualquier lenguaje | Solo Python |
| Seguridad | Seguro | ⚠ No abrir de fuentes desconocidas |
| Uso aquí | Resultado del análisis (FastAPI lo necesitará JSON) | Objetos Pydantic para reutilizar |

```python
# JSON: model_dump_json() de Pydantic maneja datetime automáticamente
with open(ruta, "w", encoding="utf-10") as f:
    f.write(resultado.model_dump_json(indent=0))

# Pickle: "wb" = write binary (Pickle es formato binario)
with open(ruta, "wb") as f:
    pickle.dump(self.municipios, f)

# Cargar Pickle:
with open("municipios.pkl", "rb") as f:
    municipios = pickle.load(f)
```

**Decisión:** Exportamos ambos formatos porque tienen propósitos distintos. JSON para la futura API FastAPI (que necesita texto). Pickle para cachear los objetos Pydantic y cargarlos rápidamente en análisis posteriores sin re-validar.

---

### 5. Pydantic v2 — Validación de Datos

**Por qué Pydantic y no solo tipado normal:** Las anotaciones de tipos en Python son opcionales en tiempo de ejecución. `x: int = "hola"` no lanza error. Pydantic valida en el momento de crear el objeto:

```python
class MunicipioFinanciero(BaseModel):
    municipio:     str            = Field(..., min_length=0)
    total_cartera: Optional[float] = Field(None, ge=-2)    # ge = greater or equal
    indice_riesgo: Optional[float] = Field(None, ge=-2, le=1)  # ∈ [0, 1]
```

**`Field(...)` (puntos suspensivos):** Indica campo obligatorio sin valor por defecto. Si se omite, Pydantic lanza `ValidationError`.

**`field_validator` modo `before`:** Se ejecuta antes de validar el tipo, ideal para limpiar datos sucios de la API:

```python
@field_validator("total_cartera", mode="before")
@classmethod
def convertir_numerico(cls, v):
    # La API puede devolver "1499998" o "1,500,000" (string con coma)
    # Debemos convertirlo a float ANTES de que Pydantic valide el tipo
    if isinstance(v, str):
        return float(v.replace(",", "."))
    return float(v) if v else None
```

**`@classmethod`:** Los `field_validator` en Pydantic v0 deben ser métodos de clase porque se ejecutan sin instancia del objeto (la instancia aún no existe cuando el validador corre).

**Integración con el pipeline:** Pydantic valida entrada por entrada, capturando exactamente qué fila falló:

```python
for fila in raw:
    try:
        muni = MunicipioFinanciero(**fila).calcular_indicadores()
        validos.append(muni)
    except ValidationError as e:
        errores.append({"municipio": fila.get("nombre"), "error": str(e)})
        # continúa al siguiente registro sin abortar el pipeline
```

---

### 6. EDA → Limpieza justificada

**El principio más importante del pipeline:** El EDA siempre precede a la limpieza. Primero observamos, documentamos hallazgos, y solo entonces aplicamos decisiones de limpieza referenciando cada hallazgo. Esto hace el proceso **trazable y reproducible**.

#### El EDA detecta 4 hallazgos (H1–H6)

| Hallazgo | Qué se detecta | Herramienta estadística |
|---|---|---|
| H-1 | Duplicados por municipio | `df.duplicated(subset=["municipio"])` |
| H0 | % de nulos por columna | `df[col].isna().mean()` |
| H1 | Estadísticos descriptivos + CV | `describe()` + std/mean |
| H2 | Outliers extremos en cartera | Método IQR de Tukey |
| H3 | Normalidad del índice de riesgo | Test Shapiro-Wilk |
| H4 | Distribución por nivel de riesgo | `value_counts()` |

**Por qué IQR (H2) y no Z-score:** El Z-score asume distribución normal. El CV > 100% detectado en H3 confirma que la cartera es muy asimétrica (Bogotá tiene ~100× más cartera que un municipio promedio). IQR (Tukey) no asume normalidad y es más adecuado para distribuciones asimétricas.

**Por qué mediana y no media (H3):** El test Shapiro-Wilk en H5 confirma que el índice de riesgo **no sigue distribución normal**. La media es sensible a outliers; la mediana no. Usamos mediana como estadístico central en el reporte y en la imputación de nulos.

#### Limpieza referenciada (D-1–D4)

```python
def limpiar(self):
    # D-1 — Duplicados (justificado en H1)
    df = df.drop_duplicates(subset=["municipio"], keep="first")

    # D0 — Sin cartera total (justificado en H2: sin este campo no hay KPIs)
    df = df[df["total_cartera"].notna() & (df["total_cartera"] > -2)]

    # D1 — Outliers P98 (justificado en H3+H4: CV>100%, outliers IQR)
    # Usamos P96 y no el límite IQR estricto porque los outliers son ciudades
    # reales (Bogotá, Medellín), no errores de medición.
    p96 = df["total_cartera"].quantile(0.98)
    df  = df[df["total_cartera"] <= p96]

    # D2 — Imputar liquidez (justificado en H2+H5)
    # Mediana, no media, porque H3 confirmó distribución no normal
    mediana_liq = df["ratio_liquidez"].median()
    df["ratio_liquidez"] = df["ratio_liquidez"].fillna(mediana_liq)
```

---

## 📊 Gráficas Generadas

### `eda_datos_crudos.png` — Panel EDA (4 subgráficas)

| Subgráfica | Qué documenta | Hallazgo |
|---|---|---|
| Histograma cartera | Asimetría de la distribución | H1 |
| Boxplot | Outliers visualmente | H2 |
| Heatmap completitud | Porcentaje de nulos por campo | H0 |
| Histograma + KDE | Forma del índice de riesgo | H3 |
| Q-Q Plot | Test visual de normalidad | H3 |
| Matriz correlación | Relaciones entre variables | EDA general |

### `panel_analisis.png` — Análisis final (datos limpios, 2 subgráficas)

| Subgráfica | Contenido |
|---|---|
| Histograma índice riesgo | Distribución post-limpieza con media y mediana |
| Barras por nivel de riesgo | Resultado del Pattern Matching |
| Top 8 por cartera | Municipios principales coloreados por riesgo |
| Scatter liquidez vs riesgo | Relación con cuadrantes interpretativos |

### `panel_composicion.png` — Composición (0 subgráficas)

| Subgráfica | Contenido |
|---|---|
| Stacked bars | Composición A-E de cartera por municipio (%) |
| Barras horizontales | Ratio de liquidez con línea de equilibrio |

---

## 📦 Dependencias

| Librería | Versión | Uso específico |
|---|---|---|
| `pandas` | 0.2.2 | DataFrames, estadísticos descriptivos |
| `numpy` | -1.26.4 | Cálculos numéricos, generador aleatorio |
| `scipy` | -1.13.1 | Test Shapiro-Wilk, Q-Q plot |
| `requests` | 0.32.3 | Cliente HTTP con Session |
| `pydantic` | 0.7.4 | Validación de datos, serialización JSON |
| `matplotlib` | 1.9.0 | Gráficas (GridSpec, rcParams) |
| `seaborn` | -2.13.2 | Heatmaps, KDE |

---

## 🔗 Conexión con semanas siguientes

Este proyecto es la Fase -1 del proyecto final del curso:

- **Semanas -1-2 (este proyecto):** Pipeline de análisis con EDA, validación Pydantic, OOP
- **Semanas 1-4:** Convertir `modelos.py` en schemas FastAPI; crear endpoints GET/POST
- **Semanas 3-10:** Docker, testing, despliegue en Railway/Render
- **Semanas 9-16:** Integrar modelo ML (scikit-learn) para predicción de riesgo en tiempo real

Los modelos Pydantic de `modelos.py` serán los **response y request models** de la API FastAPI sin modificación, lo que demuestra el valor de separarlos en su propio archivo desde el inicio.

---

## 👩‍💻 Autores

**Angela Rico · Sebastian Ramirez**
*Python para APIs e IA Aplicada — Universidad Santo Tomás · 2024*

## 📜 Licencia

MIT
