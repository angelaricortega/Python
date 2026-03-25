"""
test_censo_rapido.py — Prueba rápida con subconjunto de datos del Censo 2018.

Carga solo las primeras 1000 filas para validar el funcionamiento.
"""

import httpx
import pandas as pd
import io
from pathlib import Path

# Configuración
API_BASE = "http://localhost:8000"
CSV_CENSO = Path(r"C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\CENSO 2018 dep\05_Antioquia_CSV\CNPV2018_5PER_A2_05.CSV")
MUESTRAS = 1000  # Número de filas para prueba

def main():
    print("=" * 80)
    print("PRUEBA RÁPIDA - CENSO 2018 (SUBCONJUNTO)")
    print("=" * 80)
    
    # Leer subconjunto de datos
    print(f"\n1. Leyendo {MUESTRAS} filas del CSV...")
    df = pd.read_csv(CSV_CENSO, nrows=MUESTRAS, low_memory=False)
    print(f"   ✓ Filas leídas: {len(df)}")
    print(f"   ✓ Columnas: {list(df.columns)[:10]}...")
    
    # Guardar en buffer
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)
    
    # Conectar a API
    print("\n2. Conectando a la API...")
    with httpx.Client(timeout=120.0) as client:
        response = client.get(f"{API_BASE}/")
        if response.status_code == 200:
            print(f"   ✓ API: {response.json()['estado']}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            return
        
        # Cargar archivo
        print(f"\n3. Cargando {len(df)} registros...")
        files = {'file': ('censo_muestra.csv', buffer, 'text/csv')}
        response = client.post(
            f"{API_BASE}/censo-2018/upload-csv/",
            files=files
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Carga completada")
            print(f"   ✓ Exitosos: {data.get('exitosos', 'N/A')}")
            print(f"   ✓ Fallidos: {data.get('fallidos', 'N/A')}")
            
            if data.get('errores'):
                print(f"   ⚠️  Errores ({len(data['errores'])}):")
                for err in data['errores'][:3]:
                    print(f"      - Fila {err.get('fila')}: {err.get('error', '')[:80]}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   Detalle: {response.text[:300]}")
            return
        
        # Obtener estadísticas
        print("\n4. Obteniendo estadísticas...")
        response = client.get(f"{API_BASE}/censo-2018/estadisticas/")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"\n   ✓ ESTADÍSTICAS:")
            print(f"      Total registros: {stats.get('total_registros', 'N/A'):,}")
            print(f"      Edad promedio: {stats.get('edad_promedio', 'N/A')} años")
            print(f"      Edad mediana: {stats.get('edad_mediana', 'N/A')} años")
            print(f"      Rango edades: {stats.get('edad_minima', 'N/A')} - {stats.get('edad_maxima', 'N/A')} años")
            
            if stats.get('distribucion_por_sexo'):
                print(f"\n      DISTRIBUCIÓN POR SEXO:")
                for sexo, count in stats['distribucion_por_sexo'].items():
                    print(f"         {sexo}: {count:,}")
            
            if stats.get('distribucion_por_grupo_etnico'):
                print(f"\n      DISTRIBUCIÓN POR GRUPO ÉTNICO:")
                for etnia, count in list(stats['distribucion_por_grupo_etnico'].items())[:5]:
                    print(f"         {etnia}: {count:,}")
            
            if stats.get('indice_masculinidad') is not None:
                print(f"\n      ÍNDICE DE MASCULINIDAD: {stats['indice_masculinidad']}")
            
            if stats.get('indice_dependencia') is not None:
                print(f"      ÍNDICE DE DEPENDENCIA: {stats['indice_dependencia']}")
            
            # Validar resultados
            print("\n5. VALIDACIÓN DE RESULTADOS:")
            total = stats.get('total_registros', 0)
            if total >= MUESTRAS * 0.9:  # Al menos 90% de los esperados
                print(f"   ✓ Total de registros correcto: {total:,} >= {int(MUESTRAS * 0.9):,}")
            else:
                print(f"   ✗ Total de registros bajo: {total:,} < {int(MUESTRAS * 0.9):,}")
            
            if stats.get('edad_promedio', 0) > 0:
                print(f"   ✓ Edad promedio calculada: {stats['edad_promedio']}")
            
            if stats.get('distribucion_por_sexo'):
                total_sexo = sum(stats['distribucion_por_sexo'].values())
                if total_sexo > 0:
                    print(f"   ✓ Distribución por sexo calculada: {total_sexo:,} registros")
            
            if stats.get('indice_masculinidad') is not None:
                print(f"   ✓ Índice de masculinidad calculado: {stats['indice_masculinidad']}")
            
            if stats.get('indice_dependencia') is not None:
                print(f"   ✓ Índice de dependencia calculado: {stats['indice_dependencia']}")
        else:
            print(f"   ✗ Error: {response.status_code}")
    
    print("\n" + "=" * 80)
    print("PRUEBA RÁPIDA COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    main()
