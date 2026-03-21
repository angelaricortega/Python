# 🌸 API de Encuestas Poblacionales

API REST desarrollada con **FastAPI + Pydantic v2** para la recolección, validación y análisis estadístico de encuestas poblacionales colombianas.

> **Material del curso:** Python para APIs e IA — Universidad Santo Tomás (2026)

---

## ✨ Características

- **CRUD completo** de encuestas (Crear, Leer, Actualizar, Eliminar)
- **Validación rigurosa** con Pydantic v2:
  - Edad [0-120] — restricción biológica
  - Estrato [1-6] — clasificación socioeconómica colombiana
  - Departamentos DANE — catálogo oficial de Colombia
  - Escala Likert [1-5] y Porcentajes [0-100]
- **Upload de CSV** desde Google Forms
- **Export a JSON/Pickle** para interoperabilidad
- **Estadísticas en tiempo real** con distribuciones
- **Manejo de errores HTTP 422** con mensajes descriptivos
- **Documentación interactiva** Swagger UI y Redoc
- **Frontend HTML** interactivo

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd encuesta-api
```

### 2. Crear entorno virtual (venv)

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> **Justificación:** Usamos `venv` (en lugar de `conda`) porque es más ligero, viene incluido con Python desde 3.3, y es suficiente para proyectos de APIs web sin dependencias científicas complejas.

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la API

```bash
uvicorn main:app --reload --port 8000
```

---

## 📚 Endpoints

### CRUD Encuestas

| Método | Ruta | Descripción | Status Code |
|--------|------|-------------|-------------|
| POST | `/encuestas/` | Crear nueva encuesta | 201 Created |
| GET | `/encuestas/` | Listar todas las encuestas | 200 OK |
| GET | `/encuestas/{id}` | Obtener encuesta por ID | 200 OK / 404 |
| PUT | `/encuestas/{id}` | Actualizar encuesta | 200 OK / 404 |
| DELETE | `/encuestas/{id}` | Eliminar encuesta | 204 No Content / 404 |

### Upload/Export

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/encuestas/upload-csv/` | Subir archivo CSV desde Google Forms |
| GET | `/encuestas/export/json/` | Descargar resultados en JSON |
| GET | `/encuestas/export/pickle/` | Descargar resultados en Pickle |

### Estadísticas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/encuestas/estadisticas/` | Resumen estadístico agregado |

### Sistema

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/ui` | Frontend interactivo |
| GET | `/docs` | Swagger UI (documentación interactiva) |
| GET | `/redoc` | Redoc (documentación alternativa) |

---

## 📤 Formato de Upload (CSV)

El sistema detecta automáticamente las columnas demográficas:

### Columnas reconocidas:
- `nombre` — Nombre completo (requerido)
- `edad` — Edad en años (requerido, 0-120)
- `genero` — Género (masculino, femenino, no_binario, prefiero_no_decir)
- `estrato` — Estrato socioeconómico (1-6)
- `departamento` — Departamento colombiano (catálogo DANE)
- `municipio` — Ciudad o municipio
- `nivel_educativo` — Nivel educativo (ninguno, primaria, secundaria, tecnico, universitario, posgrado)
- `ocupacion` — Ocupación o trabajo

### Columnas de respuestas:
Cualquier otra columna será tratada como pregunta:
- **Valores 1-5** → Tipo `likert`
- **Valores 0-100** → Tipo `porcentaje`
- **"si"/"no"** → Tipo `si_no`
- **Texto** → Tipo `texto_abierto`

### Ejemplo CSV:

```csv
nombre,edad,genero,estrato,departamento,municipio,nivel_educativo,ocupacion,satisfaccion,confianza
María García,34,femenino,3,Antioquia,Medellín,universitario,Docente,4,75.5
Carlos López,28,masculino,2,Valle del Cauca,Cali,tecnico,Ingeniero,5,60.0
```

---

## 🧪 Pruebas

### Ejecutar tests unitarios (Bonificación +0.1)

```bash
pytest tests/test_endpoints.py -v
```

### Probar upload de CSV

1. Abre el frontend: http://localhost:8000/ui
2. Ve a la pestaña "Upload CSV"
3. Arrastra un archivo CSV o haz clic para seleccionar

### Probar exportación

```bash
# Descargar JSON
curl -O http://localhost:8000/encuestas/export/json/

# Descargar Pickle
curl -O http://localhost:8000/encuestas/export/pickle/
```

---

## 🎨 Frontend

Accede a la interfaz gráfica en: **http://localhost:8000/ui**

Funcionalidades:
- ✏️ Crear encuestas manualmente con validación en tiempo real
- 📤 Upload de CSV con drag & drop
- 📥 Exportar resultados a JSON/Pickle
- 📊 Ver estadísticas con gráficos de barras
- 📋 Listar y buscar encuestas por ID

---

## 📖 Documentación Interactiva

FastAPI genera automáticamente documentación interactiva:

- **Swagger UI**: http://localhost:8000/docs
  - Prueba de endpoints directamente desde el navegador
  - Esquemas JSON de request/response
  - Autenticación (si estuviera configurada)

- **Redoc**: http://localhost:8000/redoc
  - Vista alternativa más limpia
  - Navegación lateral por endpoints

---

## 🔧 Estructura del Proyecto

```
encuesta-api/
├── main.py                    # Puntos de entrada API (endpoints)
├── models.py                  # Modelos Pydantic anidados
├── validators.py              # Validadores (DANE, estrato, edad)
├── requirements.txt           # Dependencias
├── render.yaml                # Configuración de despliegue en Render
├── Procfile                   # Configuración de despliegue (Railway/Heroku)
├── README.md                  # Este archivo
├── .gitignore                 # Git ignore
├── frontend/
│   └── index.html             # Interfaz gráfica HTML
├── tests/
│   └── test_endpoints.py      # 25 tests unitarios con pytest
├── scripts/
│   └── cliente_consumidor.py  # Cliente Python (httpx + pandas)
└── datos_ejemplo/
    └── encuestas_ejemplo.csv  # CSV de ejemplo para pruebas
```

---

## 🎓 Bonificaciones Implementadas

### ✅ +0.1 Tests Unitarios
- 25 tests con `pytest` organizados en clases por endpoint:
  - Ciclo CRUD completo (POST → GET → PUT → DELETE)
  - Validaciones Pydantic (edad inválida, estrato, departamento, Likert)
  - Estructura del handler HTTP 422 personalizado
  - Estadísticas agregadas

**Ejecutar:**
```bash
pytest tests/test_endpoints.py -v
```

### ✅ +0.1 Serialización JSON vs Pickle
- Endpoint `/encuestas/export/json/` — formato universal, legible
- Endpoint `/encuestas/export/pickle/` — binario, rápido, solo Python

**Diferencias clave:**
| Característica | JSON | Pickle |
|----------------|------|--------|
| Formato | Texto plano | Binario |
| Legibilidad | ✅ Legible por humanos | ❌ No legible |
| Interoperabilidad | ✅ Cualquier lenguaje | ❌ Solo Python |
| Seguridad | ✅ Seguro | ⚠️ Riesgo al deserializar |
| Velocidad | 🐌 Más lento | 🚀 Más rápido |

### ✅ +0.1 Cliente Python Consumidor
- Script `scripts/cliente_consumidor.py` que:
  - Consume la API con `httpx`
  - Carga datos desde CSV
  - Genera reporte estadístico con `pandas`
  - Exporta a JSON y Pickle

**Ejecutar:**
```bash
python scripts/cliente_consumidor.py
```

### ✅ +0.2 Despliegue en la Nube (Render)
- Archivos de configuración incluidos: `render.yaml` y `Procfile`

**Pasos para desplegar en Render (gratuito):**
1. Crear cuenta en https://render.com
2. Hacer clic en **New → Web Service**
3. Conectar el repositorio de GitHub (`angelaricortega/Python`)
4. Render detecta automáticamente el `render.yaml` — no requiere configuración manual
5. Hacer clic en **Deploy**

La URL pública quedará disponible en: `https://encuesta-api.onrender.com`

**Alternativa con Railway:**
```bash
# Instalar Railway CLI
npm install -g @railway/cli
railway login
railway up
```

---

## 🔍 Decisiones de Diseño

### ¿Por qué `async def` en el endpoint de estadísticas?

El endpoint `/encuestas/estadisticas/` está implementado como `async def` porque:

1. **Escenario I/O bound**: En producción, consultaría una base de datos con operaciones de agregación (GROUP BY, COUNT, AVG).
2. **Non-blocking**: Con `async/await`, la corutina cede el control al event loop mientras espera la respuesta de la BD.
3. **Concurrencia**: Permite atender miles de requests simultáneos sin bloquear threads.
4. **ASGI**: FastAPI usa Uvicorn (servidor ASGI) que entiende nativamente `async/await`.

```python
@app.get("/encuestas/estadisticas/")
async def obtener_estadisticas(request: Request):
    # En producción: await db.encuestas.aggregate(pipeline)
    # El await libera el event loop mientras la BD procesa
```

### ¿Por qué validación con Pydantic v2?

1. **Type hints nativos**: Usa el sistema de tipos de Python 3.10+
2. **Validación anidada**: Valida automáticamente modelos dentro de modelos
3. **Mensajes de error claros**: Facilita debugging y feedback al usuario
4. **Rendimiento**: Pydantic v2 es 5-50x más rápido que v1 (usa Rust)

---

## 📝 Notas

- **Almacenamiento en memoria**: Los datos se pierden al reiniciar el servidor. Para producción, conectar a PostgreSQL/MongoDB.
- **Validación estricta**: La API rechaza datos fuera de rango (edad > 120, estrato > 6, etc.).
- **Contexto colombiano**: Los validadores usan el catálogo oficial DANE de Colombia.

---

## 📄 Licencia

MIT License — Uso libre para fines educativos.

---

## 👨‍💻 Autor

Material desarrollado para el curso **Python para APIs e IA** — Universidad Santo Tomás (2026)

---

## 🙋 Soporte

Para dudas o problemas:
1. Revisar la documentación en `/docs`
2. Ejecutar tests: `pytest tests/test_endpoints.py -v`
3. Verificar logs en consola

---

## 🎤 Preguntas de Sustentación — Respuestas Técnicas

### Eje 1 — Modelos Pydantic y Tipado

---

**Pregunta 1 — Si envío `edad` como el string `"25"` en lugar de un entero, ¿la API lo rechaza o lo acepta?**

La API **lo acepta y lo convierte automáticamente**. Pydantic v2 opera por defecto en modo *lax* (no estricto): cuando un campo está declarado como `int` y recibe el string `"25"`, Pydantic intenta la coerción `int("25") = 25` y, si tiene éxito, continúa la validación con el entero resultante.

Esto no es un bug — es una decisión de diseño deliberada de Pydantic v2 para facilitar el consumo desde formularios HTML y fuentes externas (como Google Forms) que a veces envían números como texto. Si se quisiera rechazar `"25"` explícitamente, habría que usar `model_config = ConfigDict(strict=True)`.

```python
# Pydantic v2 modo lax (default): "25" → int(25) → pasa validación ✅
# Pydantic v2 modo estricto:      "25" → ValueError: int required     ❌
```

---

**Pregunta 2 — En `Union[int, float, str]`, si llega `"5"`, ¿se guarda como `int`, `str` o `float`? ¿Y `5.0`?**

**Caso `"5"` (string):** El validador `limpiar_valor_entrada` (`mode='before'`) se ejecuta primero. Su lógica intenta `int("5") = 5` con éxito y **retorna el entero `5`**. Pydantic nunca ve el string — recibe directamente el `int 5`.

**Caso `5.0` (float):** El validador `mode='before'` solo transforma strings; `5.0` es un float, así que lo deja pasar sin modificar. Pydantic v2 usa "smart union" y elige el tipo más específico que coincide sin coerción: `5.0` ya es `float`, por lo que se almacena como `float 5.0`.

**Consecuencia práctica:** Si el tipo de pregunta es `"likert"` y llega `5.0`, el `model_validator mode='after'` detecta `isinstance(5.0, int) == False` y lanza `ValueError` — correcto, porque Likert requiere entero exacto. Esto garantiza integridad estadística: `4` y `4.0` no son equivalentes en la escala ordinal.

```python
# Criterio de resolución Union[int, float, str] en Pydantic v2:
# 1. Si ya es del tipo exacto → se usa sin coerción
# 2. Si es string → el field_validator mode='before' lo transforma primero
# 3. Smart union prioriza el tipo más restrictivo que coincide
```

---

**Pregunta 3 — ¿Qué modificar para agregar `SubRespuestas` anidadas dentro de `RespuestaEncuesta`?**

Solo hay que modificar **`models.py`**. Los endpoints no requieren ningún cambio porque FastAPI delega toda la deserialización y validación a Pydantic.

```python
# models.py — agregar:
class SubRespuesta(BaseModel):
    sub_id: int
    texto: str
    puntaje: Optional[float] = None

# Modificar RespuestaEncuesta:
class RespuestaEncuesta(BaseModel):
    ...
    sub_respuestas: Optional[List[SubRespuesta]] = Field(default=None)
```

Pydantic valida automáticamente la lista anidada. Swagger UI refleja el nuevo esquema sin tocar ningún endpoint. El payload JSON simplemente incluiría el array `sub_respuestas` dentro de cada respuesta.

---

### Eje 2 — Validadores de Campo

---

**Pregunta 4 — ¿Qué pasaría si el validador de estrato fuera `mode='before'` y llegara el string `"3"`?**

Fallaría incorrectamente con un error 422, **aunque `"3"` representa un estrato válido**.

El validador actual usa `mode='after'`, por lo que Pydantic convierte primero `"3"` → `3` (int), y el validador recibe el entero `3` y lo acepta.

Si fuera `mode='before'`, el validador recibiría el string `"3"` antes de la coerción. La lógica `isinstance(valor, int) or isinstance(valor, bool)` devolvería `False` para un string, y lanzaría `ValueError: El estrato debe ser un número entero` — rechazando un dato perfectamente válido.

```
mode='before' con "3":  validador → "3" es str, no int → ValueError ❌ (falso negativo)
mode='after'  con "3":  Pydantic convierte "3"→3, validador → 3 es int → OK ✅
```

**Regla práctica:** `mode='before'` para transformar o limpiar datos crudos; `mode='after'` para validar semántica sobre el tipo ya convertido.

---

**Pregunta 5 — Normalizar `"bogotá"` → `"Bogotá"` en el validador de departamento: ¿es validación o transformación? ¿Pydantic permite ambas?**

Es **ambas al mismo tiempo**, y Pydantic v2 las permite y fomenta en el mismo validador. El nombre oficial de esta capacidad es *validator with side effects* o simplemente *transformer-validator*.

En este proyecto, `normalizar_y_validar_departamento` hace exactamente eso:
1. **Transforma:** `"ANTIOQUIA"` o `"antioquia"` → `"Antioquia"` (nombre oficial DANE)
2. **Valida:** verifica que el nombre normalizado exista en el catálogo DANE; si no, lanza `ValueError`

**Implicaciones para la integridad del dato original:** El valor almacenado en el modelo **no es el que envió el usuario** sino la forma canónica del catálogo. Esto es intencional: garantiza que `distribucion_por_departamento` en las estadísticas agrupe correctamente sin producir entradas duplicadas como `"Córdoba"`, `"Cordoba"`, `"CORDOBA"`.

---

### Eje 3 — Endpoints y Protocolo HTTP

---

**Pregunta 6 — Si en `PUT /encuestas/{id}` el cliente envía solo el campo `estrato` modificado, ¿qué pasa?**

La API retorna **HTTP 422**. PUT tiene semántica de **reemplazo total**: el cliente debe enviar la representación completa del recurso. Si faltan campos requeridos (`nombre`, `edad`, `respuestas`, etc.), Pydantic lanza `RequestValidationError`.

Esto es **correcto según HTTP/1.1 (RFC 7231)**. Si se quisiera permitir actualización parcial, el verbo correcto es **PATCH**:

| Verbo | Semántica | Payload requerido |
|-------|-----------|-------------------|
| `PUT` | Reemplaza el recurso completo | Todo el objeto |
| `PATCH` | Modifica campos específicos | Solo los campos a cambiar |

Un `PATCH /encuestas/{id}` aceptaría `{"encuestado": {"estrato": 4}}` y actualizaría solo ese campo. Para implementarlo, se usaría un modelo Pydantic con todos los campos `Optional`.

---

**Pregunta 7 — `DELETE` retorna `204 No Content`. ¿Es correcto? ¿204 o 200?**

**204 es más correcto** según los estándares HTTP. La diferencia:

| Código | Semántica | Cuerpo de respuesta |
|--------|-----------|---------------------|
| `204 No Content` | Operación exitosa, no hay contenido que retornar | **Vacío obligatoriamente** (RFC 7230 §3.3) |
| `200 OK` | Operación exitosa, el cuerpo contiene la representación | Permite cuerpo |

El RFC 7231 especifica explícitamente `204` como el código preferido para DELETE cuando el servidor no retorna representación. Usar `200` con un `{"mensaje": "eliminado"}` es válido pero agrega una transferencia de datos innecesaria. Además, algunos clientes HTTP y proxies pueden ignorar cuerpos en respuestas `204`, causando comportamiento inesperado si se usa `200`.

En FastAPI, `return None` con `status_code=204` genera automáticamente una respuesta sin cuerpo.

---

**Pregunta 8 — Si no hay encuestas, ¿`/estadisticas/` retorna vacío, 404 o ceros?**

Retorna **ceros y distribuciones vacías** — y eso es lo correcto.

Un `404 Not Found` sería incorrecto: el endpoint *existe*, simplemente el repositorio está vacío. `404` significa "no encontré este recurso", no "no hay datos para procesar". Retornar `404` aquí confundiría a cualquier cliente que compruebe si la API está activa.

Un JSON completamente vacío `{}` sería incorrecto: no cumpliría el `response_model=EstadisticasEncuesta` y Pydantic lo rechazaría.

La implementación actual retorna:
```json
{
  "total_encuestas": 0,
  "edad_promedio": 0.0,
  "distribucion_por_estrato": {},
  ...
}
```
Esto permite que cualquier dashboard que consuma el endpoint funcione sin manejo de errores especial para el caso vacío — simplemente muestra graficas con 0 registros.

---

### Eje 4 — Manejo de Errores

---

**Pregunta 9 — Con tres errores simultáneos (edad 150, estrato 9, departamento inválido), ¿la API reporta los tres o solo el primero?**

**Los tres errores simultáneamente**. Pydantic v2 ejecuta todos los validadores de todos los campos antes de lanzar la excepción, y acumula todos los errores en una sola lista.

El handler personalizado `manejador_error_validacion` (RF4) los formatea en el campo `detalle_errores`:

```json
{
  "codigo_http": 422,
  "total_errores": 3,
  "detalle_errores": [
    {"campo": "body → encuestado → edad",        "mensaje": "Input should be less than or equal to 120"},
    {"campo": "body → encuestado → estrato",      "mensaje": "Input should be less than or equal to 6"},
    {"campo": "body → encuestado → departamento", "mensaje": "'Nárnia' no es un departamento válido"}
  ]
}
```

Esto es fundamental para UX: si la API reportara un error a la vez, el usuario necesitaría corregir y reenviar tres veces para descubrir todos sus errores.

---

### Eje 5 — Asincronía y ASGI

---

**Pregunta 10 — Si un `async def` llama internamente a una función síncrona que tarda 10 segundos, ¿qué pasa con los otros requests?**

**Bloquea el event loop completo durante 10 segundos.** Ninguna otra corutina puede ejecutarse mientras el event loop está ocupado esperando la llamada síncrona bloqueante.

```python
async def endpoint_roto():
    resultado = sqlite3.connect("db.sqlite").execute("SELECT ...").fetchall()  # bloquea 10s
    # ← durante esos 10s, NINGÚN otro request puede ser atendido
```

La solución correcta es ejecutar la función síncrona en un threadpool para no bloquear el event loop:

```python
import asyncio

async def endpoint_correcto():
    loop = asyncio.get_event_loop()
    resultado = await loop.run_in_executor(None, funcion_sincronica_pesada)
    # ← el event loop queda libre para atender otros requests mientras el thread trabaja
```

En producción, la solución definitiva es usar librerías async nativas: `aiosqlite` en lugar de `sqlite3`, `asyncpg` en lugar de `psycopg2`, `httpx.AsyncClient` en lugar de `requests`.

---

**Pregunta 11 — Si defino un endpoint con `def` en lugar de `async def`, ¿la aplicación deja de ser asíncrona?**

**No.** FastAPI/Starlette detecta si un endpoint es síncrono y lo ejecuta automáticamente en un **threadpool externo** usando `anyio.to_thread.run_sync`. El event loop principal nunca se bloquea.

```
async def endpoint → se ejecuta DIRECTAMENTE en el event loop (ideal para I/O async)
def endpoint       → FastAPI lo corre en un THREAD del pool (ideal para código CPU/sync)
```

Esto significa que en FastAPI puedes mezclar `async def` y `def` en la misma aplicación sin problemas. La diferencia es de rendimiento y semántica:

- `def` con código CPU-intensivo → correcto, el thread libera el event loop
- `async def` con `await db.query()` → correcto, el await libera el event loop
- `async def` con llamada síncrona bloqueante → **incorrecto**, bloquea el event loop

---

### Eje 6 — Infraestructura y Git

---

**Pregunta 12 — Un compañero no usó entorno virtual y tiene conflicto de versiones de Pydantic. ¿Cómo lo explico y resuelvo?**

**El problema:** Sin entorno virtual, `pip install` instala paquetes en el Python global del sistema operativo. Si el sistema ya tenía `pydantic==1.10` y el proyecto requiere `pydantic>=2.5`, hay conflicto: el sistema tiene una versión, el proyecto necesita otra. No pueden coexistir en el mismo entorno Python.

**La analogía:** Es como tener una sola versión de Microsoft Word instalada y que dos documentos requieran versiones incompatibles.

**La solución:**

```bash
# 1. Crear un entorno Python aislado solo para este proyecto
python -m venv .venv

# 2. Activar el entorno (Windows)
.venv\Scripts\activate

# 3. Instalar las versiones exactas del proyecto
pip install -r requirements.txt

# 4. Verificar que está usando el Python del venv
python -c "import pydantic; print(pydantic.__version__)"  # debe mostrar 2.x
```

Con el venv activo, todos los `pip install` van al directorio `.venv/` del proyecto y no afectan el Python global. El `.gitignore` excluye `.venv/` del repositorio porque cada desarrollador crea el suyo localmente a partir del `requirements.txt`.

---

**Pregunta 13 — El último commit introdujo un bug en los validadores. ¿Cómo vuelvo al estado anterior sin perder el historial?**

Hay tres opciones con diferente impacto en el historial:

**Opción 1 — `git revert` (recomendada, preserva historial):**
```bash
git revert HEAD          # crea un NUEVO commit que deshace el commit anterior
git push origin main     # seguro para ramas compartidas
```
El historial muestra el commit con el bug + el commit de reversión. No reescribe historia.

**Opción 2 — `git reset --soft` (deshace el commit, conserva los cambios en staging):**
```bash
git reset --soft HEAD~1  # el commit desaparece pero los archivos quedan modificados
# editar el bug, luego:
git commit -m "fix: corregir validador de departamento"
```
Reescribe la historia local. Solo seguro si no se ha hecho `push`.

**Opción 3 — Restaurar solo el archivo afectado:**
```bash
git checkout HEAD~1 -- validators.py   # restaura validators.py al commit anterior
git commit -m "fix: revertir validators.py al estado previo"
```

Para el contexto del curso, `git revert HEAD` es siempre la opción más segura porque es la única que no reescribe historia y puede usarse después de hacer `push`.

---

### Eje 7 — Decoradores y Documentación

---

**Pregunta 14 — ¿En qué se parecen y diferencian `@log_request` y `@app.post("/encuestas/")`?**

**Similitud estructural:** Ambos son funciones de orden superior — reciben una función como argumento y retornan una función. Eso los hace decoradores Python válidos en sentido técnico.

```python
# Estructura básica de ambos:
def decorador(func):      # recibe la función original
    def wrapper(*args):   # crea una nueva función
        ...               # hace algo
        return func(*args)
    return wrapper        # retorna la nueva función
```

**Diferencias fundamentales:**

| Aspecto | `@log_request` | `@app.post("/encuestas/")` |
|---------|---------------|---------------------------|
| Tipo | Decorador *envolvente* (wrapper) | Decorador de *registro* |
| Qué retorna | Una nueva función con logging añadido | La función **original sin modificar** |
| Efecto principal | Añade comportamiento en tiempo de ejecución | Registra la función en el router de Starlette |
| Usa `@wraps` | Sí (preserva `__name__`, `__doc__`) | No necesario |
| Ejecución | Cada vez que se llama el endpoint | Una sola vez al iniciar la app |

`@app.post()` no cambia cómo funciona el endpoint — simplemente dice *"cuando llegue un POST a `/encuestas/`, llamá a esta función"*. `@log_request` sí cambia el comportamiento: envuelve la función y añade logging antes de cada invocación.

---

**Pregunta 15 — ¿Qué pasaría con Swagger si se eliminan todos los type hints?**

Depende de dónde se eliminen:

**Si se eliminan de los modelos Pydantic:** La aplicación **fallaría al importar**. Pydantic v2 requiere type annotations para saber qué tipo de dato espera cada campo. Sin ellas, los campos no se registran como campos del modelo.

**Si se eliminan solo de las funciones de endpoint (pero se mantienen en los modelos):** La API seguiría funcionando en tiempo de ejecución, pero Swagger perdería información:
- FastAPI ya no podría inferir el tipo de los query parameters
- Los `response_model` seguirían funcionando (están en el decorador, no en el type hint)
- Los parámetros de path seguirían funcionando si usan `Path(...)`

**Si se eliminan ambos:** Swagger mostraría esquemas vacíos `{}` para todos los request/response bodies. La documentación interactiva quedaría inútil.

**Conclusión:** Los type hints no son decorativos en FastAPI/Pydantic — son el mecanismo central que hace funcionar la validación automática, la serialización y la generación de documentación OpenAPI. Sin ellos, el framework pierde su razón de ser.
