# API de Encuestas Poblacionales

API REST construida con **FastAPI + Pydantic v2** para la recolección, validación y análisis estadístico de encuestas poblacionales colombianas.

Desarrollada como actividad evaluativa del curso **Python para APIs e IA** — Semana III: Validación de Datos.

---

## Estructura del proyecto

```
encuesta-api/
├── main.py              # FastAPI: endpoints, decoradores, handler 422
├── models.py            # Pydantic: Encuestado, RespuestaEncuesta, EncuestaCompleta
├── validators.py        # Validadores auxiliares y catálogo DANE
├── requirements.txt     # Dependencias del proyecto
├── README.md            # Este archivo
├── .gitignore           # Exclusiones de Git
└── tests/
    ├── __init__.py
    ├── test_models.py   # Pruebas unitarias de modelos Pydantic (15+ tests)
    └── test_endpoints.py # Pruebas de integración de endpoints (20+ tests)
```

---

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd encuesta-api
```

### 2. Crear y activar entorno virtual

**¿Por qué `venv`?** Es el gestor estándar de Python, no requiere instalación adicional y garantiza reproducibilidad del entorno aislado del sistema.

```bash
# Crear entorno virtual
python -m venv .venv

# Activar (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activar (Windows CMD)
.venv\Scripts\activate.bat

# Activar (Linux/macOS)
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la API

```bash
uvicorn main:app --reload --port 8000
```

La API estará disponible en `http://localhost:8000`

---

## Documentación interactiva

| Interfaz | URL |
|----------|-----|
| Swagger UI | http://localhost:8000/docs |
| Redoc | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |

---

## Endpoints disponibles

| Método | Ruta | Descripción | Status |
|--------|------|-------------|--------|
| `GET` | `/` | Health check | 200 |
| `POST` | `/encuestas/` | Registrar nueva encuesta | 201 / 422 |
| `GET` | `/encuestas/` | Listar todas las encuestas | 200 |
| `GET` | `/encuestas/{id}` | Obtener encuesta por ID | 200 / 404 |
| `PUT` | `/encuestas/{id}` | Actualizar encuesta | 200 / 404 / 422 |
| `DELETE` | `/encuestas/{id}` | Eliminar encuesta | 204 / 404 |
| `GET` | `/encuestas/estadisticas/` | Estadísticas agregadas | 200 |

---

## Ejemplo de uso — cURL

### Crear encuesta

```bash
curl -X POST http://localhost:8000/encuestas/ \
  -H "Content-Type: application/json" \
  -d '{
    "encuestado": {
      "nombre": "María García",
      "edad": 34,
      "genero": "femenino",
      "estrato": 3,
      "departamento": "Antioquia",
      "municipio": "Medellín",
      "nivel_educativo": "universitario"
    },
    "respuestas": [
      {
        "pregunta_id": 1,
        "enunciado": "Satisfacción con el servicio de salud",
        "tipo_pregunta": "likert",
        "valor": 4
      }
    ]
  }'
```

### Obtener estadísticas

```bash
curl http://localhost:8000/encuestas/estadisticas/
```

---

## Ejecutar pruebas

```bash
# Todas las pruebas con detalle
pytest tests/ -v

# Solo modelos
pytest tests/test_models.py -v

# Solo endpoints
pytest tests/test_endpoints.py -v

# Con reporte de cobertura (requiere pytest-cov)
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## Reglas de validación

| Campo | Restricción | Fundamento |
|-------|-------------|------------|
| `edad` | [0, 120] | Axioma biológico estadístico |
| `estrato` | [1, 6] | Clasificación DANE Colombia |
| `departamento` | Catálogo DANE (33 entidades) | Integridad referencial geográfica |
| Escala Likert | [1, 5] | Escala ordinal estándar |
| Porcentaje | [0.0, 100.0] | Escala de razón estadística |
| `si_no` | "si" / "no" | Variable dicotómica |

---

## Decisiones de diseño

- **`Union[int, float, str]`** en `RespuestaEncuesta.valor`: permite una API única para todos los tipos de escala sin endpoints separados.
- **`mode='before'`** en validators: normaliza errores de digitación (espacios, comas decimales) antes de la validación.
- **`mode='after'`** en model_validator: valida coherencia cruzada tipo-valor después de construir el objeto.
- **`async def`** en estadísticas: preparado para I/O no bloqueante en producción con bases de datos.
- **Decoradores personalizados**: `@log_request` y `@timer` como cross-cutting concerns reutilizables.
