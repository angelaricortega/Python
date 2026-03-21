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
pytest tests/test_api.py -v
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
├── README.md                  # Este archivo
├── .gitignore                 # Git ignore
├── frontend/
│   └── index.html             # Interfaz gráfica HTML
├── tests/
│   └── test_api.py            # Tests unitarios con pytest
├── scripts/
│   └── cliente_consumidor.py  # Cliente Python (httpx + pandas)
└── datos_ejemplo/
    └── encuestas_ejemplo.csv  # CSV de ejemplo para pruebas
```

---

## 🎓 Bonificaciones Implementadas

### ✅ +0.1 Tests Unitarios
- 22 tests con `pytest` que validan:
  - Modelos Pydantic (Encuestado, RespuestaEncuesta, EncuestaCompleta)
  - Endpoints CRUD
  - Manejo de errores HTTP 422
  - Exportación JSON/Pickle

**Ejecutar:**
```bash
pytest tests/test_api.py -v
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

### ⏳ +0.2 Despliegue en la Nube
- Pendiente: Desplegar en Render/Railway

**Pasos sugeridos:**
1. Crear cuenta en https://render.com
2. Crear nuevo "Web Service"
3. Conectar repositorio de GitHub
4. Configurar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Desplegar

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
2. Ejecutar tests: `pytest tests/test_api.py -v`
3. Verificar logs en consola
