"""
test_censo_upload.py — Script para probar la carga del Censo 2018.

Uso:
    python scripts/test_censo_upload.py

Requiere que la API esté corriendo en http://localhost:8000
"""

import httpx
from pathlib import Path
import time

# Configuración
API_BASE = "http://localhost:8000"
CSV_CENSO = Path(r"C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\CENSO 2018 dep\05_Antioquia_CSV\CNPV2018_5PER_A2_05.CSV")

def main():
    print("=" * 80)
    print("PRUEBA DE CARGA - CENSO 2018")
    print("=" * 80)
    
    # Verificar conexión
    print("\n1. Verificando conexión con la API...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_BASE}/")
            if response.status_code == 200:
                print(f"   ✓ API conectada: {response.json()}")
            else:
                print(f"   ✗ Error: {response.status_code}")
                return
    except httpx.RequestError as e:
        print(f"   ✗ Error de conexión: {e}")
        print("   💡 Asegúrese de ejecutar: uvicorn main:app --reload --port 8000")
        return
    
    # Verificar archivo
    print("\n2. Verificando archivo CSV...")
    if not CSV_CENSO.exists():
        print(f"   ✗ Archivo no encontrado: {CSV_CENSO}")
        return
    print(f"   ✓ Archivo encontrado: {CSV_CENSO}")
    
    # Calcular tamaño
    import os
    tamaño_mb = os.path.getsize(CSV_CENSO) / (1024 * 1024)
    print(f"   ✓ Tamaño: {tamaño_mb:.2f} MB")
    
    # Contar filas (estimado)
    print("\n3. Contando filas del CSV...")
    with open(CSV_CENSO, 'r', encoding='utf-8') as f:
        lineas = sum(1 for _ in f)
    print(f"   ✓ Filas totales (estimado): {lineas - 1}")  # -1 por el header
    
    # Preguntar si continuar
    print("\n⚠️  ADVERTENCIA: La carga de archivos grandes puede tomar varios minutos.")
    continuar = input("   ¿Desea continuar con la carga? (s/n): ").strip().lower()
    if continuar != 's':
        print("   Operación cancelada.")
        return
    
    # Cargar archivo
    print("\n4. Cargando archivo CSV...")
    print("   ⏳ Esto puede tomar varios minutos dependiendo del tamaño del archivo...")
    
    inicio = time.time()
    
    try:
        with open(CSV_CENSO, 'rb') as f:
            files = {'file': (CSV_CENSO.name, f, 'text/csv')}
            
            with httpx.Client(timeout=600.0) as client:  # 10 min timeout
                response = client.post(
                    f"{API_BASE}/censo-2018/upload-csv/",
                    files=files
                )
        
        duracion = time.time() - inicio
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   ✓ Carga completada en {duracion:.2f} segundos")
            print(f"   ✓ Total procesados: {data.get('total_procesados', 'N/A')}")
            print(f"   ✓ Exitosos: {data.get('exitosos', 'N/A')}")
            print(f"   ✓ Fallidos: {data.get('fallidos', 'N/A')}")
            
            if data.get('errores'):
                print(f"\n   ⚠️  Primeros errores ({len(data['errores'])} mostrados):")
                for err in data['errores'][:5]:
                    print(f"      - Fila {err.get('fila')}: {err.get('error', '')[:100]}")
        else:
            print(f"\n   ✗ Error en la carga: {response.status_code}")
            print(f"   Detalle: {response.text[:500]}")
    
    except httpx.ReadTimeout:
        print(f"\n   ✗ Timeout de lectura (la carga puede estar en progreso)")
        print(f"   💡 Intente consultar el estado en: {API_BASE}/censo-2018/estadisticas/")
    except httpx.RequestError as e:
        print(f"\n   ✗ Error de conexión: {e}")
    
    # Obtener estadísticas
    print("\n5. Obteniendo estadísticas...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_BASE}/censo-2018/estadisticas/")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"\n   ✓ Estadísticas obtenidas:")
                print(f"      - Total registros: {stats.get('total_registros', 'N/A'):,}")
                print(f"      - Edad promedio: {stats.get('edad_promedio', 'N/A')} años")
                print(f"      - Edad mediana: {stats.get('edad_mediana', 'N/A')} años")
                print(f"      - Rango de edades: {stats.get('edad_minima', 'N/A')} - {stats.get('edad_maxima', 'N/A')} años")
                
                if stats.get('distribucion_por_sexo'):
                    print(f"\n   ✓ Distribución por sexo:")
                    for sexo, count in stats['distribucion_por_sexo'].items():
                        print(f"      - {sexo}: {count:,}")
                
                if stats.get('distribucion_por_grupo_etnico'):
                    print(f"\n   ✓ Distribución por grupo étnico (top 5):")
                    for etnia, count in list(stats['distribucion_por_grupo_etnico'].items())[:5]:
                        print(f"      - {etnia}: {count:,}")
                
                if stats.get('indice_masculinidad') is not None:
                    print(f"\n   ✓ Índice de masculinidad: {stats['indice_masculinidad']}")
                
                if stats.get('indice_dependencia') is not None:
                    print(f"   ✓ Índice de dependencia: {stats['indice_dependencia']}")
            else:
                print(f"   ✗ Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 80)
    print("PRUEBA COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    main()
