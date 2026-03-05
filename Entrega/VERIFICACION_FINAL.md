# 🚀 VERIFICACIÓN FINAL ANTES DE ENTREGAR
## Sistema de Análisis de Riesgo Crediticio

---

## ✅ PASO 1: Verificar que main.py no tiene errores

### Opción A: Verificación rápida (recomendada)

Abre una terminal (PowerShell o CMD) y ejecuta:

```powershell
# Ir a la carpeta del proyecto
cd "c:\Users\user\Documents\001 Uni\Octavo\PYTHJON PARA DESARROLLO  DE APIS E INTELIGENCIA ARTIFICIAL\Python\Entrega"

# Verificar sintaxis de Python (sin ejecutar)
python -m py_compile main.py

# Si no muestra errores, el archivo está bien
echo "✅ main.py tiene sintaxis válida"
```

### Opción B: Verificar en VS Code

1. Abre `main.py` en VS Code
2. Presiona `F5` o ve a `Run > Start Debugging`
3. Si no hay errores rojos en el panel "Problems", está correcto

### Opción C: Verificación manual

Abre `main.py` y verifica que:
- [ ] No hay líneas subrayadas en rojo
- [ ] Todos los `import` están al inicio
- [ ] Las funciones tienen `return`
- [ ] Las llaves `{}` y paréntesis `()` están balanceados

---

## ✅ PASO 2: Ejecutar la API y tomar las 5 capturas

### 2.1 Iniciar la API

```powershell
# En la carpeta Entrega:
cd "c:\Users\user\Documents\001 Uni\Octavo\PYTHJON PARA DESARROLLO  DE APIS E INTELIGENCIA ARTIFICIAL\Python\Entrega"

# Activar entorno virtual (si existe)
venv\Scripts\activate

# Iniciar API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Espera a ver este mensaje:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 2.2 Abrir Swagger UI

En tu navegador, visita:
```
http://127.0.0.1:8000/docs
```

Deberías ver 5 endpoints listados.

---

## 📸 GUÍA PARA LAS 5 CAPTURAS DE PANTALLA

### 📷 Captura 1: POST — Caso exitoso (201 Created)

1. En Swagger UI, haz clic en **POST /analizar**
2. Clic en **"Try it out"**
3. Deja los datos de ejemplo (ya están completos)
4. Clic en **"Execute"**
5. **Toma la captura mostrando:**
   - Request body (cuadro verde)
   - Response code: `201`
   - Response body con: `indice_riesgo`, `nivel_riesgo`, `mensaje`

**Datos de ejemplo:**
```json
{
  "municipio": "Bogotá D.C.",
  "cartera_a": 1500000000,
  "cartera_b": 200000000,
  "cartera_c": 50000000,
  "cartera_d": 25000000,
  "cartera_e": 10000000,
  "total_cartera": 1800000000,
  "total_captaciones": 2500000000
}
```

**Resultado esperado:**
```json
{
  "id": 1,
  "municipio": "Bogotá D.C.",
  "indice_riesgo": 0.0472,
  "nivel_riesgo": "riesgo_moderado",
  "mensaje": "🟡 Alerta temprana — revisar (NPL < 5%)"
}
```

---

### 📷 Captura 2: POST — Validación rechazada (422 Unprocessable Entity)

1. En **POST /analizar**, modifica UN campo:
   - Cambia `"total_cartera": 1800000000` por `"total_cartera": 0`
2. Clic en **"Execute"**
3. **Toma la captura mostrando:**
   - Request body con el error
   - Response code: `422`
   - Mensaje de error de Pydantic

**Resultado esperado:**
```json
{
  "detail": [
    {
      "loc": ["body", "total_cartera"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

---

### 📷 Captura 3: GET /historial — Persistencia

1. Primero ejecuta POST /analizar 2-3 veces con datos diferentes
2. Haz clic en **GET /historial**
3. Clic en **"Try it out"** → **"Execute"**
4. **Toma la captura mostrando:**
   - Lista con 2-3 análisis
   - IDs consecutivos (1, 2, 3...)
   - Diferentes municipios

**Resultado esperado:**
```json
[
  {
    "id": 1,
    "municipio": "Bogotá D.C.",
    "indice_riesgo": 0.0472,
    "nivel_riesgo": "riesgo_moderado",
    "fecha_analisis": "2026-02-28T10:30:00"
  },
  {
    "id": 2,
    "municipio": "Medellín",
    "indice_riesgo": 0.0312,
    "nivel_riesgo": "riesgo_moderado",
    "fecha_analisis": "2026-02-28T10:31:00"
  }
]
```

---

### 📷 Captura 4: GET /historial/99 — Error 404

1. Haz clic en **GET /historial/{analisis_id}**
2. En `analisis_id`, escribe `99` (número que no existe)
3. Clic en **"Execute"**
4. **Toma la captura mostrando:**
   - Response code: `404`
   - Mensaje de error

**Resultado esperado:**
```json
{
  "detail": "Análisis con ID 99 no encontrado. IDs válidos: 1 a 3"
}
```

---

### 📷 Captura 5: DELETE — Eliminar y verificar

**Parte A: Eliminar**
1. Haz clic en **DELETE /historial/{analisis_id}**
2. En `analisis_id`, escribe `1`
3. Clic en **"Execute"**
4. **Toma la captura mostrando:**
   - Response code: `200`
   - Mensaje de confirmación

**Resultado esperado:**
```json
{
  "mensaje": "✅ Análisis 1 eliminado exitosamente",
  "id_eliminado": 1,
  "analisis_restantes": 2
}
```

**Parte B: Verificar que fue eliminado**
1. Ahora ve a **GET /historial/1**
2. Clic en **"Execute"**
3. **Toma la captura mostrando:**
   - Response code: `404`

**Resultado esperado:**
```json
{
  "detail": "Análisis con ID 1 no encontrado"
}
```

---

## ✅ PASO 3: Revisar reflexiones.md

Abre `reflexiones.md` y verifica:

- [ ] **Pregunta 1:** Menciona "riesgo crediticio", "cartera bancaria", "NPL Ratio"
- [ ] **Pregunta 2:** Incluye ejemplo con `total_cartera: 0` y `ZeroDivisionError`
- [ ] **Pregunta 3:** Habla de PostgreSQL, Redis, memoria RAM
- [ ] **Pregunta 4:** Describe el flujo completo (9 pasos)

**NO debe decir:**
- ❌ "mi dominio es genérico"
- ❌ "los datos son cualquiera"
- ❌ Copiado textual de la lección

**SÍ debe decir:**
- ✅ "sistema financiero colombiano"
- ✅ "Datos Abiertos Gov.co"
- ✅ "Circular 98 Superfinanciera"
- ✅ "Basel II/III"

---

## ✅ PASO 4: Empaquetar archivos para subir

### Archivos obligatorios (mínimo):

```
📦 Para_Entrega/
├── 📄 main.py                    ← API principal
├── 📄 requirements.txt           ← Dependencias
├── 📄 reflexiones.md             ← Respuestas (o PDF)
├── 📄 README.md                  ← Documentación
└── 📁 capturas/
    ├── 📷 captura_1_post_exitoso.png
    ├── 📷 captura_2_post_error_422.png
    ├── 📷 captura_3_get_historial.png
    ├── 📷 captura_4_get_404.png
    └── 📷 captura_5_delete.png
```

### Archivos adicionales (opcional, muestra trabajo completo):

```
📦 Para_Entrega_Completo/
├── 📄 main.py
├── 📄 requirements.txt
├── 📄 reflexiones.md
├── 📄 README.md
├── 📄 ENTREGA_CHECKLIST.md
├── 📁 capturas/
│   └── (5 capturas)
├── 📄 config.py
├── 📄 decorators.py
├── 📄 modelos.py
├── 📄 pipeline.py
├── 📄 visualizaciones.py
├── 📄 api_fastapi.py
└── 📄 analisis.ipynb
```

---

## 🎯 CHECKLIST FINAL

Antes de subir a la plataforma:

- [ ] **main.py se ejecuta sin errores** (verificado con `py_compile`)
- [ ] **5 capturas tomadas** (numeradas y claras)
- [ ] **reflexiones.md revisado** (contextualizado, no genérico)
- [ ] **Archivos empaquetados** (ZIP o carpeta)
- [ ] **Nombre del archivo:** `Apellido_Nombre_API_Riesgo.zip`

---

## 📤 SUBIR A PLATAFORMA

1. Ingresa a la plataforma de entrega
2. Selecciona la tarea: "Actividad Aplicada — Semana III"
3. Sube el archivo ZIP o carpeta
4. Verifica que se subió correctamente
5. ¡Entregado! ✅

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Error: "uvicorn: command not found"

```powershell
# Activar entorno virtual
venv\Scripts\activate

# Instalar uvicorn
pip install uvicorn
```

### Error: "ModuleNotFoundError: No module named 'fastapi'"

```powershell
# Instalar dependencias
pip install -r requirements.txt
```

### Error: "Port 8000 is already in use"

```powershell
# Opción 1: Matar proceso en puerto 8000
netstat -ano | findstr :8000
taskkill /PID <numero> /F

# Opción 2: Usar otro puerto
uvicorn main:app --reload --port 8001
```

### Swagger UI no carga

1. Verifica que uvicorn dice "Uvicorn running on http://0.0.0.0:8000"
2. Prueba en modo incógnito del navegador
3. Limpia caché del navegador (Ctrl+Shift+R)

---

## 🎉 ¡LISTO PARA ENTREGAR!

**Nota máxima posible:** 100/100

**Autores:** Angela Rico · Sebastian Ramirez  
**Fecha:** febrero 28, 2026  
**Universidad:** Universidad Santo Tomás
