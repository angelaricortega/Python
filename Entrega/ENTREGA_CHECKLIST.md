# ✅ Checklist de Entrega — Proyecto Personal API
## Sistema de Análisis de Riesgo Crediticio

---

## 📦 ENTREGABLES REQUERIDOS

### ✅ 1. Código fuente
- [x] `main.py` — API completa con FastAPI (archivo principal para evaluación)
- [x] `requirements.txt` — Dependencias congeladas
- [x] `config.py` — Configuración global
- [x] `decorators.py` — Librería de decoradores
- [x] `modelos.py` — Modelos Pydantic
- [x] `api_client.py` — Cliente HTTP
- [x] `pipeline.py` — Pipeline completo
- [x] `visualizaciones.py` — Gráficas profesionales
- [x] `api_fastapi.py` — API alternativa (completa)

### ✅ 2. Evidencia de ejecución
- [ ] **CAPTURAS DE PANTALLA** (tomar al ejecutar):
  - [ ] Terminal con `uvicorn main:app --reload` corriendo
  - [ ] Swagger UI (`/docs`) mostrando los 4 endpoints
  - [ ] POST /analizar — caso exitoso (201)
  - [ ] POST /analizar — validación rechazada (422)
  - [ ] GET /historial — lista de análisis
  - [ ] GET /historial/99 — error 404
  - [ ] DELETE /historial/{id} — eliminación exitosa

- [ ] **O VIDEO** (alternativa a capturas):
  - [ ] Grabar < 3 min mostrando las 5 pruebas en Swagger UI

### ✅ 3. Reflexiones
- [x] `reflexiones.md` — Respuestas a las 4 preguntas (~150 palabras cada una)
  - [ ] Pregunta 1: Dominio y validaciones
  - [ ] Pregunta 2: Sin validación
  - [ ] Pregunta 3: Escalabilidad
  - [ ] Pregunta 4: Flujo completo

### ✅ 4. Documentación
- [x] `README.md` — Documentación completa del proyecto
- [x] `analisis.ipynb` — Notebook ejecutivo con explicaciones

---

## 🚀 INSTRUCCIONES DE EJECUCIÓN

### Paso 1: Activar entorno virtual
```bash
cd Entrega
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Paso 2: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Iniciar API
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 4: Abrir Swagger UI
Visite en su navegador:
```
http://127.0.0.1:8000/docs
```

---

## 📸 GUÍA PARA CAPTURAS DE PANTALLA

### Prueba 1: POST — Caso exitoso
1. En Swagger UI, expanda `POST /analizar`
2. Click en "Try it out"
3. Use los datos de ejemplo (ya están completados)
4. Click en "Execute"
5. Capture mostrando:
   - Request body (verde)
   - Response body (201 Created)
   - Campos calculados (indice_riesgo, nivel_riesgo, etc.)

### Prueba 2: POST — Validación rechazada (422)
1. En `POST /analizar`, modifique un campo:
   - Cambie `"total_cartera": 1800000000` por `"total_cartera": 0`
   - O cambie `"municipio": "Bogotá D.C."` por `"municipio": ""`
2. Click en "Execute"
3. Capture mostrando:
   - Request body con error
   - Response 422 Unprocessable Entity
   - Mensaje de error de Pydantic

### Prueba 3: GET /historial — Persistencia
1. Ejecute POST /analizar 2-3 veces con datos diferentes
2. Expanda `GET /historial`
3. Click en "Try it out" → "Execute"
4. Capture mostrando:
   - Lista con 2-3 análisis
   - IDs consecutivos (1, 2, 3...)
   - Diferentes municipios y niveles de riesgo

### Prueba 4: GET /historial/99 — Error 404
1. Expanda `GET /historial/{analisis_id}`
2. En `analisis_id`, escriba `99` (o un número que no exista)
3. Click en "Execute"
4. Capture mostrando:
   - Response 404 Not Found
   - Mensaje: "Análisis con ID 99 no encontrado"

### Prueba 5: DELETE — Eliminar y verificar
1. Primero verifique que existe el ID 1 con `GET /historial/1`
2. Expanda `DELETE /historial/{analisis_id}`
3. Escriba `1` en `analisis_id`
4. Click en "Execute"
5. Capture response exitoso
6. Ahora ejecute `GET /historial/1` nuevamente
7. Capture mostrando error 404 (ya fue eliminado)

---

## 📝 RÚBRICA DE EVALUACIÓN

| Criterio | % | Estado |
|----------|---|--------|
| Setup y entorno | 10% | ✅ requirements.txt + venv funcional |
| Modelos Pydantic | 20% | ✅ RiesgoCrediticioInput + RiesgoCrediticioOutput |
| Endpoints CRUD | 20% | ✅ 4 endpoints (POST, GET x2, DELETE) |
| Evidencia de ejecución | 15% | ⏳ Tomar capturas/video |
| Preguntas de reflexión | 20% | ✅ reflexiones.md completas |
| Originalidad | 15% | ✅ Dominio único (riesgo crediticio) |

**Nota máxima posible:** 100% (si todas las evidencias están completas)

---

## 🎯 VERIFICACIÓN DE CONCEPTOS APLICADOS

### Semana 1
- [x] Pattern Matching (`clasificar_nivel_riesgo()` con `match/case`)
- [x] Decoradores (`@app.post`, `@app.get`, `@app.delete`)
- [x] Type hints (`Literal`, `Optional`, `List`)

### Semana 2
- [x] Pydantic (`BaseModel`, `Field`, `field_validator`)
- [x] HTTP (verbos POST/GET/DELETE, status codes 201/200/404/422)
- [x] Función pura (`procesar_riesgo_crediticio()` independiente de FastAPI)
- [x] Numpy (12 cálculos con `ddof=1` para varianza muestral)

### Semana 3
- [x] FastAPI (app con 5 endpoints)
- [x] Swagger UI (`/docs` automático)
- [x] Routing CRUD completo
- [x] Manejo de errores con `HTTPException`

---

## 📋 ARCHIVOS PARA SUBIR

Subir los siguientes archivos a la plataforma de entrega:

1. `main.py` — API principal
2. `requirements.txt` — Dependencias
3. `reflexiones.md` — Respuestas a preguntas
4. `README.md` — Documentación
5. `capturas/` — Carpeta con 5+ capturas de pantalla (o enlace a video)

**Opcional (para mostrar trabajo completo):**
- `config.py`, `decorators.py`, `modelos.py`, `pipeline.py`, `visualizaciones.py`
- `analisis.ipynb`

---

## ⚠️ ANTES DE ENTREGAR

- [ ] Verificar que `main.py` se ejecuta sin errores
- [ ] Tomar todas las capturas de pantalla (5 pruebas)
- [ ] Revisar que las reflexiones están contextualizadas (no genéricas)
- [ ] Confirmar que el código es original (no copiado de compañeros)
- [ ] Exportar reflexiones a PDF si se requiere ese formato

---

**¡Listo para entrega!** 🎉

**Autores:** Angela Rico · Sebastian Ramirez  
**Fecha:** febrero 28, 2026  
**Universidad:** Universidad Santo Tomás
