#!/usr/bin/env python
# ════════════════════════════════════════════════════════════════════════════════
# start.py — Script de Inicio para RiskAPI
# ════════════════════════════════════════════════════════════════════════════════
#
# USO:
#   python start.py
#
# Este script:
#   1. Carga variables de entorno desde .env
#   2. Verifica dependencias
#   3. Inicia la API con la configuración adecuada
#
# ════════════════════════════════════════════════════════════════════════════════

import os
import sys
from pathlib import Path


def main():
    """Función principal para iniciar la API."""
    
    # Cambiar al directorio del script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("\n" + "=" * 65)
    print("  RISKAPI — Sistema de Análisis de Riesgo Crediticio")
    print("  Universidad Santo Tomás · 2026")
    print("=" * 65)

    # ── 1. Cargar variables de entorno ─────────────────────────────────────────────
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("\n✓ Variables de entorno cargadas desde .env")
    except ImportError:
        print("\n⚠ python-dotenv no instalado. Usando valores por defecto.")
        print("  Instale con: pip install python-dotenv")

    # ── 2. Verificar dependencias ──────────────────────────────────────────────────
    print("\nVerificando dependencias...")

    dependencias = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "numpy": "NumPy",
        "pandas": "Pandas",
    }

    faltantes = []
    for paquete, nombre in dependencias.items():
        try:
            __import__(paquete)
            print(f"  ✓ {nombre}")
        except ImportError:
            print(f"  ✗ {nombre} — FALTA")
            faltantes.append(paquete)

    if faltantes:
        print("\n⚠ Dependencias faltantes:")
        print(f"  pip install {' '.join(faltantes)}")
        print("\n¿Desea continuar sin ellas? (puede que la API no funcione)")
        input("Presione Enter para continuar o Ctrl+C para salir...")

    # ── 3. Obtener configuración ───────────────────────────────────────────────────
    HOST = os.getenv("API_HOST", "127.0.0.1")
    PORT = int(os.getenv("API_PORT", "8000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

    print(f"\nConfiguración:")
    print(f"  Host: {HOST}")
    print(f"  Puerto: {PORT}")
    print(f"  Log Level: {LOG_LEVEL}")

    # ── 4. Iniciar servidor ────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("Iniciando servidor...")
    print("=" * 65)

    print("\nURLs disponibles:")
    print(f"  * Interfaz Web: http://{HOST}:{PORT}/")
    print(f"  * Swagger UI:   http://{HOST}:{PORT}/docs")
    print(f"  * ReDoc:        http://{HOST}:{PORT}/redoc")
    print("\nPresione Ctrl+C para detener el servidor")
    print("=" * 65 + "\n")

    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=HOST,
            port=PORT,
            reload=False,  # Desactivar reload para evitar problemas en Windows
            log_level=LOG_LEVEL,
        )
    except KeyboardInterrupt:
        print("\n\n✓ Servidor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error al iniciar el servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
