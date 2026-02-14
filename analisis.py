"""
analisis.py - Análisis de Riesgo Crediticio - Sistema Financiero Colombiano
Autor: Angela Rico - sebastian Ramirez
Módulo: Fundamentos - Proyecto Fase 1 - Semana 1

Este script realiza:
1. ANÁLISIS EXPLORATORIO (EDA) para justificar decisiones
2. LIMPIEZA de datos basada en hallazgos del EDA
3. CÁLCULO de métricas de riesgo crediticio
4. VISUALIZACIONES profesionales
5. EXPORTACIÓN de resultados
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Tuple, List, Dict, Any
import requests
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Importar decoradores personalizados
from decorators import timer, log_execution, validar_dataframe

# =============================================================================
# CONFIGURACIÓN PROFESIONAL DE VISUALIZACIÓN
# =============================================================================

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")

# Configuración de fuentes y tamaños para gráficos profesionales
plt.rcParams.update({
    'figure.figsize': (16, 10),
    'figure.dpi': 150,
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.labelsize': 13,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.titlesize': 18,
    'figure.titleweight': 'bold'
})

# Crear carpetas para outputs
os.makedirs('outputs/graficos', exist_ok=True)
os.makedirs('outputs/datos', exist_ok=True)
os.makedirs('outputs/reportes', exist_ok=True)


# =============================================================================
# 1. ANÁLISIS EXPLORATORIO DE DATOS (EDA) - Justifica cada decisión
# =============================================================================

@timer
@log_execution
def analisis_exploratorio_inicial(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Realiza análisis exploratorio detallado para JUSTIFICAR decisiones de limpieza.
    
    Este EDA responde:
    - ¿Qué columnas tenemos? ¿Cuáles son relevantes?
    - ¿Hay valores nulos? ¿Cómo tratarlos?
    - ¿Qué columnas son numéricas? ¿Cuáles necesitan conversión?
    - ¿Hay valores extremos? ¿Cómo detectarlos?
    - ¿La distribución de datos justifica transformaciones?
    
    Returns:
        Dict con insights del EDA que guían la limpieza
    """
    print("\n" + "="*80)
    print(" 🔍 ANÁLISIS EXPLORATORIO DE DATOS (EDA) ".center(80, "="))
    print("="*80)
    
    insights = {}
    
    # 1.1 DIMENSIONES Y ESTRUCTURA
    print("\n📊 1. DIMENSIONES DEL DATASET:")
    print(f"   • Filas: {df.shape[0]:,} registros")
    print(f"   • Columnas: {df.shape[1]} variables")
    insights['n_filas'] = df.shape[0]
    insights['n_columnas'] = df.shape[1]
    
    # 1.2 TIPOS DE DATOS - JUSTIFICA CONVERSIONES
    print("\n📋 2. TIPOS DE DATOS (justifica conversiones):")
    dtypes_count = df.dtypes.value_counts()
    for dtype, count in dtypes_count.items():
        pct = (count / df.shape[1]) * 100
        print(f"   • {dtype}: {count} columnas ({pct:.1f}%)")
    insights['tipos_datos'] = {str(k): v for k, v in dtypes_count.to_dict().items()}
    
    # 1.3 COLUMNAS RELEVANTES PARA ANÁLISIS DE RIESGO
    print("\n🎯 3. COLUMNAS RELEVANTES IDENTIFICADAS:")
    columnas_riesgo = [col for col in df.columns if any(x in col.lower() 
                      for x in ['riesgo', 'cartera', 'credito', 'deposito'])]
    
    for i, col in enumerate(columnas_riesgo[:10]):  # Mostrar primeras 10
        print(f"   • {col}")
    if len(columnas_riesgo) > 10:
        print(f"   • ... y {len(columnas_riesgo) - 10} más")
    insights['columnas_relevantes'] = len(columnas_riesgo)
    
    # 1.4 VALORES NULOS - ¡CRÍTICO PARA LIMPIEZA!
    print("\n❓ 4. ANÁLISIS DE VALORES NULOS (justifica tratamiento de missing):")
    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0].sort_values(ascending=False)
    
    if len(nulos) > 0:
        print(f"   • {len(nulos)} columnas con valores nulos")
        print("\n   Top 10 columnas con más nulos:")
        for col, val in nulos.head(10).items():
            pct = (val / len(df)) * 100
            print(f"     - {col}: {val:,} nulos ({pct:.1f}%)")
        
        # Decisión basada en EDA
        if (nulos / len(df)).max() > 0.3:
            print("\n   🔴 DECISIÓN: Columnas con >30% nulos serán evaluadas para eliminación")
        else:
            print("\n   🟢 DECISIÓN: Nulos manejables con errors='coerce' en conversión")
        
        insights['columnas_con_nulos'] = len(nulos)
        insights['max_pct_nulos'] = (nulos.max() / len(df)) * 100
    else:
        print("   ✅ Sin valores nulos")
        insights['columnas_con_nulos'] = 0
    
    # 1.5 COLUMNAS NUMÉRICAS POTENCIALES
    print("\n🔢 5. IDENTIFICACIÓN DE COLUMNAS NUMÉRICAS:")
    numericas_potenciales = []
    no_numericas = []
    
    for col in df.columns:
        # Tomar muestra para prueba rápida
        muestra = df[col].dropna().iloc[:100] if len(df) > 100 else df[col].dropna()
        try:
            pd.to_numeric(muestra, errors='coerce')
            numericas_potenciales.append(col)
        except:
            no_numericas.append(col)
    
    print(f"   • {len(numericas_potenciales)} columnas convertibles a numérico")
    print(f"   • {len(no_numericas)} columnas no numéricas (fechas, texto, etc.)")
    insights['columnas_numericas_potenciales'] = len(numericas_potenciales)
    
    # 1.6 MUESTRA DE DATOS
    print("\n👀 6. VISTA PREVIA (primeras 3 filas):")
    print(df.head(3).to_string())
    
    # 1.7 ESTADÍSTICAS DESCRIPTIVAS INICIALES
    print("\n📈 7. ESTADÍSTICAS DESCRIPTIVAS INICIALES:")
    
    # Buscar columnas numéricas para mostrar estadísticas
    cols_estadisticas = [col for col in df.columns[:10] 
                        if col in numericas_potenciales[:5]]
    
    if cols_estadisticas:
        print(df[cols_estadisticas].describe().to_string())
        
        # Detección de outliers
        for col in cols_estadisticas[:3]:  # Primeras 3 columnas
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = df[(df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)]
            pct_outliers = (len(outliers) / len(df)) * 100
            print(f"\n   • {col}: {pct_outliers:.1f}% valores atípicos (IQR)")
    
    # 1.8 RESUMEN DE DECISIONES DE LIMPIEZA
    print("\n" + "="*80)
    print(" 📋 DECISIONES DE LIMPIEZA BASADAS EN EDA ".center(80, "="))
    print("="*80)
    
    decisiones = [
        "1. Renombrar columnas a nombres cortos y consistentes (mejor legibilidad)",
        f"2. Convertir {len(numericas_potenciales)} columnas a tipo numérico (basado en identificación)",
        "3. Usar errors='coerce' para manejar valores no numéricos (basado en detección de nulos)",
        "4. Crear métricas derivadas: índice de riesgo, ratio provisiones, etc.",
        "5. Filtrar valores extremos usando percentiles (basado en detección de outliers)",
        "6. Mantener columnas de municipio y fecha para análisis temporal/geográfico"
    ]
    
    for decision in decisiones:
        print(f"   {decision}")
    
    print("\n" + "="*80)
    print(" ✅ EDA COMPLETADO - Decisiones de limpieza justificadas ".center(80, "="))
    print("="*80 + "\n")
    
    return insights


# =============================================================================
# 2. DESCARGA DE DATOS
# =============================================================================

@timer
@log_execution
def descargar_datos(url: str = "https://www.datos.gov.co/api/views/u2wk-tfe3/rows.csv?accessType=DOWNLOAD") -> Optional[pd.DataFrame]:
    """
    Descarga datos de captaciones y colocaciones.
    
    Args:
        url: URL del dataset en Datos Abiertos Colombia
        
    Returns:
        DataFrame con los datos o None si hay error
    """
    print("🌐 Iniciando descarga desde Datos Abiertos Colombia...")
    
    try:
        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        df = pd.read_csv(url, storage_options=headers)
        
        print(f"✅ Descarga exitosa:")
        print(f"   • {len(df):,} registros")
        print(f"   • {len(df.columns)} columnas")
        print(f"   • Tamaño aproximado: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
        
        return df
        
    except Exception as e:
        print(f"❌ Error en descarga: {e}")
        return None


# =============================================================================
# 3. LIMPIEZA Y PREPARACIÓN DE DATOS (Basada en hallazgos del EDA)
# =============================================================================

@timer
@log_execution
@validar_dataframe(columnas_requeridas=['Cartera de créditos'])
def preparar_datos(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], Dict[str, Any]]:
    """
    Limpia y prepara los datos para análisis de riesgo.
    
    Decisiones basadas en EDA:
    - Renombrar columnas para consistencia
    - Convertir a numérico con manejo de errores
    - Crear métricas derivadas de riesgo
    - Identificar columnas útiles para análisis
    
    Args:
        df: DataFrame crudo
        
    Returns:
        Tuple[DataFrame limpio, Lista columnas numéricas, Diccionario métricas de limpieza]
    """
    print("\n🛠️  INICIANDO PROCESO DE LIMPIEZA...")
    
    df_clean = df.copy()
    metricas_limpieza = {
        'registros_iniciales': len(df),
        'columnas_iniciales': len(df.columns)
    }
    
    # 3.1 RENOMBRAR COLUMNAS (basado en identificación de relevantes)
    print("\n   📝 Renombrando columnas para consistencia...")
    columnas_rename = {
        'Código del departamento': 'cod_depto',
        'Código del municipio': 'cod_municipio',
        'Nombre del municipio': 'municipio',
        'Fecha de Corte': 'fecha',
        'Cartera de créditos': 'cartera_total',
        'Depósitos en cuenta corriente bancaria': 'dep_corriente',
        'Depósitos simples': 'dep_simples',
        'Certificados de depósito a término': 'cdts',
        'Depósitos de ahorro': 'dep_ahorro',
        'Categoría A riesgo normal': 'riesgo_a',
        'Categoría B riesgo aceptable': 'riesgo_b',
        'Categoría C riesgo apreciable': 'riesgo_c',
        'Categoría D riesgo significativo': 'riesgo_d',
        'Categoría E riesgo de Incobrabilidad': 'riesgo_e',
        'Créditos de vivienda': 'cred_vivienda',
        'Provisión créditos de vivienda': 'prov_vivienda',
        'Provisión créditos de consumo': 'prov_consumo',
        'Provisión microcréditos': 'prov_micro',
        'Provisión general': 'prov_general'
    }
    
    # Solo renombrar columnas que existen
    rename_dict = {k: v for k, v in columnas_rename.items() if k in df_clean.columns}
    df_clean = df_clean.rename(columns=rename_dict)
    metricas_limpieza['columnas_renombradas'] = len(rename_dict)
    
    # 3.2 CONVERTIR A NUMÉRICO (basado en identificación de numéricas potenciales)
    print("\n   🔢 Convirtiendo columnas a tipo numérico...")
    columnas_texto = ['cod_depto', 'cod_municipio', 'municipio', 'fecha']
    cols_numericas = []
    errores_conversion = 0
    
    for col in df_clean.columns:
        if col not in columnas_texto:
            try:
                # Intentar conversión, valores no convertibles -> NaN
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                cols_numericas.append(col)
            except:
                errores_conversion += 1
    
    metricas_limpieza['columnas_numericas'] = len(cols_numericas)
    metricas_limpieza['errores_conversion'] = errores_conversion
    
    print(f"      • {len(cols_numericas)} columnas convertidas a numérico")
    print(f"      • {errores_conversion} columnas no convertibles (texto/fechas)")
    
    # 3.3 CONVERTIR FECHA (si existe)
    if 'fecha' in df_clean.columns:
        print("\n   📅 Procesando fechas...")
        df_clean['fecha'] = pd.to_datetime(df_clean['fecha'], errors='coerce')
        fechas_validas = df_clean['fecha'].notna().sum()
        print(f"      • {fechas_validas:,} fechas válidas")
    
    # 3.4 CREAR MÉTRICAS DE RIESGO (basado en disponibilidad de columnas)
    print("\n   📊 Creando métricas derivadas de riesgo...")
    
    # Índice de riesgo alto (C+D+E)
    columnas_riesgo_alto = ['riesgo_c', 'riesgo_d', 'riesgo_e']
    cols_existentes = [c for c in columnas_riesgo_alto if c in df_clean.columns]
    
    if cols_existentes:
        df_clean['cartera_riesgo_alto'] = df_clean[cols_existentes].sum(axis=1)
        df_clean['indice_riesgo'] = df_clean['cartera_riesgo_alto'] / df_clean['cartera_total'].replace(0, np.nan)
        print(f"      • Índice de riesgo creado usando: {cols_existentes}")
    
    # Depósitos totales
    cols_depositos = ['dep_corriente', 'dep_simples', 'cdts', 'dep_ahorro']
    cols_dep_existentes = [c for c in cols_depositos if c in df_clean.columns]
    
    if cols_dep_existentes:
        df_clean['depositos_totales'] = df_clean[cols_dep_existentes].sum(axis=1)
        print(f"      • Depósitos totales creados usando: {cols_dep_existentes}")
    
    # Ratio de liquidez (captaciones/colocaciones)
    if 'depositos_totales' in df_clean.columns and 'cartera_total' in df_clean.columns:
        df_clean['ratio_liquidez'] = df_clean['depositos_totales'] / df_clean['cartera_total'].replace(0, np.nan)
        print(f"      • Ratio de liquidez creado")
    
    # 3.5 ELIMINAR VALORES EXTREMOS (basado en detección de outliers)
    print("\n   📉 Detectando y manejando valores extremos...")
    registros_antes = len(df_clean)
    
    for col in ['indice_riesgo', 'ratio_liquidez']:
        if col in df_clean.columns:
            q1, q99 = df_clean[col].quantile([0.01, 0.99])
            df_clean = df_clean[(df_clean[col] >= q1) & (df_clean[col] <= q99)]
    
    registros_despues = len(df_clean)
    metricas_limpieza['registros_eliminados'] = registros_antes - registros_despues
    metricas_limpieza['pct_eliminados'] = ((registros_antes - registros_despues) / registros_antes) * 100
    
    print(f"      • {metricas_limpieza['registros_eliminados']:,} registros eliminados ({metricas_limpieza['pct_eliminados']:.1f}%)")
    
    metricas_limpieza['registros_finales'] = len(df_clean)
    
    print(f"\n✅ LIMPIEZA COMPLETADA:")
    print(f"   • {metricas_limpieza['registros_finales']:,} registros finales")
    print(f"   • {len(cols_numericas)} columnas numéricas disponibles")
    
    return df_clean, cols_numericas, metricas_limpieza


# =============================================================================
# 4. ANÁLISIS DESCRIPTIVO Y MÉTRICAS
# =============================================================================

@timer
def calcular_metricas(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula métricas estadísticas del análisis.
    
    Args:
        df: DataFrame limpio
        
    Returns:
        Diccionario con métricas calculadas
    """
    print("\n📈 CALCULANDO MÉTRICAS ESTADÍSTICAS...")
    
    metricas = {}
    
    # 4.1 Métricas de riesgo
    if 'indice_riesgo' in df.columns:
        datos_riesgo = df['indice_riesgo'].dropna()
        metricas['riesgo'] = {
            'media': datos_riesgo.mean(),
            'mediana': datos_riesgo.median(),
            'desviacion': datos_riesgo.std(),
            'min': datos_riesgo.min(),
            'max': datos_riesgo.max(),
            'q25': datos_riesgo.quantile(0.25),
            'q75': datos_riesgo.quantile(0.75),
            'pct_cero': (datos_riesgo == 0).mean() * 100
        }
    
    # 4.2 Métricas de cartera
    if 'cartera_total' in df.columns:
        cartera = df['cartera_total']
        metricas['cartera'] = {
            'total': cartera.sum(),
            'promedio': cartera.mean(),
            'mediana': cartera.median(),
            'total_formateado': f"${cartera.sum():,.0f}"
        }
    
    # 4.3 Métricas de liquidez
    if 'ratio_liquidez' in df.columns:
        liquidez = df['ratio_liquidez'].dropna()
        metricas['liquidez'] = {
            'media': liquidez.mean(),
            'mediana': liquidez.median(),
            'pct_mayor_1': (liquidez > 1).mean() * 100
        }
    
    # 4.4 Top municipios
    if 'municipio' in df.columns and 'cartera_total' in df.columns:
        top_municipios = df.groupby('municipio')['cartera_total'].sum().nlargest(10)
        metricas['top_municipios'] = top_municipios.to_dict()
    
    print("✅ Métricas calculadas")
    return metricas


# =============================================================================
# 5. VISUALIZACIONES PROFESIONALES
# =============================================================================

@timer
def generar_graficos(df: pd.DataFrame, metricas: Dict[str, Any]) -> None:
    """
    Genera visualizaciones profesionales del análisis.
    Guarda cada gráfico por separado Y un collage completo.
    
    Args:
        df: DataFrame limpio
        metricas: Diccionario con métricas calculadas
    """
    print("\n🎨 GENERANDO VISUALIZACIONES PROFESIONALES...")
    
    # Configurar estilo profesional
    sns.set_style("whitegrid")
    sns.set_palette("viridis")
    
    # Asegurar que existe la carpeta
    os.makedirs('outputs/graficos', exist_ok=True)
    
    # =========================================================================
    # GRÁFICO 1: Distribución del Índice de Riesgo
    # =========================================================================
    print("   📊 Generando gráfico 1/4: Distribución de riesgo...")
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    
    if 'indice_riesgo' in df.columns:
        datos = df['indice_riesgo'].dropna()
        
        # Histograma con KDE
        sns.histplot(datos, bins=50, kde=True, ax=ax1, 
                    color='#2E86AB', alpha=0.6, edgecolor='white', linewidth=0.5)
        
        # Líneas de estadísticas
        ax1.axvline(datos.mean(), color='#A23B72', linestyle='--', linewidth=2.5,
                   label=f'Media: {datos.mean():.3f}')
        ax1.axvline(datos.median(), color='#F18F01', linestyle='-', linewidth=2.5,
                   label=f'Mediana: {datos.median():.3f}')
        
        # Sombrear región de alto riesgo (>1%)
        ax1.axvspan(0.01, datos.max(), alpha=0.2, color='red', label='Riesgo >1%')
        
        ax1.set_xlabel('Índice de Riesgo (C+D+E)/Cartera Total', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frecuencia', fontsize=12, fontweight='bold')
        ax1.set_title('📊 Distribución del Índice de Riesgo Crediticio', 
                     fontsize=16, fontweight='bold', pad=20)
        ax1.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
        
        # Formato de ejes
        ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
        
        # Texto explicativo
        texto = f"Distribución sesgada a la izquierda\n{metricas.get('riesgo', {}).get('pct_cero', 0):.1f}% de municipios con riesgo 0"
        ax1.text(0.98, 0.95, texto, transform=ax1.transAxes, 
                fontsize=10, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Guardar gráfico individual
        plt.savefig('outputs/graficos/01_distribucion_riesgo.png', 
                    dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig1)
        print("      ✅ Guardado: 01_distribucion_riesgo.png")
    
    # =========================================================================
    # GRÁFICO 2: Top 10 Municipios por Cartera
    # =========================================================================
    print("   📊 Generando gráfico 2/4: Top municipios...")
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    
    if 'top_municipios' in metricas:
        top = pd.Series(metricas['top_municipios'])
        
        # Crear colores degradados
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(top)))
        
        # Gráfico de barras horizontal
        bars = ax2.barh(range(len(top)), top.values, color=colors)
        
        # Añadir etiquetas con valores
        for i, (bar, val) in enumerate(zip(bars, top.values)):
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2, 
                    f'  ${width:,.0f}', ha='left', va='center', fontsize=10, fontweight='bold')
        
        ax2.set_yticks(range(len(top)))
        ax2.set_yticklabels(top.index, fontsize=11)
        ax2.set_xlabel('Cartera Total ($)', fontsize=12, fontweight='bold')
        ax2.set_title('🏆 Top 10 Municipios por Cartera Crediticia', 
                     fontsize=16, fontweight='bold', pad=20)
        
        # Formato de eje x en miles de millones
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e12:.1f}B'))
        
        # Añadir línea de promedio
        total_sistema = metricas.get('cartera', {}).get('total', 0)
        ax2.axvline(total_sistema/10, color='red', linestyle='--', alpha=0.5, 
                   label='Promedio top 10')
        ax2.legend()
        
        # Guardar gráfico individual
        plt.savefig('outputs/graficos/02_top_municipios.png', 
                    dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig2)
        print("      ✅ Guardado: 02_top_municipios.png")
    
    # =========================================================================
    # GRÁFICO 3: Boxplot de Riesgo por Quintiles
    # =========================================================================
    print("   📊 Generando gráfico 3/4: Boxplot por quintiles...")
    fig3, ax3 = plt.subplots(figsize=(12, 8))
    
    if 'cartera_total' in df.columns and 'indice_riesgo' in df.columns:
        # Crear quintiles por tamaño de cartera
        df_temp = df[['cartera_total', 'indice_riesgo']].dropna().copy()
        df_temp['quintil'] = pd.qcut(df_temp['cartera_total'], q=5, 
                                     labels=['Q1 (Menor)', 'Q2', 'Q3', 'Q4', 'Q5 (Mayor)'])
        
        # Boxplot
        sns.boxplot(data=df_temp, x='quintil', y='indice_riesgo', ax=ax3, 
                   palette='RdYlGn_r', fliersize=2, linewidth=1.5)
        
        ax3.set_xlabel('Tamaño de Cartera (Quintiles)', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Índice de Riesgo', fontsize=12, fontweight='bold')
        ax3.set_title('📦 Distribución de Riesgo por Tamaño de Cartera', 
                     fontsize=16, fontweight='bold', pad=20)
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
        
        # Rotar etiquetas para mejor lectura
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=15)
        
        # Test estadístico
        try:
            from scipy import stats
            q1_data = df_temp[df_temp['quintil'] == 'Q1 (Menor)']['indice_riesgo'].dropna()
            q5_data = df_temp[df_temp['quintil'] == 'Q5 (Mayor)']['indice_riesgo'].dropna()
            stat, p_value = stats.mannwhitneyu(q1_data, q5_data, alternative='two-sided')
            
            texto = f"Test Mann-Whitney: p={p_value:.4f}\n{'✅ Diferencia significativa' if p_value < 0.05 else '❌ Sin diferencia'}"
        except:
            # Si no hay scipy, cálculo manual
            q1_media = q1_data.mean()
            q5_media = q5_data.mean()
            diferencia_pct = abs(q1_media - q5_media) / max(q1_media, q5_media) * 100
            texto = f"Diferencia entre grupos: {diferencia_pct:.1f}%\n{'✅ Diferencia significativa' if diferencia_pct > 20 else '⚠️ Diferencia moderada'}"
        
        ax3.text(0.05, 0.95, texto, transform=ax3.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Guardar gráfico individual
        plt.savefig('outputs/graficos/03_boxplot_riesgo.png', 
                    dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig3)
        print("      ✅ Guardado: 03_boxplot_riesgo.png")
    
    # =========================================================================
    # GRÁFICO 4: Composición de Cartera por Riesgo
    # =========================================================================
    print("   📊 Generando gráfico 4/4: Composición de riesgo...")
    fig4, ax4 = plt.subplots(figsize=(12, 8))
    
    categorias_riesgo = ['riesgo_a', 'riesgo_b', 'riesgo_c', 'riesgo_d', 'riesgo_e']
    cols_existentes = [c for c in categorias_riesgo if c in df.columns]
    
    if cols_existentes:
        # Calcular porcentajes
        total_riesgo = df[cols_existentes].sum().sum()
        valores = [df[col].sum() / total_riesgo * 100 for col in cols_existentes]
        labels = ['A - Normal', 'B - Aceptable', 'C - Apreciable', 
                 'D - Significativo', 'E - Incobrable']
        
        # Colores para cada categoría
        colors = ['#2ECC71', '#F1C40F', '#E67E22', '#E74C3C', '#C0392B']
        
        # Crear gráfico de torta
        wedges, texts, autotexts = ax4.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90, 
                                           wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        
        # Mejorar formato de porcentajes
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')
        
        ax4.set_title('🥧 Composición de Cartera por Categoría de Riesgo', 
                     fontsize=16, fontweight='bold', pad=20)
        
        # Destacar categorías de alto riesgo
        alto_riesgo = sum(valores[2:])  # C+D+E
        ax4.text(0, -1.2, f'⚠️ Cartera de Alto Riesgo (C+D+E): {alto_riesgo:.1f}%', 
                ha='center', fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='red', alpha=0.1))
        
        # Guardar gráfico individual
        plt.savefig('outputs/graficos/04_composicion_riesgo.png', 
                    dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig4)
        print("      ✅ Guardado: 04_composicion_riesgo.png")
    
    # =========================================================================
    # COLLAGE COMPLETO (todos los gráficos juntos)
    # =========================================================================
    print("   🖼️  Generando collage completo...")
    
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)
    
    # Re-crear cada gráfico en el collage
    # (código del collage - similar al anterior pero en subplots)
    
    ax1 = fig.add_subplot(gs[0, 0])
    if 'indice_riesgo' in df.columns:
        datos = df['indice_riesgo'].dropna()
        sns.histplot(datos, bins=50, kde=True, ax=ax1, color='#2E86AB', alpha=0.6)
        ax1.axvline(datos.mean(), color='#A23B72', linestyle='--', linewidth=2, label=f'Media: {datos.mean():.3f}')
        ax1.axvline(datos.median(), color='#F18F01', linestyle='-', linewidth=2, label=f'Mediana: {datos.median():.3f}')
        ax1.set_title('Distribución del Índice de Riesgo', fontsize=14, fontweight='bold')
        ax1.legend()
    
    ax2 = fig.add_subplot(gs[0, 1])
    if 'top_municipios' in metricas:
        top = pd.Series(metricas['top_municipios'])
        top.plot(kind='barh', ax=ax2, color=plt.cm.Blues(np.linspace(0.4, 0.9, len(top))))
        ax2.set_title('Top 10 Municipios por Cartera', fontsize=14, fontweight='bold')
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e12:.1f}B'))
    
    ax3 = fig.add_subplot(gs[1, 0])
    if 'cartera_total' in df.columns and 'indice_riesgo' in df.columns:
        df_temp = df[['cartera_total', 'indice_riesgo']].dropna().copy()
        df_temp['quintil'] = pd.qcut(df_temp['cartera_total'], q=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
        sns.boxplot(data=df_temp, x='quintil', y='indice_riesgo', ax=ax3, palette='RdYlGn_r')
        ax3.set_title('Riesgo por Tamaño de Cartera', fontsize=14, fontweight='bold')
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
    
    ax4 = fig.add_subplot(gs[1, 1])
    if cols_existentes:
        valores = [df[col].sum() for col in cols_existentes]
        ax4.pie(valores, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax4.set_title('Composición por Riesgo', fontsize=14, fontweight='bold')
    
    plt.suptitle('📊 ANÁLISIS DE RIESGO CREDITICIO - SISTEMA FINANCIERO COLOMBIANO', 
                fontsize=18, fontweight='bold', y=1.02)
    
    plt.savefig('outputs/graficos/00_collage_completo.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('outputs/graficos/00_collage_completo.pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("      ✅ Guardado: 00_collage_completo.png y .pdf")
    
    print(f"\n✅ TODOS LOS GRÁFICOS GUARDADOS EN: outputs/graficos/")
    print("   📁 Archivos generados:")
    print("      • 01_distribucion_riesgo.png")
    print("      • 02_top_municipios.png") 
    print("      • 03_boxplot_riesgo.png")
    print("      • 04_composicion_riesgo.png")
    print("      • 00_collage_completo.png (todos juntos)")

    # =============================================================================
# 6. REPORTE DE RESULTADOS
# =============================================================================

def generar_reporte(metricas_eda: Dict, metricas_limpieza: Dict, 
                   metricas_analisis: Dict, df: pd.DataFrame) -> str:
    """
    Genera reporte completo del análisis.
    """
    reporte = []
    reporte.append("\n" + "="*80)
    reporte.append(" 📋 REPORTE FINAL DE ANÁLISIS DE RIESGO CREDITICIO ".center(80, "="))
    reporte.append("="*80)
    
    # 1. RESUMEN EJECUTIVO
    reporte.append("\n🎯 1. RESUMEN EJECUTIVO")
    reporte.append("-" * 40)
    reporte.append(f"📅 Fecha análisis: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    reporte.append(f"📊 Registros analizados: {len(df):,}")
    reporte.append(f"📈 Cartera total sistema: ${df['cartera_total'].sum():,.0f}")
    
    if 'indice_riesgo' in df.columns:
        riesgo_medio = df['indice_riesgo'].mean()
        reporte.append(f"⚠️  Riesgo promedio: {riesgo_medio:.2%}")
    
    # 2. HALLAZGOS DEL EDA
    reporte.append("\n🔍 2. HALLAZGOS DEL ANÁLISIS EXPLORATORIO")
    reporte.append("-" * 40)
    for key, value in metricas_eda.items():
        if isinstance(value, float):
            reporte.append(f"   • {key}: {value:.2f}")
        else:
            reporte.append(f"   • {key}: {value}")
    
    # 3. PROCESO DE LIMPIEZA
    reporte.append("\n🧹 3. PROCESO DE LIMPIEZA")
    reporte.append("-" * 40)
    for key, value in metricas_limpieza.items():
        if isinstance(value, float):
            reporte.append(f"   • {key}: {value:.2f}")
        else:
            reporte.append(f"   • {key}: {value}")
    
    # 4. MÉTRICAS DE RIESGO
    reporte.append("\n📊 4. MÉTRICAS DE RIESGO")
    reporte.append("-" * 40)
    
    if 'riesgo' in metricas_analisis:
        for key, value in metricas_analisis['riesgo'].items():
            if isinstance(value, float):
                if 'pct' in key:
                    reporte.append(f"   • {key}: {value:.1f}%")
                else:
                    reporte.append(f"   • {key}: {value:.4f}")
    
    # 5. CONCLUSIONES
    reporte.append("\n💡 5. CONCLUSIONES Y RECOMENDACIONES")
    reporte.append("-" * 40)
    
    if 'riesgo' in metricas_analisis:
        riesgo_medio = metricas_analisis['riesgo']['media']
        if riesgo_medio < 0.03:
            reporte.append("   ✅ SISTEMA SÓLIDO: Bajo nivel de cartera problemática")
        elif riesgo_medio < 0.06:
            reporte.append("   ⚠️ RIESGO MODERADO: Nivel controlable")
        else:
            reporte.append("   🔴 ALERTA: Alto porcentaje de cartera deteriorada")
    
    if 'liquidez' in metricas_analisis:
        liq_mediana = metricas_analisis['liquidez']['mediana']
        if liq_mediana > 1.1:
            reporte.append("   💧 ALTA LIQUIDEZ: Exceso de captaciones")
        elif liq_mediana > 0.9:
            reporte.append("   ⚖️ LIQUIDEZ EQUILIBRADA")
        else:
            reporte.append("   🔴 TENSIÓN DE LIQUIDEZ: Colocaciones superan captaciones")
    
    reporte.append("\n" + "="*80)
    reporte.append(" 🎯 ANÁLISIS COMPLETADO EXITOSAMENTE ".center(80, "="))
    reporte.append("="*80)
    
    reporte_texto = "\n".join(reporte)
    
    # Guardar reporte
    with open('outputs/reportes/reporte_final.txt', 'w', encoding='utf-8') as f:
        f.write(reporte_texto)
    
    return reporte_texto


# =============================================================================
# 7. FUNCIÓN PRINCIPAL
# =============================================================================

@timer
def main():
    """
    Función principal que orquesta todo el análisis.
    """
    print("\n" + "="*80)
    print(" 🏦 ANÁLISIS DE RIESGO CREDITICIO ".center(80, "="))
    print(" Sistema Financiero Colombiano - Datos Abiertos ".center(80))
    print("="*80 + "\n")
    
    # 7.1 DESCARGA DE DATOS
    print("\n📥 FASE 1: DESCARGA DE DATOS")
    print("-" * 40)
    df = descargar_datos()
    if df is None:
        print("❌ No se pudo descargar los datos. Abortando.")
        return
    
    # 7.2 ANÁLISIS EXPLORATORIO (JUSTIFICA LIMPIEZA)
    print("\n🔍 FASE 2: ANÁLISIS EXPLORATORIO (EDA)")
    print("-" * 40)
    insights_eda = analisis_exploratorio_inicial(df)
    
    # 7.3 LIMPIEZA DE DATOS (BASADA EN EDA)
    print("\n🧹 FASE 3: LIMPIEZA DE DATOS")
    print("-" * 40)
    df_clean, cols_numericas, metricas_limpieza = preparar_datos(df)
    
    # 7.4 CÁLCULO DE MÉTRICAS
    print("\n📊 FASE 4: CÁLCULO DE MÉTRICAS")
    print("-" * 40)
    metricas = calcular_metricas(df_clean)
    
    # 7.5 VISUALIZACIONES
    print("\n🎨 FASE 5: VISUALIZACIONES")
    print("-" * 40)
    generar_graficos(df_clean, metricas)
    
    # 7.6 REPORTE FINAL
    print("\n📋 FASE 6: GENERACIÓN DE REPORTE")
    print("-" * 40)
    reporte = generar_reporte(insights_eda, metricas_limpieza, metricas, df_clean)
    print(reporte)
    
    # 7.7 EXPORTAR DATOS PROCESADOS
    df_clean.to_csv('outputs/datos/datos_procesados.csv', index=False, encoding='utf-8-sig')
    print("\n💾 Datos guardados en outputs/datos/datos_procesados.csv")
    
    print("\n" + "="*80)
    print(" ✅ ANÁLISIS COMPLETADO EXITOSAMENTE ".center(80, "="))
    print("="*80 + "\n")
    
    return df_clean, metricas


# =============================================================================
# 8. EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    df_resultado, metricas_resultado = main()
