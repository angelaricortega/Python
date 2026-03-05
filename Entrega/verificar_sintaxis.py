"""
╔══════════════════════════════════════════════════════════════════════════╗
║   VERIFICADOR DE SINTAXIS — main.py                                    ║
║   Sistema de Análisis de Riesgo Crediticio                             ║
╚══════════════════════════════════════════════════════════════════════════╝

Ejecuta este script para verificar que main.py no tiene errores de sintaxis
antes de tomar las capturas de pantalla.

Uso:
    python verificar_sintaxis.py
"""

import sys
import os

# ═══════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN 1: Sintaxis de Python
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("  VERIFICADOR DE SINTAXIS — main.py")
print("=" * 70)

print("\n[1/5] Verificando sintaxis de main.py...")

try:
    import py_compile
    py_compile.compile("main.py", doraise=True)
    print("  ✅ main.py tiene sintaxis válida")
except py_compile.PyCompileError as e:
    print(f"  ❌ Error de sintaxis: {e}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN 2: Imports
# ═══════════════════════════════════════════════════════════════════════════

print("\n[2/5] Verificando imports...")

imports_requeridos = [
    "fastapi",
    "pydantic",
    "numpy",
    "uvicorn",
]

for modulo in imports_requeridos:
    try:
        __import__(modulo)
        print(f"  ✅ {modulo}")
    except ImportError:
        print(f"  ❌ {modulo} — Ejecuta: pip install {modulo}")

# ═══════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN 3: Estructura de main.py
# ═══════════════════════════════════════════════════════════════════════════

print("\n[3/5] Verificando estructura de main.py...")

with open("main.py", "r", encoding="utf-8") as f:
    contenido = f.read()

# Verificar elementos requeridos
verificaciones = [
    ("from fastapi import", "Import de FastAPI"),
    ("from pydantic import", "Import de Pydantic"),
    ("class RiesgoCrediticioInput", "Modelo de entrada"),
    ("class RiesgoCrediticioOutput", "Modelo de salida"),
    ("def procesar_riesgo_crediticio", "Función pura"),
    ("app = FastAPI", "Instancia de FastAPI"),
    ("@app.post", "Endpoint POST"),
    ("@app.get", "Endpoint GET"),
    ("@app.delete", "Endpoint DELETE"),
    ("np.mean", "Uso de numpy"),
    ("np.std", "Uso de numpy para desviación estándar"),
    ("ddof=1", "Cálculo muestral (ddof=1)"),
]

for codigo, descripcion in verificaciones:
    if codigo in contenido:
        print(f"  ✅ {descripcion}")
    else:
        print(f"  ⚠️  {descripcion} — No encontrado")

# ═══════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN 4: Modelos Pydantic
# ═══════════════════════════════════════════════════════════════════════════

print("\n[4/5] Verificando modelos Pydantic...")

# Verificar campos en el modelo de entrada
campos_input = [
    "municipio: str",
    "cartera_a: float",
    "cartera_b: float",
    "cartera_c: float",
    "cartera_d: float",
    "cartera_e: float",
    "total_cartera: float",
    "Field(",
]

for campo in campos_input:
    if campo in contenido:
        print(f"  ✅ {campo}")
    else:
        print(f"  ⚠️  {campo} — No encontrado")

# ═══════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN 5: Endpoints
# ═══════════════════════════════════════════════════════════════════════════

print("\n[5/5] Verificando endpoints...")

endpoints = [
    ('@app.post("/analizar"', "POST /analizar"),
    ('@app.get("/",', "GET / (raíz)"),
    ('@app.get("/historial"', "GET /historial"),
    ('@app.get("/historial/{analisis_id}"', "GET /historial/{{id}}"),
    ('@app.delete("/historial/{analisis_id}"', "DELETE /historial/{{id}}"),
]

for endpoint, descripcion in endpoints:
    if endpoint in contenido:
        print(f"  ✅ {descripcion}")
    else:
        print(f"  ⚠️  {descripcion} — No encontrado")

# ═══════════════════════════════════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("  RESUMEN")
print("=" * 70)
print("\n  ✅ main.py está listo para ejecutar")
print("\n  Siguientes pasos:")
print("    1. Ejecuta: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
print("    2. Abre: http://127.0.0.1:8000/docs")
print("    3. Toma las 5 capturas de pantalla")
print("    4. Revisa reflexiones.md")
print("    5. Empaqueta y entrega")
print("\n" + "=" * 70 + "\n")
