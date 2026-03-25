"""Script de diagnóstico para la API del Censo 2018."""
import httpx
import json

print("=" * 80)
print("DIAGNÓSTICO DE LA API - CENSO 2018")
print("=" * 80)

# 1. Health check
print("\n1. HEALTH CHECK:")
try:
    r = httpx.get("http://localhost:8000/", timeout=5)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
except Exception as e:
    print(f"   ERROR: {e}")

# 2. Estadísticas del Censo
print("\n2. ESTADÍSTICAS DEL CENSO:")
try:
    r = httpx.get("http://localhost:8000/censo-2018/estadisticas/", timeout=60)
    print(f"   Status: {r.status_code}")
    
    if r.status_code != 200:
        print(f"   ERROR HTTP: {r.status_code}")
        print(f"   Response: {r.text[:500]}")
    else:
        d = r.json()
        print(f"   ✓ Response OK")
        print(f"   Keys: {list(d.keys())}")
        print(f"   Total registros: {d.get('total_registros', 0):,}")
        print(f"   Grupos de edad: {len(d.get('distribucion_por_grupos_edad', {}))}")
        print(f"   Rangos de edad: {len(d.get('distribucion_por_rangos_edad', {}))}")
        print(f"   Índice masculinidad: {d.get('indice_masculinidad')}")
        print(f"   Índice dependencia: {d.get('indice_dependencia')}")
        
        # Guardar JSON para inspección
        with open("diagnostico_censo.json", "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print(f"\n   ✓ JSON guardado en: diagnostico_censo.json")
        
except httpx.TimeoutException:
    print("   ERROR: Timeout - la API no respondió en 60 segundos")
except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
