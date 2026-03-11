# Semana 1 - Funciones puras para limpieza de DataFrames
from typing import List, Optional
import pandas as pd
import numpy as np

def eliminar_duplicados(df: pd.DataFrame, subset: Optional[List[str]] = None, mantener: str = "first") -> pd.DataFrame:
    """Elimina filas duplicadas del DataFrame."""
    if df.empty:
        return df.copy()
    n_antes = len(df)
    df_limpio = df.drop_duplicates(subset=subset, keep=mantener)
    n_duplicados = n_antes - len(df_limpio)
    if n_duplicados > 0:
        print(f"    Eliminados {n_duplicados} duplicados")
    return df_limpio

def imputar_nulos(df: pd.DataFrame, columnas: List[str], estrategia: str = "mediana") -> pd.DataFrame:
    """Imputa valores nulos con la estrategia especificada."""
    df_limpio = df.copy()
    for col in columnas:
        if col not in df_limpio.columns:
            continue
        n_nulos = df_limpio[col].isna().sum()
        if n_nulos == 0:
            continue
        if estrategia == "media":
            valor = df_limpio[col].mean()
        elif estrategia == "mediana":
            valor = df_limpio[col].median()
        elif estrategia == "moda":
            valor = df_limpio[col].mode().iloc[0] if len(df_limpio[col].mode()) > 0 else df_limpio[col].median()
        else:
            valor = 0
        df_limpio[col] = df_limpio[col].fillna(valor)
        print(f"    {col}: {n_nulos} nulos imputados")
    return df_limpio

def detectar_outliers_iqr(df: pd.DataFrame, columna: str, factor: float = 1.5) -> pd.Series:
    """Detecta outliers usando el método IQR."""
    Q1 = df[columna].quantile(0.25)
    Q3 = df[columna].quantile(0.75)
    IQR = Q3 - Q1
    outliers = (df[columna] < Q1 - factor * IQR) | (df[columna] > Q3 + factor * IQR)
    print(f"    {columna}: {outliers.sum()} outliers detectados")
    return outliers

def limpieza_completa(df: pd.DataFrame, columnas_numericas: List[str], columna_municipio: str = "municipio", estrategia_imputacion: str = "mediana") -> pd.DataFrame:
    """Aplica pipeline completo de limpieza de datos."""
    df_limpio = eliminar_duplicados(df, subset=[columna_municipio])
    df_limpio = imputar_nulos(df_limpio, columnas=columnas_numericas, estrategia=estrategia_imputacion)
    for col in columnas_numericas:
        if col in df_limpio.columns:
            detectar_outliers_iqr(df_limpio, col)
    return df_limpio
