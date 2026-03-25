"""Script para explorar la estructura del CSV del Censo 2018."""
import pandas as pd

ruta = r"C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\CENSO 2018 dep\05_Antioquia_CSV\CNPV2018_5PER_A2_05.CSV"

print("=" * 80)
print("EXPLORACIÓN DE BASE DE DATOS - CENSO 2018 COLOMBIA")
print("=" * 80)

# Leer primeras 1000 filas para exploración
df = pd.read_csv(ruta, nrows=1000, low_memory=False)

print(f"\n📊 INFORMACIÓN GENERAL")
print(f"   Columnas totales: {len(df.columns)}")
print(f"   Filas en muestra: {len(df)}")
print(f"   Columnas: {df.columns.tolist()}")

print(f"\n📋 COLUMNAS PRINCIPALES PARA EL PROYECTO")
cols_interes = {
    'U_DPTO': 'Código departamento',
    'U_MPIO': 'Código municipio', 
    'P_SEXO': 'Sexo',
    'P_EDADR': 'Edad en años',
    'P_NIVEL_ANOSR': 'Nivel educativo (años)',
    'PA1_GRP_ETNIC': 'Pertenencia étnica',
    'P_ENFERMO': 'Enfermedad crónica',
    'P_EST_CIVIL': 'Estado civil',
    'P_TRABAJO': 'Trabajó la semana pasada',
    'P_ALFABETA': 'Sabe leer y escribir',
    'PA_ASISTENCIA': 'Asistencia educativa',
}

for col, descripcion in cols_interes.items():
    if col in df.columns:
        vals = sorted(df[col].dropna().unique())
        print(f"\n   {col} ({descripcion}):")
        print(f"      Valores únicos: {vals[:20]}{'...' if len(vals) > 20 else ''}")
        print(f"      Total únicos: {len(vals)}")
        print(f"      Nulos: {df[col].isna().sum()}")
    else:
        print(f"\n   {col} ({descripcion}): NO EXISTE")

print(f"\n📈 ESTADÍSTICAS DESCRIPTIVAS (EDAD)")
if 'P_EDADR' in df.columns:
    print(df['P_EDADR'].describe())

print(f"\n📈 DISTRIBUCIÓN POR SEXO")
if 'P_SEXO' in df.columns:
    print(df['P_SEXO'].value_counts())

print(f"\n📈 DISTRIBUCIÓN POR GRUPO ÉTNICO")
if 'PA1_GRP_ETNIC' in df.columns:
    print(df['PA1_GRP_ETNIC'].value_counts())

print("\n" + "=" * 80)
