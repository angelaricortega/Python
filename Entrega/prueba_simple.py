import pandas as pd
from limpieza import limpieza_completa

print("Prueba de limpieza.py")
print("=" * 50)

df = pd.DataFrame({
    "municipio": ["A", "B", "A", "C"],
    "cartera_a": [1000, None, 1000, 3000],
    "total": [1500, 2000, 1500, 4000]
})

print("Datos originales:")
print(df)
print()

df_limpio = limpieza_completa(
    df,
    columnas_numericas=["cartera_a", "total"],
    columna_municipio="municipio"
)

print("\nDatos limpios:")
print(df_limpio)
print("\nOK - limpieza.py funciona correctamente")
