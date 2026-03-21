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

import httpx
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from models import (
    EncuestaCompleta,
    Encuestado,
    EstadisticasEncuesta,
    ExportResultado,
    GoogleFormsPayload,
    MensajeRespuesta,
    RespuestaEncuesta,
)

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
    title="API de Encuestas Poblacionales",
    description="""
## Sistema de Validación y Gestión de Encuestas Colombianas

API REST desarrollada con **FastAPI + Pydantic v2** para la recolección,
validación y análisis estadístico de encuestas poblacionales.

### Características principales
- **Validación rigurosa**: edad [0-120], estrato [1-6], departamentos DANE
- **Tipos polimórficos**: Likert (1-5), porcentaje (0-100), texto, si/no
- **CRUD completo** con almacenamiento en memoria
- **Upload de CSV** desde Google Forms o archivos locales
- **Export a JSON/Pickle** para interoperabilidad
- **Estadísticas agregadas** en tiempo real
- **Manejo de errores HTTP 422** con mensajes descriptivos
- **Documentación interactiva** en `/docs` (Swagger) y `/redoc` (Redoc)

### Ejecución local
```bash
uvicorn main:app --reload --port 8000
```
    """,
    version="2.0.0",
    contact={
        "name": "Equipo de Desarrollo — Python para APIs e IA",
        "email": "dev@encuestas-co.edu",
    },
    license_info={"name": "MIT License"},
    openapi_tags=[
        {"name": "Encuestas", "description": "Operaciones CRUD sobre encuestas poblacionales"},
        {"name": "Upload/Export", "description": "Carga y descarga de archivos"},
        {"name": "Estadísticas", "description": "Análisis estadístico agregado"},
        {"name": "Sistema", "description": "Health check y estado de la API"},
    ],
)


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
        "Recibe, valida y almacena una encuesta poblacional completa. "
        "El servidor asigna automáticamente el `id_encuesta` (UUID) y el "
        "`fecha_registro` (timestamp ISO 8601). Retorna la encuesta guardada."
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
        "Retorna el listado completo de encuestas registradas. "
        "Soporta paginación mediante `skip` (offset) y `limit` (máximo por página)."
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
    summary="Estadísticas agregadas del repositorio",
    description=(
        "Genera un resumen estadístico en tiempo real: conteo total, "
        "promedio de edad, distribuciones por estrato, departamento, "
        "género y nivel educativo. "
        "**Endpoint async** — en producción delegaría cómputo a una BD con `await`."
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
        "Recupera una encuesta específica por su UUID. "
        "Retorna **200 OK** si existe, **404 Not Found** si el ID no está registrado."
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
    summary="Actualizar encuesta existente",
    description=(
        "Reemplaza completamente los datos de una encuesta existente. "
        "Preserva el `id_encuesta` original y actualiza el `fecha_registro`. "
        "Retorna **200 OK** con el objeto actualizado, **404** si no existe."
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
        "Elimina permanentemente una encuesta del repositorio. "
        "Retorna **204 No Content** en caso de éxito, **404** si el ID no existe. "
        "Esta operación es irreversible."
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
    "/encuestas/upload-csv/",
    tags=["Upload/Export"],
    summary="Subir archivo CSV desde Google Forms",
    description=(
        "Sube un archivo CSV exportado desde Google Forms o Google Sheets. "
        "El sistema detecta automáticamente las columnas demográficas y de respuestas."
    ),
    status_code=200,
)
@log_request
async def upload_csv(request: Request, file: UploadFile = File(...)) -> dict:
    """
    Procesa archivo CSV de Google Forms y carga encuestas.

    Columnas detectadas automáticamente:
    - Demográficas: nombre, edad, genero, estrato, departamento, municipio, educacion, ocupacion
    - Respuestas: Cualquier otra columna numérica o de texto

    Retorna el número de encuestas procesadas exitosamente.
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

    logger.info(f"UPLOAD CSV | Archivo: {file.filename} | Filas: {len(df)}")

    ids_creados = []
    errores = []

    for idx, row in df.iterrows():
        try:
            # Mapeo flexible de columnas
            col_map = {str(c).lower().strip(): c for c in df.columns}
            
            # Obtener valores con nombres flexibles
            nombre_col = next((col_map[c] for c in ['nombre', 'nombres', 'nombre completo'] if c in col_map), None)
            edad_col = next((col_map[c] for c in ['edad', 'edad (años)'] if c in col_map), None)
            genero_col = next((col_map[c] for c in ['genero', 'género', 'sexo'] if c in col_map), None)
            estrato_col = next((col_map[c] for c in ['estrato', 'estrato socioeconomico'] if c in col_map), None)
            depto_col = next((col_map[c] for c in ['departamento', 'depto'] if c in col_map), None)
            municipio_col = next((col_map[c] for c in ['municipio', 'ciudad'] if c in col_map), None)
            edu_col = next((col_map[c] for c in ['nivel_educativo', 'educacion', 'escolaridad'] if c in col_map), None)
            ocupacion_col = next((col_map[c] for c in ['ocupacion', 'ocupación', 'trabajo', 'empleo'] if c in col_map), None)

            if not nombre_col or not edad_col:
                raise ValueError(f"Fila {idx + 1}: Faltan columnas requeridas (nombre, edad)")

            # Parsear edad
            edad_raw = row.get(edad_col, 30)
            try:
                edad = int(float(str(edad_raw).replace(",", ".")))
            except (ValueError, TypeError):
                edad = 30

            # Parsear estrato
            estrato_raw = row.get(estrato_col, 3) if estrato_col else 3
            try:
                estrato = int(float(str(estrato_raw).replace(",", ".")))
            except (ValueError, TypeError):
                estrato = 3

            # Género
            genero_raw = str(row.get(genero_col, "prefiero_no_decir")).strip().lower()
            genero_map = {
                "m": "masculino", "masculino": "masculino", "hombre": "masculino",
                "f": "femenino", "femenino": "femenino", "mujer": "femenino",
                "no_binario": "no_binario", "no binario": "no_binario",
                "prefiero_no_decir": "prefiero_no_decir", "prefiero no decir": "prefiero_no_decir",
            }
            genero = genero_map.get(genero_raw, "prefiero_no_decir")

            # Nivel educativo
            nivel_raw = str(row.get(edu_col, "otro")).strip().lower() if edu_col else "otro"
            nivel_map = {
                "ninguno": "ninguno", "primaria": "primaria", "secundaria": "secundaria",
                "tecnico": "tecnico", "técnico": "tecnico", "universitario": "universitario",
                "posgrado": "posgrado", "postgrado": "posgrado",
            }
            nivel_educativo = nivel_map.get(nivel_raw, "otro")

            # Construir respuestas (columnas restantes)
            respuestas = []
            pregunta_id = 1
            skip_cols = {nombre_col, edad_col, genero_col, estrato_col, depto_col, municipio_col, edu_col, ocupacion_col}
            
            for col in df.columns:
                if col in skip_cols:
                    continue
                
                valor = row.get(col)
                if pd.isna(valor):
                    continue

                # Determinar tipo de pregunta
                if isinstance(valor, (int, float)):
                    if 1 <= valor <= 5:
                        tipo = "likert"
                        val = int(valor) if isinstance(valor, float) and valor.is_integer() else float(valor)
                    elif 0 <= valor <= 100:
                        tipo = "porcentaje"
                        val = float(valor)
                    else:
                        tipo = "numerico"
                        val = float(valor)
                elif isinstance(valor, str):
                    valor = valor.strip()
                    if valor.lower() in ('si', 'sí', 'no'):
                        tipo = "si_no"
                        val = "si" if valor.lower() in ('si', 'sí') else "no"
                    else:
                        tipo = "texto_abierto"
                        val = valor
                else:
                    continue

                respuestas.append({
                    "pregunta_id": pregunta_id,
                    "enunciado": str(col),
                    "tipo_pregunta": tipo,
                    "valor": val,
                })
                pregunta_id += 1

            if not respuestas:
                raise ValueError(f"Fila {idx + 1}: No se encontraron respuestas")

            encuesta = EncuestaCompleta(
                encuestado=Encuestado(
                    nombre=str(row.get(nombre_col, f"Encuestado {idx + 1}")).strip(),
                    edad=edad,
                    genero=genero,
                    estrato=estrato,
                    departamento=str(row.get(depto_col, "Bogotá D.C.")).strip() if depto_col else "Bogotá D.C.",
                    municipio=str(row.get(municipio_col, "Desconocido")).strip() if municipio_col else "Desconocido",
                    nivel_educativo=nivel_educativo,
                    ocupacion=str(row.get(ocupacion_col, "")).strip() if ocupacion_col else None,
                ),
                respuestas=respuestas,
                observaciones_generales=f"[Upload CSV] Archivo: {file.filename}, Fila: {idx + 1}",
                fuente="csv_upload",
            )
            db_encuestas[encuesta.id_encuesta] = encuesta
            ids_creados.append(encuesta.id_encuesta)

        except Exception as e:
            errores.append({"fila": idx + 1, "error": str(e)})

    logger.info(f"UPLOAD CSV COMPLETADO | Exitosos: {len(ids_creados)} | Errores: {len(errores)}")

    return {
        "total_procesados": len(df),
        "exitosos": len(ids_creados),
        "fallidos": len(errores),
        "errores": errores[:10],  # Máximo 10 errores
        "ids_creados": ids_creados[:10],  # Máximo 10 IDs
    }


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS EXPORT (Bonificación +0.1 JSON vs Pickle)
# ══════════════════════════════════════════════════════════════════════════════

@app.get(
    "/encuestas/export/json/",
    tags=["Upload/Export"],
    summary="Exportar encuestas a JSON",
    description="Descarga todas las encuestas en formato JSON.",
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
    summary="Exportar encuestas a Pickle",
    description="Descarga todas las encuestas en formato Pickle (binario de Python).",
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
    summary="Health check",
    description="Verifica que la API esté activa. Retorna estado y enlaces a la documentación.",
)
async def health_check():
    """Endpoint de verificación de estado de la API."""
    return {
        "estado": "activo",
        "encuestas_registradas": len(db_encuestas),
        "documentacion": "/docs",
        "redoc": "/redoc",
        "frontend": "/ui",
    }
