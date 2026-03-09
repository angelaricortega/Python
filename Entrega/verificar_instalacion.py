#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ════════════════════════════════════════════════════════════════════════════════
# verificar_instalacion.py — Verifica que todo esté listo para ejecutar RiskAPI
# ════════════════════════════════════════════════════════════════════════════════

import sys
import os
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

def verificar_python():
    """Verifica versión de Python."""
    print("\n" + "=" * 65)
    print("  VERIFICACION DE INSTALACION - RiskAPI")
    print("=" * 65)
    
    version = sys.version_info
    print(f"\n[INFO] Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  [ADVERTENCIA] Python 3.10+ es recomendado (usa Pattern Matching)")
        return False
    print("  [OK] Version compatible")
    return True

def verificar_dependencias():
    """Verifica todas las dependencias."""
    print("\n" + "-" * 65)
    print("  DEPENDENCIAS")
    print("-" * 65)
    
    dependencias = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "requests": "Requests",
        "matplotlib": "Matplotlib",
        "seaborn": "Seaborn",
        "scipy": "SciPy",
        "dotenv": "python-dotenv",
    }
    
    todas_ok = True
    for paquete, nombre in dependencias.items():
        try:
            mod = __import__(paquete)
            version = getattr(mod, "__version__", "desconocida")
            print(f"  [OK] {nombre:15} v{version}")
        except ImportError:
            print(f"  [FALTA] {nombre:15}")
            todas_ok = False
    
    return todas_ok

def verificar_archivos():
    """Verifica archivos críticos."""
    print("\n" + "-" * 65)
    print("  ARCHIVOS CRITICOS")
    print("-" * 65)
    
    archivos = [
        "main.py",
        "modelos.py",
        "decorators.py",
        "config.py",
        "requirements.txt",
        "static/index.html",
        "static/style.css",
        "static/app.js",
    ]
    
    todos_ok = True
    for archivo in archivos:
        ruta = Path(archivo)
        if ruta.exists():
            size = ruta.stat().st_size
            print(f"  [OK] {archivo:25} ({size:,} bytes)")
        else:
            print(f"  [FALTA] {archivo:25}")
            todos_ok = False
    
    return todos_ok

def verificar_entorno():
    """Verifica variables de entorno."""
    print("\n" + "-" * 65)
    print("  VARIABLES DE ENTORNO")
    print("-" * 65)
    
    env_file = Path(".env")
    if env_file.exists():
        print(f"  [OK] .env encontrado")
        
        # Cargar y mostrar variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            vars = {
                "API_HOST": os.getenv("API_HOST", "no definida"),
                "API_PORT": os.getenv("API_PORT", "no definida"),
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "no definida"),
            }
            
            for key, value in vars.items():
                print(f"    - {key:15} = {value}")
        except ImportError:
            print(f"    [INFO] python-dotenv no instalado")
    else:
        print(f"  [INFO] .env no encontrado (usando valores por defecto)")
    
    return True

def verificar_directorios():
    """Verifica directorios necesarios."""
    print("\n" + "-" * 65)
    print("  DIRECTORIOS")
    print("-" * 65)
    
    directorios = ["static", "outputs"]
    
    for directorio in directorios:
        ruta = Path(directorio)
        if ruta.exists() and ruta.is_dir():
            print(f"  [OK] {directorio}/")
        else:
            print(f"  [INFO] {directorio}/ - No existe (creando...)")
            ruta.mkdir(exist_ok=True)
            print(f"    [OK] Creado")
    
    return True

def resumen(final_ok):
    """Muestra resumen final."""
    print("\n" + "=" * 65)
    
    if final_ok:
        print("  [EXITO] TODO LISTO PARA EJECUTAR!")
        print("=" * 65)
        print("\nSiguientes pasos:")
        print("  1. python start.py")
        print("  2. Abra http://127.0.0.1:8000 en su navegador")
        print("  3. Disfrute la interfaz!")
    else:
        print("  [ADVERTENCIA] HAY PROBLEMAS POR RESOLVER")
        print("=" * 65)
        print("\nAcciones requeridas:")
        print("  1. Instale dependencias: pip install -r requirements.txt")
        print("  2. Verifique archivos criticos")
        print("  3. Ejecute este script nuevamente")
    
    print()

def main():
    """Funcion principal."""
    resultados = []
    
    resultados.append(verificar_python())
    resultados.append(verificar_dependencias())
    resultados.append(verificar_archivos())
    resultados.append(verificar_entorno())
    resultados.append(verificar_directorios())
    
    final_ok = all(resultados)
    resumen(final_ok)
    
    return 0 if final_ok else 1

if __name__ == "__main__":
    sys.exit(main())
