"""
main.py — Punto de entrada de la API de Encuestas Poblacionales.

Arquitectura general:
─────────────────────────────────────────────────────────────────────────────
Framework: FastAPI (ASGI — Asynchronous Server Gateway Interface)
Almacenamiento: Diccionario en memoria (repositorio temporal para desarrollo)
Validación: Pydantic v2 + manejo centralizado de errores HTTP 422
─────────────────────────────────────────────────────────────────────────────

def vs async def en FastAPI (RF5 — Endpoint asíncrono):
─────────────────────────────────────────────────────────────────────────────
  def endpoint():
      FastAPI detecta que es síncrona y la ejecuta en un threadpool externo
      para no bloquear el event loop principal de asyncio. Es adecuado para
      operaciones CPU-intensivas o código legacy sin soporte async.

  async def endpoint():
      La función se ejecuta directamente en el event loop de asyncio con
      await. Ideal para operaciones I/O: consultas a base de datos, peticiones
      HTTP externas, lectura/escritura de archivos.
      Ejemplo práctico: await db.aggregate(pipeline) libera el event loop
      mientras espera la respuesta de MongoDB — miles de requests concurrentes
      con un solo proceso, sin threads adicionales.

ASGI vs WSGI:
─────────────────────────────────────────────────────────────────────────────
  WSGI (Flask, Django clásico):
      - Interfaz síncrona: 1 request = 1 thread bloqueado hasta respuesta.
      - Escalabilidad: horizontal (más procesos/threads).

  ASGI (FastAPI, Starlette, Django 3+):
      - Interfaz asíncrona: el event loop maneja múltiples conexiones sin
        bloqueo usando async/await y corutinas.
      - Soporta WebSockets, SSE, y HTTP/2 nativamente.
      - FastAPI usa Uvicorn/Hypercorn como servidor ASGI.
─────────────────────────────────────────────────────────────────────────────
"""

import io
import json
import logging
import pickle
import time
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from models import (
    EncuestaCompleta,
    Encuestado,
    EstadisticasEncuesta,
    RespuestaEncuesta,
)

# Importar endpoints del Censo 2018
from censo_endpoints import router as censo_router
from database import crear_tablas, engine

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de logging — auditoría de ingresos válidos e inválidos
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("encuesta_api")


# ─────────────────────────────────────────────────────────────────────────────
# Inicialización de FastAPI
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="API de Encuestas Poblacionales · Colombia",
    description="""
## Sistema de Validación y Gestión de Encuestas Poblacionales Colombianas

API REST desarrollada con **FastAPI + Pydantic v2** para la recolección, validación y
análisis estadístico de encuestas poblacionales y datos del **Censo Nacional 2018** del DANE.

---

## 📦 Módulo 1 — Encuestas (almacenamiento en memoria)

Gestiona encuestas poblacionales con validación estricta de dominio colombiano.

### Flujo de trabajo típico
1. `POST /encuestas/` — crear una encuesta manualmente
2. `POST /encuestas/upload-csv/` — cargar resultados desde Google Forms o CSV propio
3. `GET /encuestas/estadisticas/` — obtener resumen estadístico en tiempo real
4. `GET /encuestas/export/json/` o `.../pickle/` — exportar para análisis externo

### Modelo de datos: `EncuestaCompleta`

Cada encuesta contiene:
- **`encuestado`** — perfil demográfico del respondente:
  - `nombre` (str, 2-100 chars)
  - `edad` (int, 0-120) — axioma biológico
  - `genero` (Literal) — `masculino | femenino | no_binario | prefiero_no_decir`
  - `estrato` (int, 1-6) — clasificación socioeconómica DANE
  - `departamento` (str) — validado contra catálogo DANE DIVIPOLA (33 entidades)
  - `municipio` (str, 2-100 chars)
  - `nivel_educativo` (Literal) — `ninguno | primaria | secundaria | tecnico | universitario | posgrado | otro`
  - `ocupacion` (str, opcional)
- **`respuestas`** — lista de `RespuestaEncuesta`:
  - `pregunta_id` (int ≥ 1, único por encuesta)
  - `enunciado` (str, 5-500 chars)
  - `tipo_pregunta` (Literal) — `likert | porcentaje | texto_abierto | si_no`
  - `valor` — polimórfico según tipo:
    - `likert` → **int** en [1, 5]
    - `porcentaje` → **float** en [0.0, 100.0]
    - `si_no` → **str** `"si"` o `"no"`
    - `texto_abierto` → **str** no vacío
  - `observacion` (str, opcional, hasta 300 chars)
- **`observaciones_generales`** (str, opcional) — notas del levantamiento
- **`fuente`** — `"manual"`, `"csv_upload"`, `"google_forms"`
- **`id_encuesta`** — UUID asignado automáticamente por el servidor
- **`fecha_registro`** — timestamp ISO 8601 asignado por el servidor

### Validaciones automáticas (Pydantic v2)
| Campo | Regla | Motivo |
|-------|-------|--------|
| `edad` | 0–120 | Axioma biológico demográfico |
| `estrato` | 1–6 | Clasificación oficial DANE |
| `departamento` | Catálogo DANE | Integridad referencial regional |
| `likert` | 1–5 | Escala ordinal estándar |
| `porcentaje` | 0.0–100.0 | Escala de razón estadística |
| `pregunta_id` | Sin duplicados por encuesta | Consistencia interna |

### Normalización de departamento
El sistema acepta variaciones de escritura:
- `'ANTIOQUIA'`, `'antioquia'` → `'Antioquia'`
- `'Cordoba'` (sin tilde) → `'Córdoba'`
- `'bogota d.c.'` → `'Bogotá D.C.'`

### Errores HTTP retornados
- **201 Created** — encuesta creada exitosamente
- **200 OK** — consulta exitosa
- **204 No Content** — eliminación exitosa (sin cuerpo)
- **400 Bad Request** — archivo inválido o vacío
- **404 Not Found** — encuesta no encontrada por ID
- **422 Unprocessable Entity** — falla de validación Pydantic (con detalle por campo)

---

## 🏛️ Módulo 2 — Censo 2018 DANE (base de datos SQLite)

Carga y análisis de las bases de datos del **Censo Nacional de Población y Vivienda 2018**
publicadas por el DANE. Los archivos CSV originales contienen decenas de variables por persona.

### Arquitectura de persistencia
- **SQLite + SQLAlchemy 2.0 async** con `aiosqlite`
- Tabla `censo_2018_registros` con índices compuestos en columnas de alta consulta
- Procesamiento en lotes de **50.000 registros** para no saturar RAM

### Variables principales del CSV del DANE
| Variable | Descripción | Códigos |
|----------|-------------|---------|
| `U_DPTO` | Código departamento DIVIPOLA | 5=Antioquia, 11=Bogotá, 76=Valle... |
| `U_MPIO` | Código municipio DIVIPOLA | Varía por departamento |
| `P_SEXO` | Sexo | 1=Hombre, 2=Mujer |
| `P_EDADR` | Rango etario (código 1-21) | 1=00-04, 4=15-19, 13=60-64... |
| `PA1_GRP_ETNIC` | Grupo étnico | 1=Ninguno, 4=Afro, 6=Indígena... |
| `P_NIVEL_ANOSR` | Años de educación aprobados | 0-11, 99=Ignorado |
| `P_EST_CIVIL` | Estado civil | 1=Soltero, 2=Casado... |
| `P_TRABAJO` | Situación laboral | 0=No trabaja, 1-9=categorías |

### ⚠️ Nota sobre edad en el Censo 2018
El DANE **no registra edades individuales** — usa **rangos quinquenales** (código 1-21):
- Código 1 = 00-04 años
- Código 4 = 15-19 años
- Código 13 = 60-64 años
- Código 21 = 100+ años

Por esto, **no se calculan promedio/mediana de edad** en los endpoints — sería inventar datos
que no existen. En su lugar se muestran distribuciones por rangos DANE y grupos amplios.

### Índices demográficos implementados
- **Índice de masculinidad** = (Hombres / Mujeres) × 100
  - &gt;100: más hombres · =100: equilibrio · &lt;100: más mujeres
- **Índice de dependencia** = ((Población &lt;15 + Población &gt;64) / Población 15-64) × 100
  - &gt;60: alta presión · 40-60: equilibrio · &lt;40: baja presión

### Municipios — cruce con catálogo DIVIPOLA
Los endpoints muestran nombres oficiales de municipios cruzados con el catálogo DIVIPOLA del DANE,
no solo códigos numéricos. La distribución `distribucion_por_municipio` muestra los 15 municipios
con más registros con sus nombres completos.

---

## 🔧 Ejecución local
```bash
# Activar entorno virtual
.venv\\Scripts\\activate          # Windows
source .venv/bin/activate        # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
uvicorn main:app --reload --port 8001
```

**Interfaces disponibles:**
- Interfaz visual: `http://localhost:8001/ui`
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`
- Health check: `http://localhost:8001/`
    """,
    version="2.2.0",
    contact={
        "name": "Equipo de Desarrollo — Python para APIs e IA",
        "email": "dev@encuestas-co.edu",
    },
    license_info={"name": "MIT License"},
    openapi_tags=[
        {"name": "Encuestas", "description": "Operaciones CRUD sobre encuestas poblacionales"},
        {"name": "Upload/Export", "description": "Carga y descarga de archivos"},
        {"name": "Estadísticas", "description": "Análisis estadístico agregado"},
        {"name": "Censo 2018", "description": "Carga y análisis de bases del Censo 2018 DANE"},
        {"name": "Sistema", "description": "Health check y estado de la API"},
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# Incluir router del Censo 2018
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(censo_router)


# ─────────────────────────────────────────────────────────────────────────────
# CORS — permite que el frontend (servido desde /ui) haga fetch a la API
# sin restricciones de origen. En producción se restringiría a dominios
# específicos. Aquí lo dejamos abierto para desarrollo local.
# ─────────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Repositorio en memoria
# En producción este dict se reemplazaría por una conexión a base de datos
# (ej. Motor/AsyncPG con await), aprovechando el async del ASGI.
# ─────────────────────────────────────────────────────────────────────────────
db_encuestas: Dict[str, EncuestaCompleta] = {}


# ══════════════════════════════════════════════════════════════════════════════
# DECORADORES PERSONALIZADOS (RT5)
#
# Los decoradores de FastAPI (@app.get, @app.post) son funciones de orden
# superior que registran el callable en el router interno de Starlette.
# Son, en esencia, decoradores Python estándar con lógica de routing.
#
# Los decoradores personalizados aquí implementados siguen el mismo patrón:
# envuelven la función original añadiendo comportamiento transversal
# (cross-cutting concerns) sin modificar la lógica de negocio del endpoint.
# ══════════════════════════════════════════════════════════════════════════════

def log_request(func):
    """
    Decorador de auditoría — registra verbo HTTP, ruta y timestamp de cada request.

    Uso conceptual análogo a @app.get/@app.post: ambos son decoradores que
    añaden comportamiento sin tocar la función original. La diferencia es que
    los decoradores de FastAPI registran en el router, mientras que este
    añade logging transversal.

    Aplicable a: cualquier endpoint async que reciba `request: Request`.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Optional[Request] = kwargs.get("request")
        if request is not None and isinstance(request, Request):
            logger.info(
                f"REQUEST  | {request.method:<7} {request.url.path} "
                f"| {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        return await func(*args, **kwargs)
    return wrapper


def timer(func):
    """
    Decorador de métricas — mide y registra el tiempo de ejecución del endpoint.

    Escenario práctico donde es esencial: el endpoint /estadisticas/ agrega
    datos de potencialmente miles de encuestas. En producción, esta métrica
    alimentaría un sistema APM (Application Performance Monitoring) para
    detectar degradación de rendimiento antes de que impacte al usuario.

    El tiempo se mide con perf_counter (alta resolución, no afectado por NTP).
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        t_inicio = time.perf_counter()
        resultado = await func(*args, **kwargs)
        duracion_ms = (time.perf_counter() - t_inicio) * 1000
        logger.info(f"TIMER    | {func.__name__:<35} | {duracion_ms:7.2f} ms")
        return resultado
    return wrapper


# ══════════════════════════════════════════════════════════════════════════════
# MANEJO CENTRALIZADO DE ERRORES HTTP 422 (RF4)
#
# FastAPI lanza RequestValidationError cuando Pydantic rechaza el payload.
# Este handler intercepta la excepción y construye una respuesta JSON
# estructurada y legible, muy superior al mensaje crudo de Pydantic.
# ══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(RequestValidationError)
async def manejador_error_validacion(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handler centralizado para errores de validación HTTP 422.

    Transforma los errores internos de Pydantic en una respuesta JSON
    estructurada y comprensible para cualquier consumidor de la API.
    Cada campo inválido se reporta con su ruta, el mensaje de error,
    el tipo de fallo, y el valor que fue rechazado.

    Además registra en el log de auditoría cada intento de ingesta inválida,
    permitiendo detectar patrones de error sistemáticos en los formularios.
    """
    errores_formateados = []
    for error in exc.errors():
        # Construir ruta legible del campo (ej. "body → encuestado → edad")
        ruta_campo = " → ".join(str(loc) for loc in error.get("loc", []))
        errores_formateados.append(
            {
                "campo": ruta_campo,
                "mensaje": error.get("msg", "Error de validación desconocido"),
                "tipo_error": error.get("type", "unknown"),
                "valor_recibido": str(error.get("input", "N/A"))[:150],
            }
        )

    # Auditoría: log de cada intento inválido
    logger.warning(
        f"INGESTA INVÁLIDA | {request.method} {request.url.path} | "
        f"{len(errores_formateados)} error(es) detectados"
    )
    for err in errores_formateados:
        logger.warning(f"  └─ [{err['campo']}] {err['mensaje']}")

    return JSONResponse(
        status_code=422,
        content={
            "codigo_http": 422,
            "error": "Error de Validación de Datos",
            "descripcion": (
                "Los datos enviados no cumplen las restricciones estadísticas "
                "y de formato requeridas por el sistema."
            ),
            "total_errores": len(errores_formateados),
            "detalle_errores": errores_formateados,
            "sugerencia": (
                "Revise cada campo indicado. Consulte /docs para ver los "
                "esquemas JSON válidos con ejemplos para cada endpoint."
            ),
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS REST (RF3)
# CRUD completo + estadísticas + health check
# ══════════════════════════════════════════════════════════════════════════════

@app.post(
    "/encuestas/",
    response_model=EncuestaCompleta,
    status_code=201,
    tags=["Encuestas"],
    summary="Registrar nueva encuesta",
    description=(
        "Recibe, valida y almacena una encuesta poblacional completa.\n\n"
        "**Campos obligatorios del encuestado:** `nombre`, `edad`, `genero`, `estrato`, "
        "`departamento`, `municipio`, `nivel_educativo`.\n\n"
        "**Campos obligatorios de cada respuesta:** `pregunta_id` (único por encuesta), "
        "`enunciado` (mín. 5 chars), `tipo_pregunta`, `valor` (validado por tipo).\n\n"
        "**Asignados automáticamente por el servidor:**\n"
        "- `id_encuesta` — UUID v4 único, imposible de predecir ni falsificar\n"
        "- `fecha_registro` — timestamp UTC ISO 8601 del momento de registro\n\n"
        "**Validaciones que generan HTTP 422:**\n"
        "- `edad` fuera de [0, 120]\n"
        "- `estrato` fuera de [1, 6]\n"
        "- `departamento` no existe en catálogo DANE (acepta variaciones sin tilde/mayúsculas)\n"
        "- `tipo_pregunta = 'likert'` con valor fuera de [1, 5]\n"
        "- `tipo_pregunta = 'porcentaje'` con valor fuera de [0.0, 100.0]\n"
        "- `tipo_pregunta = 'si_no'` con valor distinto de `'si'`/`'no'`\n"
        "- `pregunta_id` duplicado dentro de la misma encuesta\n\n"
        "**Retorna:** `201 Created` con el objeto `EncuestaCompleta` completo incluido el UUID."
    ),
)
@log_request
async def crear_encuesta(
    request: Request, encuesta: EncuestaCompleta
) -> EncuestaCompleta:
    """Registra una nueva encuesta. Retorna 201 Created con el objeto completo."""
    db_encuestas[encuesta.id_encuesta] = encuesta
    logger.info(
        f"CREADA   | ID: {encuesta.id_encuesta} | "
        f"Encuestado: {encuesta.encuestado.nombre} | "
        f"Respuestas: {len(encuesta.respuestas)}"
    )
    return encuesta


@app.get(
    "/encuestas/",
    response_model=List[EncuestaCompleta],
    status_code=200,
    tags=["Encuestas"],
    summary="Listar todas las encuestas",
    description=(
        "Retorna el listado completo de encuestas almacenadas en memoria.\n\n"
        "**Paginación (query params):**\n"
        "- `skip` (int, default 0) — número de registros a saltar (offset)\n"
        "- `limit` (int, default 100) — máximo de registros a retornar\n\n"
        "**Ejemplo:** `GET /encuestas/?skip=10&limit=5` retorna las encuestas 11-15.\n\n"
        "**Nota:** El almacenamiento es **en memoria** — los datos se pierden al reiniciar "
        "el servidor. Use `/encuestas/export/json/` para persistir antes de reiniciar.\n\n"
        "**Retorna:** `200 OK` con array de `EncuestaCompleta` (puede ser vacío `[]`)."
    ),
)
@log_request
async def listar_encuestas(
    request: Request,
    skip: int = 0,
    limit: int = 100,
) -> List[EncuestaCompleta]:
    """Lista encuestas con paginación opcional. Retorna 200 OK."""
    todas = list(db_encuestas.values())
    return todas[skip: skip + limit]


@app.get(
    "/encuestas/estadisticas/",
    response_model=EstadisticasEncuesta,
    status_code=200,
    tags=["Estadísticas"],
    summary="Estadísticas agregadas del repositorio de encuestas",
    description=(
        "Genera un resumen estadístico en tiempo real sobre todas las encuestas en memoria.\n\n"
        "**Campos retornados:**\n"
        "- `total_encuestas` — conteo total de encuestas registradas\n"
        "- `edad_promedio` — media aritmética de edades (float, 2 decimales)\n"
        "- `edad_minima` / `edad_maxima` — rango observado de edades\n"
        "- `distribucion_por_estrato` — frecuencia por estrato (`{'Estrato 1': 5, ...}`)\n"
        "- `distribucion_por_departamento` — frecuencia por departamento, ordenada descendente\n"
        "- `distribucion_por_genero` — frecuencia por género\n"
        "- `distribucion_por_nivel_educativo` — frecuencia por nivel educativo\n"
        "- `promedio_respuestas_por_encuesta` — promedio de preguntas por encuesta\n\n"
        "**Si no hay encuestas:** retorna todos los campos en 0 o `{}`, nunca lanza 404.\n\n"
        "**Por qué `async def`:** en producción este endpoint consultaría una base de datos "
        "con `await db.aggregate(...)`. Con `async/await`, el event loop atiende otros "
        "requests mientras espera la BD — miles de requests concurrentes con un solo proceso."
    ),
)
@timer
@log_request
async def obtener_estadisticas(request: Request) -> EstadisticasEncuesta:
    """
    Endpoint implementado como async def (RF5).

    Por qué async aquí es la elección correcta:
    En un entorno productivo, este endpoint consultaría una base de datos
    con una consulta de agregación (ej. MongoDB Atlas $group, PostgreSQL GROUP BY).
    Con async/await, la corutina cede el control al event loop mientras espera
    la respuesta de la BD. Esto permite que el servidor atienda otros requests
    simultáneamente sin bloquear — esencial en APIs de alto tráfico.

    ASGI + Uvicorn habilita este comportamiento: el servidor web implementa
    la interfaz ASGI que el event loop de asyncio entiende nativamente.
    """
    if not db_encuestas:
        return EstadisticasEncuesta(
            total_encuestas=0,
            edad_promedio=0.0,
            edad_minima=0,
            edad_maxima=0,
            distribucion_por_estrato={},
            distribucion_por_departamento={},
            distribucion_por_genero={},
            distribucion_por_nivel_educativo={},
            promedio_respuestas_por_encuesta=0.0,
        )

    encuestas = list(db_encuestas.values())
    edades = [e.encuestado.edad for e in encuestas]

    # Distribuciones por variables categóricas
    dist_estrato: Dict[str, int] = {}
    dist_departamento: Dict[str, int] = {}
    dist_genero: Dict[str, int] = {}
    dist_educativo: Dict[str, int] = {}

    for enc in encuestas:
        # Estrato con etiqueta descriptiva
        clave_estrato = f"Estrato {enc.encuestado.estrato}"
        dist_estrato[clave_estrato] = dist_estrato.get(clave_estrato, 0) + 1

        dept = enc.encuestado.departamento
        dist_departamento[dept] = dist_departamento.get(dept, 0) + 1

        gen = enc.encuestado.genero
        dist_genero[gen] = dist_genero.get(gen, 0) + 1

        edu = enc.encuestado.nivel_educativo
        dist_educativo[edu] = dist_educativo.get(edu, 0) + 1

    return EstadisticasEncuesta(
        total_encuestas=len(encuestas),
        edad_promedio=round(sum(edades) / len(edades), 2),
        edad_minima=min(edades),
        edad_maxima=max(edades),
        distribucion_por_estrato=dict(sorted(dist_estrato.items())),
        distribucion_por_departamento=dict(
            sorted(dist_departamento.items(), key=lambda x: x[1], reverse=True)
        ),
        distribucion_por_genero=dist_genero,
        distribucion_por_nivel_educativo=dist_educativo,
        promedio_respuestas_por_encuesta=round(
            sum(len(e.respuestas) for e in encuestas) / len(encuestas), 2
        ),
    )


@app.get(
    "/encuestas/{id_encuesta}",
    response_model=EncuestaCompleta,
    status_code=200,
    tags=["Encuestas"],
    summary="Obtener encuesta por ID",
    description=(
        "Recupera una encuesta específica por su UUID.\n\n"
        "**Path param:** `id_encuesta` — UUID v4 completo (ej: `3fa85f64-5717-4562-b3fc-2c963f66afa6`).\n\n"
        "**Respuestas:**\n"
        "- `200 OK` — objeto `EncuestaCompleta` completo\n"
        "- `404 Not Found` — el UUID no existe en el repositorio. "
        "Use `GET /encuestas/` para obtener los IDs disponibles.\n\n"
        "**Tip:** Los IDs se obtienen de la respuesta del `POST /encuestas/` "
        "o del listado `GET /encuestas/`."
    ),
)
@log_request
async def obtener_encuesta(
    request: Request, id_encuesta: str
) -> EncuestaCompleta:
    """Busca y retorna una encuesta por su ID único."""
    if id_encuesta not in db_encuestas:
        logger.warning(f"NO ENCONTRADA | ID: {id_encuesta}")
        raise HTTPException(
            status_code=404,
            detail=f"Encuesta con ID '{id_encuesta}' no encontrada. "
                   f"Use GET /encuestas/ para ver los IDs disponibles.",
        )
    return db_encuestas[id_encuesta]


@app.put(
    "/encuestas/{id_encuesta}",
    response_model=EncuestaCompleta,
    status_code=200,
    tags=["Encuestas"],
    summary="Actualizar encuesta existente (reemplazo total)",
    description=(
        "Reemplaza **completamente** los datos de una encuesta existente (PUT semántico).\n\n"
        "**Comportamiento:**\n"
        "- El `id_encuesta` del path tiene precedencia — el del body se ignora\n"
        "- El `fecha_registro` se actualiza al momento del PUT\n"
        "- Aplica todas las mismas validaciones Pydantic que el `POST /encuestas/`\n\n"
        "**Diferencia PUT vs PATCH:** PUT reemplaza el recurso completo. "
        "Si omite un campo opcional, quedará como `null`. "
        "No existe PATCH en esta API — use PUT con el objeto completo.\n\n"
        "**Respuestas:**\n"
        "- `200 OK` — encuesta actualizada con el objeto completo\n"
        "- `404 Not Found` — UUID no existe\n"
        "- `422 Unprocessable Entity` — falla de validación en el body"
    ),
)
@log_request
async def actualizar_encuesta(
    request: Request,
    id_encuesta: str,
    encuesta_actualizada: EncuestaCompleta,
) -> EncuestaCompleta:
    """Actualiza una encuesta existente preservando su ID original."""
    if id_encuesta not in db_encuestas:
        raise HTTPException(
            status_code=404,
            detail=f"Encuesta con ID '{id_encuesta}' no encontrada.",
        )
    # Preservar ID original; el servidor controla la identidad del recurso
    encuesta_actualizada.id_encuesta = id_encuesta
    encuesta_actualizada.fecha_registro = datetime.now()
    db_encuestas[id_encuesta] = encuesta_actualizada
    logger.info(f"ACTUALIZADA | ID: {id_encuesta}")
    return encuesta_actualizada


@app.delete(
    "/encuestas/{id_encuesta}",
    status_code=204,
    tags=["Encuestas"],
    summary="Eliminar encuesta",
    description=(
        "Elimina permanentemente una encuesta del repositorio en memoria.\n\n"
        "**Respuestas:**\n"
        "- `204 No Content` — eliminación exitosa. La respuesta **no tiene cuerpo** "
        "(esto es estándar HTTP: 204 significa éxito sin contenido).\n"
        "- `404 Not Found` — el UUID no existe en el repositorio.\n\n"
        "**⚠️ Irreversible:** una vez eliminada no hay forma de recuperar la encuesta. "
        "Si necesita respaldo, exporte primero con `GET /encuestas/export/json/`."
    ),
)
@log_request
async def eliminar_encuesta(request: Request, id_encuesta: str):
    """Elimina una encuesta. Retorna 204 No Content (sin cuerpo de respuesta)."""
    if id_encuesta not in db_encuestas:
        raise HTTPException(
            status_code=404,
            detail=f"Encuesta con ID '{id_encuesta}' no encontrada.",
        )
    del db_encuestas[id_encuesta]
    logger.info(f"ELIMINADA   | ID: {id_encuesta}")
    return None  # 204 No Content — la respuesta no lleva cuerpo


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS UPLOAD CSV (Funcionalidad extra para Google Forms)
# ══════════════════════════════════════════════════════════════════════════════

@app.post(
    "/encuestas/debug-columns/",
    tags=["Upload/Export"],
    summary="Debug: Ver columnas detectadas en CSV (sin cargar datos)",
    description=(
        "Analiza un CSV y retorna el mapeo de columnas detectadas **sin insertar datos**.\n\n"
        "Útil para diagnosticar por qué un CSV no se procesa correctamente antes de cargarlo.\n\n"
        "**Retorna:**\n"
        "- `columnas_originales` — lista de nombres exactos de columnas en el CSV\n"
        "- `columnas_normalizadas` — versión en minúsculas para comparación interna\n"
        "- `detecciones` — mapa `campo → columna_detectada` (o `null` si no se encontró)\n"
        "  - Campos buscados: `nombre`, `edad`, `genero`, `estrato`, `departamento`, "
        "`municipio`, `educacion`, `ocupacion`\n"
        "- `columnas_no_detectadas` — columnas del CSV que no se mapearon a ningún campo\n\n"
        "**Variaciones aceptadas por campo (ejemplos):**\n"
        "- `nombre`: `nombre`, `nombres`, `nombre completo`, `full name`\n"
        "- `edad`: `edad`, `edad (años)`, `age`, `¿cuántos años tienes?`\n"
        "- `genero`: `genero`, `género`, `sexo`, `gender`\n"
        "- `departamento`: `departamento`, `depto`, `department`, `state`"
    ),
    status_code=200,
)
async def debug_columns(request: Request, file: UploadFile = File(...)) -> dict:
    """Endpoint de debug para ver qué columnas detecta el sistema."""
    if not file.filename.lower().endswith('.csv'):
        return {"error": "Solo archivos CSV"}

    contenido = await file.read()
    df = pd.read_csv(io.BytesIO(contenido), encoding='utf-8-sig', nrows=0)

    columnas_originales = list(df.columns)
    columnas_normalizadas = {str(c).lower().strip(): c for c in df.columns}

    # Función auxiliar para buscar columna
    def buscar_columna(variaciones):
        for v in variaciones:
            if v in columnas_normalizadas:
                return columnas_normalizadas[v]
        return None

    # Detectar columnas demográficas
    detecciones = {
        'nombre': buscar_columna(['nombre', 'nombres', 'nombre completo']),
        'edad': buscar_columna(['edad', 'edad (años)', 'edad en años']),
        'genero': buscar_columna(['genero', 'género', 'sexo']),
        'estrato': buscar_columna(['estrato', 'estrato socioeconomico']),
        'departamento': buscar_columna(['departamento', 'depto', 'departamento/provincia']),
        'municipio': buscar_columna(['municipio', 'ciudad', 'municipio o ciudad']),
        'educacion': buscar_columna(['nivel_educativo', 'educacion', 'educación', 'escolaridad']),
        'ocupacion': buscar_columna(['ocupacion', 'ocupación', 'trabajo', 'empleo']),
    }

    return {
        'archivo': file.filename,
        'total_columnas': len(columnas_originales),
        'columnas_originales': columnas_originales,
        'columnas_normalizadas': list(columnas_normalizadas.keys()),
        'detecciones': detecciones,
        'columnas_no_detectadas': [c for c in columnas_originales if str(c).lower().strip() not in [v for v in detecciones.values() if v]]
    }


@app.post(
    "/encuestas/upload-csv/",
    tags=["Upload/Export"],
    summary="Cargar encuestas desde archivo CSV (Google Forms o propio)",
    description=(
        "Procesa un archivo `.csv` y crea encuestas a partir de sus filas.\n\n"
        "**Filosofía:** tolerante a errores — filas inválidas se saltan individualmente, "
        "el resto del archivo continúa procesándose.\n\n"
        "**Detección automática de columnas** (acepta variaciones de nombre):\n"
        "- Requeridas: `nombre`/`nombres`/`full name`, `edad`/`age`, `departamento`/`department`\n"
        "- Opcionales: `genero`/`sexo`, `estrato`, `municipio`/`ciudad`, "
        "`nivel_educativo`/`educacion`, `ocupacion`/`trabajo`\n"
        "- Respuestas: **cualquier otra columna** se trata como pregunta automáticamente\n\n"
        "**Detección automática de tipo de respuesta:**\n"
        "- Valor entero 1-5 → `likert`\n"
        "- Valor numérico 0-100 → `porcentaje`\n"
        "- Texto `si`/`sí`/`no` → `si_no`\n"
        "- Cualquier otro texto → `texto_abierto`\n\n"
        "**Motivos de fila saltada:**\n"
        "- Columna `nombre` o `edad` no encontrada en el CSV\n"
        "- Departamento no reconocible en catálogo DANE\n"
        "- Nombre o municipio que son números puros\n"
        "- Fila sin ninguna respuesta válida\n\n"
        "**Retorna:**\n"
        "- `exitosos` — encuestas creadas\n"
        "- `fallidos` — filas saltadas\n"
        "- `errores` — hasta 20 mensajes descriptivos del motivo de cada fallo\n"
        "- `ids_creados` — primeros 10 UUIDs generados\n\n"
        "**Tip:** use primero `POST /encuestas/debug-columns/` para verificar el mapeo."
    ),
    status_code=200,
)
@log_request
async def upload_csv(request: Request, file: UploadFile = File(...)) -> dict:
    """
    Procesa archivo CSV de Google Forms y carga encuestas.

    CARACTERÍSTICAS:
    - Mapeo FLEXIBLE de columnas (acepta variaciones de nombres)
    - Tolerante a errores: filas inválidas se saltan, no se rechaza todo el archivo
    - Valores por defecto para campos opcionales inválidos

    Columnas detectadas automáticamente (variaciones aceptadas):
    - Demográficas: nombre, edad, genero/género, estrato, departamento, municipio, educacion, ocupacion
    - Respuestas: Cualquier otra columna numérica o de texto

    Retorna el número de encuestas procesadas exitosamente y errores por fila.
    """
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use solo archivos .csv")

    contenido = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(contenido), encoding='utf-8-sig')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="El archivo CSV está vacío")

    logger.info(f"UPLOAD CSV | Archivo: {file.filename} | Filas: {len(df)} | Columnas: {list(df.columns)}")

    # DEBUG: Mostrar mapeo de columnas encontradas
    col_map_debug = {str(c).lower().strip(): c for c in df.columns}
    logger.info(f"UPLOAD CSV | Columnas normalizadas: {list(col_map_debug.keys())}")

    ids_creados = []
    errores = []
    filas_saltadas = []

    for idx, row in df.iterrows():
        try:
            # ═══════════════════════════════════════════════════════════════════════════════
            # MAPEO FLEXIBLE DE COLUMNAS (acepta variaciones de Google Forms)
            # ═══════════════════════════════════════════════════════════════════════════════
            col_map = {str(c).lower().strip(): c for c in df.columns}

            # Función auxiliar para buscar columna con variaciones
            def buscar_columna(variaciones):
                for v in variaciones:
                    if v in col_map:
                        return col_map[v]
                return None

            # Mapeo con múltiples variaciones por campo (incluye formatos de Google Forms)
            nombre_col = buscar_columna([
                'nombre', 'nombres', 'nombre completo', '¿nombre?', 'nombre del encuestado',
                'nombre completo:', 'full name', 'name'
            ])
            edad_col = buscar_columna([
                'edad', 'edad (años)', '¿edad?', 'años', 'edad en años', 'age',
                'edad (en años)', 'age (years)', '¿cuántos años tienes?'
            ])
            genero_col = buscar_columna([
                'genero', 'género', 'sexo', '¿género?', '¿sexo?', 'gender', 'sex',
                'género/sexo', 'gender/sex', '¿con qué género te identificas?'
            ])
            estrato_col = buscar_columna([
                'estrato', 'estrato socioeconomico', 'estrato socioeconómico', '¿estrato?',
                'estrato (clasificación de vivienda)', 'socioeconomic stratum', 'stratum',
                'estrato socioeconómico (clasificación de vivienda)'
            ])
            depto_col = buscar_columna([
                'departamento', 'depto', '¿departamento?', 'departamento de residencia',
                'department', 'state', 'region', '¿en qué departamento vives?',
                'departamento/provincia de residencia', 'departamento/provincia'
            ])
            municipio_col = buscar_columna([
                'municipio', 'ciudad', '¿municipio?', '¿ciudad de residencia?', 'city',
                'town', 'municipality', '¿dónde vives?', 'ciudad/municipio',
                'municipio o ciudad de residencia', 'municipio/ciudad'
            ])
            edu_col = buscar_columna([
                'nivel_educativo', 'educacion', 'educación', 'escolaridad', 'nivel educativo',
                '¿nivel educativo?', 'education level', 'education', 'schooling',
                '¿cuál es tu nivel de educación?', 'máximo nivel de estudios',
                'nivel educativo máximo alcanzado', 'nivel educativo maximo alcanzado'
            ])
            ocupacion_col = buscar_columna([
                'ocupacion', 'ocupación', 'trabajo', 'empleo', '¿ocupación?', 'actividad económica',
                'occupation', 'job', 'work', '¿a qué se dedica?', 'ocupación actual',
                'ocupación actual (describa brevemente su rol principal)', 'ocupacion actual'
            ])

            # ═══════════════════════════════════════════════════════════════════════════════
            # VALIDACIÓN DE CAMPOS REQUERIDOS (mínimos para crear encuesta)
            # ═══════════════════════════════════════════════════════════════════════════════
            if not nombre_col:
                errores.append({"fila": idx + 1, "error": "No se encontró columna de nombre. Columnas disponibles: " + ", ".join(df.columns[:5])})
                filas_saltadas.append(idx + 1)
                continue

            if not edad_col:
                errores.append({"fila": idx + 1, "error": "No se encontró columna de edad. Columnas disponibles: " + ", ".join(df.columns[:5])})
                filas_saltadas.append(idx + 1)
                continue

            # ═══════════════════════════════════════════════════════════════════════════════
            # PARSEO DE VALORES CON VALIDACIÓN ESTRICTA
            # ═══════════════════════════════════════════════════════════════════════════════
            # Nombre (validación estricta - no aceptar números puros)
            nombre_raw = row.get(nombre_col, "")
            try:
                nombre = str(nombre_raw).strip()
                # Validar que no sea un número puro (ej: "23", "24")
                if nombre.isdigit() or (len(nombre) < 3 and nombre.isnumeric()):
                    errores.append({"fila": idx + 1, "error": f"Nombre inválido: '{nombre}' parece ser un número"})
                    filas_saltadas.append(idx + 1)
                    continue
                if len(nombre) < 2:
                    nombre = f"Encuestado Fila {idx + 1}"  # Fallback si nombre muy corto
            except (ValueError, AttributeError, TypeError):
                nombre = f"Encuestado Fila {idx + 1}"

            # Edad (con fallback a valor por defecto si es inválida)
            edad_raw = row.get(edad_col, "")
            try:
                edad = int(float(str(edad_raw).replace(",", ".")))
                if edad < 0 or edad > 120:
                    logger.warning(f"Fila {idx + 1}: Edad {edad} fuera de rango, usando 30 como default")
                    edad = 30  # Fallback para edad inválida
            except (ValueError, TypeError):
                logger.warning(f"Fila {idx + 1}: Edad '{edad_raw}' no es número, usando 30 como default")
                edad = 30

            # Género (con fallback)
            genero_raw = str(row.get(genero_col, "prefiero_no_decir") if genero_col else "prefiero_no_decir").strip().lower()
            genero_map = {
                "m": "masculino", "masculino": "masculino", "hombre": "masculino", "varon": "masculino", "varón": "masculino",
                "f": "femenino", "femenino": "femenino", "mujer": "femenino", "dama": "femenino",
                "no_binario": "no_binario", "no binario": "no_binario", "nb": "no_binario",
                "prefiero_no_decir": "prefiero_no_decir", "prefiero no decir": "prefiero_no_decir", "no responde": "prefiero_no_decir",
            }
            genero = genero_map.get(genero_raw, "prefiero_no_decir")

            # Estrato (con fallback a 3 si es inválido)
            estrato_raw = row.get(estrato_col, "3") if estrato_col else "3"
            try:
                estrato = int(float(str(estrato_raw).replace(",", ".")))
                if estrato < 1 or estrato > 6:
                    logger.warning(f"Fila {idx + 1}: Estrato {estrato} fuera de rango, usando 3 como default")
                    estrato = 3
            except (ValueError, TypeError):
                estrato = 3

            # Departamento (con validación DANE - si no es válido, se salta la fila)
            depto_raw = str(row.get(depto_col, "") if depto_col else "").strip()
            if not depto_col or not depto_raw:
                errores.append({"fila": idx + 1, "error": "Departamento no especificado"})
                filas_saltadas.append(idx + 1)
                continue
            try:
                from validators import validar_departamento
                departamento = validar_departamento(depto_raw)
            except Exception as e:
                errores.append({"fila": idx + 1, "error": f"Departamento inválido: '{depto_raw}'. {str(e)[:100]}"})
                filas_saltadas.append(idx + 1)
                continue

            # Municipio (validación estricta - no aceptar números puros)
            municipio_raw = str(row.get(municipio_col, "") if municipio_col else "").strip()
            if municipio_raw.isdigit() or (len(municipio_raw) < 3 and municipio_raw.isnumeric()):
                errores.append({"fila": idx + 1, "error": f"Municipio inválido: '{municipio_raw}' parece ser un número"})
                filas_saltadas.append(idx + 1)
                continue
            municipio = municipio_raw if len(municipio_raw) >= 2 else "Desconocido"

            # Nivel educativo (con validación estricta)
            nivel_raw = str(row.get(edu_col, "") if edu_col else "").strip().lower()
            if not nivel_raw:
                nivel_educativo = "otro"
            else:
                nivel_map = {
                    "ninguno": "ninguno", "primaria": "primaria", "secundaria": "secundaria",
                    "tecnico": "tecnico", "técnico": "tecnico", "universitario": "universitario",
                    "posgrado": "posgrado", "postgrado": "posgrado", "pregrado": "universitario",
                    "doctorado": "posgrado", "maestria": "posgrado", "maestría": "posgrado",
                    "bachiller": "secundaria", "basica": "primaria", "básica": "primaria",
                }
                # Si el valor es un número puro, es inválido
                if nivel_raw.isdigit() or nivel_raw.replace(".", "").isdigit():
                    errores.append({"fila": idx + 1, "error": f"Nivel educativo inválido: '{nivel_raw}' parece ser un número"})
                    filas_saltadas.append(idx + 1)
                    continue
                nivel_educativo = nivel_map.get(nivel_raw, "otro")

            # Ocupación (validación estricta - no aceptar números puros)
            ocupacion_raw = str(row.get(ocupacion_col, "") if ocupacion_col else "").strip()
            if ocupacion_raw and (ocupacion_raw.isdigit() or (len(ocupacion_raw) < 4 and ocupacion_raw.isnumeric())):
                errores.append({"fila": idx + 1, "error": f"Ocupación inválida: '{ocupacion_raw}' parece ser un número"})
                filas_saltadas.append(idx + 1)
                continue
            ocupacion = ocupacion_raw if ocupacion_raw and ocupacion_raw.lower() not in ("ninguno", "ninguna", "n/a", "no aplica") else None

            # ═══════════════════════════════════════════════════════════════════════════════
            # CONSTRUCCIÓN DE RESPUESTAS (columnas restantes, tolerante a errores)
            # ═══════════════════════════════════════════════════════════════════════════════
            respuestas = []
            pregunta_id = 1
            skip_cols = {nombre_col, edad_col, genero_col, estrato_col, depto_col, municipio_col, edu_col, ocupacion_col}
            respuestas_saltadas = []

            for col in df.columns:
                if col in skip_cols:
                    continue

                valor_raw = row.get(col)
                if pd.isna(valor_raw):
                    continue  # Saltar valores vacíos

                try:
                    # Determinar tipo de pregunta basado en el valor
                    if isinstance(valor_raw, (int, float)):
                        # Verificar si es entero o float
                        es_entero = isinstance(valor_raw, int) or (isinstance(valor_raw, float) and valor_raw.is_integer())

                        if 1 <= valor_raw <= 5:
                            tipo = "likert"
                            # Likert requiere int, convertir si es float entero
                            val = int(valor_raw) if es_entero else float(valor_raw)
                        elif 0 <= valor_raw <= 100:
                            tipo = "porcentaje"
                            val = float(valor_raw)
                        else:
                            tipo = "numerico"
                            val = float(valor_raw)
                    elif isinstance(valor_raw, str):
                        valor_str = valor_raw.strip().lower()
                        if valor_str in ('si', 'sí', 'no'):
                            tipo = "si_no"
                            val = "si" if valor_str in ('si', 'sí') else "no"
                        elif len(valor_str) > 0:
                            tipo = "texto_abierto"
                            val = valor_raw.strip()
                        else:
                            continue  # Saltar string vacío
                    else:
                        continue

                    respuestas.append({
                        "pregunta_id": pregunta_id,
                        "enunciado": str(col),
                        "tipo_pregunta": tipo,
                        "valor": val,
                    })
                    pregunta_id += 1

                except Exception as e:
                    # Si una respuesta falla, se registra pero no detiene el proceso
                    respuestas_saltadas.append(f"Columna '{col}': {str(e)}")
                    continue

            # Si no hay respuestas válidas, saltar la fila
            if not respuestas:
                errores.append({"fila": idx + 1, "error": f"No se encontraron respuestas válidas. Columnas saltadas: {respuestas_saltadas[:3]}"})
                filas_saltadas.append(idx + 1)
                continue

            # ═══════════════════════════════════════════════════════════════════════════════
            # CREAR ENCUESTA (con validación Pydantic)
            # ═══════════════════════════════════════════════════════════════════════════════
            try:
                encuesta = EncuestaCompleta(
                    encuestado={
                        "nombre": nombre,
                        "edad": edad,
                        "genero": genero,
                        "estrato": estrato,
                        "departamento": departamento,
                        "municipio": municipio,
                        "nivel_educativo": nivel_educativo,
                        "ocupacion": ocupacion,
                    },
                    respuestas=respuestas,
                    observaciones_generales=f"[Upload CSV] Archivo: {file.filename}, Fila: {idx + 1}" + (f" | Respuestas saltadas: {len(respuestas_saltadas)}" if respuestas_saltadas else ""),
                    fuente="csv_upload",
                )
                db_encuestas[encuesta.id_encuesta] = encuesta
                ids_creados.append(encuesta.id_encuesta)

            except Exception as e:
                # Si la validación Pydantic falla, registrar error detallado
                errores.append({"fila": idx + 1, "error": f"Validación fallida: {str(e)[:200]}"})
                filas_saltadas.append(idx + 1)

        except Exception as e:
            # Error catastrófico en la fila (no debería pasar, pero por si acaso)
            errores.append({"fila": idx + 1, "error": f"Error inesperado: {str(e)[:200]}"})
            filas_saltadas.append(idx + 1)

    logger.info(f"UPLOAD CSV COMPLETADO | Exitosos: {len(ids_creados)} | Saltadas: {len(filas_saltadas)}")

    return {
        "mensaje": f"Procesamiento completado. {len(ids_creados)} encuestas creadas, {len(filas_saltadas)} filas saltadas.",
        "total_procesados": len(df),
        "exitosos": len(ids_creados),
        "fallidos": len(filas_saltadas),
        "errores": errores[:20],  # Máximo 20 errores para no saturar la respuesta
        "ids_creados": ids_creados[:10],  # Máximo 10 IDs
        "filas_saltadas": filas_saltadas[:20],  # Máximo 20 filas saltadas
    }


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS EXPORT (Bonificación +0.1 JSON vs Pickle)
# ══════════════════════════════════════════════════════════════════════════════

@app.get(
    "/encuestas/export/json/",
    tags=["Upload/Export"],
    summary="Exportar todas las encuestas a JSON",
    description=(
        "Descarga todas las encuestas del repositorio en un archivo `encuestas.json`.\n\n"
        "**Formato de respuesta:** `StreamingResponse` con `Content-Type: application/json` "
        "y header `Content-Disposition: attachment; filename=encuestas.json`.\n\n"
        "**Estructura del JSON:** array de objetos `EncuestaCompleta`. "
        "El campo `fecha_registro` se serializa como string ISO 8601 "
        "(ej: `'2025-03-25T10:30:00.123456'`).\n\n"
        "**JSON vs Pickle:**\n"
        "- ✅ JSON: texto plano, legible por humanos, interoperable con cualquier lenguaje "
        "(Python, R, JavaScript, Excel Power Query). Ideal para compartir o archivar.\n"
        "- ⚠️ Pickle: binario Python-only, no legible por humanos, más rápido para "
        "recargar en Python, pero riesgo de seguridad si la fuente no es confiable.\n\n"
        "**404** si no hay encuestas registradas."
    ),
)
async def export_json(request: Request):
    """
    Exporta todas las encuestas a JSON.

    JSON es un formato de texto plano, legible por humanos, interoperable
    con cualquier lenguaje de programación. Ideal para intercambio de datos
    y almacenamiento a largo plazo.
    """
    if not db_encuestas:
        raise HTTPException(status_code=404, detail="No hay encuestas para exportar")

    encuestas_data = []
    for enc in db_encuestas.values():
        enc_dict = enc.model_dump()
        enc_dict['fecha_registro'] = enc_dict['fecha_registro'].isoformat() if enc_dict['fecha_registro'] else None
        encuestas_data.append(enc_dict)

    json_bytes = io.BytesIO(json.dumps(encuestas_data, indent=2, ensure_ascii=False).encode('utf-8'))
    
    headers = {"Content-Disposition": "attachment; filename=encuestas.json"}
    return StreamingResponse(json_bytes, media_type="application/json", headers=headers)


@app.get(
    "/encuestas/export/pickle/",
    tags=["Upload/Export"],
    summary="Exportar todas las encuestas a Pickle (binario Python)",
    description=(
        "Descarga todas las encuestas en formato Pickle (`encuestas.pkl`).\n\n"
        "**Cómo cargar en Python:**\n"
        "```python\n"
        "import pickle\n"
        "with open('encuestas.pkl', 'rb') as f:\n"
        "    encuestas = pickle.load(f)  # Lista de objetos EncuestaCompleta\n"
        "```\n\n"
        "**Protocolo:** Pickle protocolo 4 (compatible con Python 3.4+).\n\n"
        "**Cuándo usar Pickle sobre JSON:**\n"
        "- Cuando necesita recargar los datos rápidamente en Python\n"
        "- Cuando el tamaño importa (Pickle es más compacto que JSON)\n"
        "- Cuando trabaja con objetos Python complejos que JSON no puede serializar\n\n"
        "**⚠️ Advertencia de seguridad:** nunca deserialice (cargue) un archivo `.pkl` "
        "de una fuente no confiable — Pickle puede ejecutar código arbitrario al cargar.\n\n"
        "**404** si no hay encuestas registradas."
    ),
)
async def export_pickle(request: Request):
    """
    Exporta todas las encuestas a Pickle.

    Pickle es un formato binario específico de Python que serializa objetos
    preservando su estructura exacta (tipos, clases, referencias). Es más
    rápido que JSON para cargar/guardar, pero NO es interoperable con otros
    lenguajes y puede tener vulnerabilidades de seguridad al deserializar
    datos de fuentes no confiables.

    Diferencias clave JSON vs Pickle:
    - JSON: texto plano, interoperable, seguro, más lento
    - Pickle: binario, solo Python, rápido, requiere confianza en la fuente
    """
    if not db_encuestas:
        raise HTTPException(status_code=404, detail="No hay encuestas para exportar")

    # Serializar a pickle (protocolo 4 para compatibilidad)
    pickle_bytes = io.BytesIO(pickle.dumps(list(db_encuestas.values()), protocol=4))
    
    headers = {"Content-Disposition": "attachment; filename=encuestas.pkl"}
    return StreamingResponse(pickle_bytes, media_type="application/octet-stream", headers=headers)


# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA
# ══════════════════════════════════════════════════════════════════════════════

@app.get(
    "/ui",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def frontend():
    """Sirve la interfaz gráfica HTML del sistema de encuestas."""
    with open("frontend/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get(
    "/",
    tags=["Sistema"],
    summary="Health check — estado de la API",
    description=(
        "Verifica que la API esté activa y retorna información de estado básica.\n\n"
        "**Retorna:**\n"
        "- `estado` — siempre `'activo'` si el servidor está corriendo\n"
        "- `encuestas_registradas` — número de encuestas en memoria\n"
        "- `documentacion_swagger` — URL de Swagger UI (interfaz interactiva)\n"
        "- `redoc` — URL de ReDoc (documentación detallada)\n"
        "- `frontend` — URL de la interfaz gráfica\n\n"
        "**Uso típico:** los frontends y sistemas de monitoreo hacen `GET /` cada N segundos "
        "para verificar disponibilidad (liveness check). Si hay respuesta → API activa."
    ),
)
async def health_check():
    """Endpoint de verificación de estado de la API."""
    return {
        "estado": "activo",
        "encuestas_registradas": len(db_encuestas),
        "documentacion_swagger": "/docs",
        "redoc": "/redoc",
        "frontend": "/ui",
    }


# ══════════════════════════════════════════════════════════════════════════════
# EVENTO DE INICIO: Crear tablas de base de datos
# ══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def on_startup():
    """
    Evento de inicio de la aplicación.
    Crea las tablas de base de datos si no existen.
    """
    logger.info("INICIANDO API | Creando tablas de base de datos...")
    await crear_tablas()
    logger.info("BASE DE DATOS | Tablas creadas exitosamente")
