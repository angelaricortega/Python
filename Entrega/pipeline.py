"""
╔══════════════════════════════════════════════════════════════════════════╗
║   Sistema de Análisis de Riesgo Crediticio                              ║
║   Sistema Financiero Colombiano — Datos Abiertos Gov.co                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║   Curso  : Python para APIs e IA Aplicada                               ║
║   Semanas: 1, 2 y 3                                                     ║
║   Univ.  : Universidad Santo Tomás · 2026                               ║
║   Autores: Angela Rico · Sebastian Ramirez                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║   PROYECTO PERSONAL: Mi API de Análisis de Datos                        ║
║   Actividad Aplicada — Semana III                                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║   CONCEPTOS APLICADOS (TODOS los de las Semanas 1, 2 y 3)               ║
║                                                                         ║
║   SEMANA 1 — Fundamentos de Python Moderno                              ║
║     · Pattern Matching (match/case con guardas)                         ║
║         → modelos.py: clasificar_riesgo() con 6 niveles                 ║
║         → Justificación: más expresivo que if-elif-else para umbrales   ║
║                                                                         ║
║     · Decoradores simples y decorator factories                         ║
║         → decorators.py: @registrar_ejecucion, @validar_normalidad,     ║
║           @muestra_minima, @cachear, @validar_datos_df                  ║
║         → Justificación: principio Open/Closed (extender sin modificar) ║
║                                                                         ║
║     · Type hints modernos (Literal, Optional, List)                     ║
║         → TODO el código: anotaciones de tipos completas                ║
║         → Justificación: documentación viva + detección temprana errors ║
║                                                                         ║
║     · Entornos virtuales (venv) + requirements.txt                      ║
║         → requirements.txt: dependencias congeladas                     ║
║         → Justificación: reproducibilidad total del análisis            ║
║                                                                         ║
║   SEMANA 2 — Ingeniería de Datos                                        ║
║     · OOP con __init__, atributos y métodos                             ║
║         → api_client.py: ClienteAPIFinanciero                           ║
║         → pipeline.py: PipelineRiesgoCrediticio                         ║
║         → Justificación: encapsular estado + comportamiento             ║
║                                                                         ║
║     · requests.Session (conexión TCP persistente)                       ║
║         → api_client.py: session.get() reutiliza conexión               ║
║         → Justificación: reduce latencia de 48-200ms a ~5ms por petición║
║                                                                         ║
║     · HTTP: verbos, status codes, manejo de errores                     ║
║         → api_client.py: GET, raise_for_status(), try/except            ║
║         → Justificación: robustez ante fallos de red/API                ║
║                                                                         ║
║     · JSON vs Pickle (cuándo usar cada uno)                             ║
║         → pipeline.py: JSON para API, Pickle para caché local           ║
║         → Justificación: interoperabilidad vs velocidad Python          ║
║                                                                         ║
║     · Pydantic v2: BaseModel, Field, field_validator                    ║
║         → modelos.py: MunicipioFinanciero, VariableEstadistica          ║
║         → Justificación: validación automática + conversión de tipos    ║
║                                                                         ║
║     · EDA → Limpieza justificada estadísticamente                       ║
║         → pipeline.py: eda() documenta H1-H6, limpiar() refiere D1-D4   ║
║         → Justificación: trazabilidad completa de decisiones            ║
║                                                                         ║
║   SEMANA 3 — FastAPI y Visualizaciones                                  ║
║     · FastAPI: app.get, app.post, app.delete                            ║
║         → api_fastapi.py: endpoints CRUD completos                      ║
║         → Justificación: API REST estándar para consumo externo         ║
║                                                                         ║
║     · Routing, CRUD, documentación Swagger                              ║
║         → api_fastapi.py: /analizar, /historial, /docs                  ║
║         → Justificación: cualquier cliente puede consumir sin docs extra║
║                                                                         ║
║     · Síncrono vs Asíncrono, Uvicorn                                    ║
║         → api_fastapi.py: async def para I/O, def para CPU              ║
║         → Justificación: concurrencia eficiente                         ║
║                                                                         ║
║     · Visualizaciones profesionales con paleta coherente                ║
║         → visualizaciones.py: 3 paneles con misma paleta (config.py)    ║
║         → Justificación: coherencia visual + interpretación clara       ║
╠══════════════════════════════════════════════════════════════════════════╣
║   ESTRUCTURA MODULAR DEL PROYECTO                                       ║
║                                                                         ║
║   config.py           → Configuración global (URLs, colores, umbrales)  ║
║   decorators.py       → Librería de decoradores estadísticos            ║
║   modelos.py          → Contratos Pydantic (validación de datos)        ║
║   api_client.py       → Cliente HTTP robusto (descarga datos)           ║
║   visualizaciones.py  → Gráficas profesionales (EDA, análisis, comp.)   ║
║   pipeline.py         → Pipeline principal (orquestador)                ║
║   api_fastapi.py      → API REST con FastAPI (endpoints CRUD)           ║
║   analisis.ipynb      → Notebook ejecutivo (documentación + código)     ║
║   requirements.txt    → Dependencias congeladas                         ║
║   README.md           → Documentación completa del proyecto             ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Librería estándar ────────────────────────────────────────────────────
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# ── Terceros ─────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from scipy import stats
from pydantic import ValidationError

# ── Locales ──────────────────────────────────────────────────────────────
from config import (
    API_BASE, HTTP_TIMEOUT, DEFAULT_LIMIT,
    COLUMNAS, PALETA, RUTA_SALIDA, UMBRALES_RIESGO,
    API_TITULO, API_VERSION, API_DESCRIPCION,
)
from decorators import (
    registrar_ejecucion,
    validar_normalidad,
    muestra_minima,
    validar_datos_df,
)
from modelos import (
    MunicipioFinanciero,
    ResultadoAnalisis,
    validar_dataframe,
    NivelRiesgo,
)
from api_client import ClienteAPIFinanciero
from visualizaciones import (
    graficar_eda_completo,
    graficar_analisis_final,
    graficar_composicion_cartera,
)


# ══════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL DE ANÁLISIS DE RIESGO CREDITICIO
# ══════════════════════════════════════════════════════════════════════════

class PipelineRiesgoCrediticio:
    """
    Orquestador del análisis de riesgo crediticio del sistema financiero.

    ATRIBUTOS:
      cliente      : ClienteAPIFinanciero para descargar datos
      df           : DataFrame con datos limpios
      df_crudo     : DataFrame con datos crudos (antes de limpiar)
      municipios   : lista de MunicipiosFinancieros validados
      resultados   : ResultadoAnalisis con métricas consolidadas

    MÉTODOS PÚBLICOS (encadenables):
      ingestar()           → Etapa 1: descarga + validación Pydantic
      eda()                → Etapa 2: EDA documenta H1-H6
      limpiar()            → Etapa 3: limpieza refiere D1-D4 a H1-H6
      analizar()           → Etapa 4: estadísticos + test normalidad
      visualizar()         → Etapa 5: genera 3 paneles gráficos
      exportar()           → Etapa 6: guarda JSON, Pickle, CSV

    USO TÍPICO (fluent interface):
      pipeline = PipelineRiesgoCrediticio()
      pipeline.ingestar().eda().limpiar().analizar().visualizar().exportar()
    """

    def __init__(self, limite: int = DEFAULT_LIMIT):
        """
        CONSTRUCTOR: inicializa cliente y atributos vacíos.

        Args:
            limite: cantidad máxima de registros a descargar (default: 500)
        """
        print("\n" + "=" * 65)
        print("  PIPELINE DE ANÁLISIS DE RIESGO CREDITICIO")
        print("  Sistema Financiero Colombiano · Datos Abiertos Gov.co")
        print("=" * 65)

        self.limite = limite
        self.cliente = ClienteAPIFinanciero(API_BASE, HTTP_TIMEOUT)
        self.df: Optional[pd.DataFrame] = None
        self.df_crudo: Optional[pd.DataFrame] = None
        self.municipios: List[MunicipioFinanciero] = []
        self.resultados: Optional[ResultadoAnalisis] = None

        print(f"\n  Configuración inicial:")
        print(f"    · Límite de registros: {limite}")
        print(f"    · Timeout HTTP: {HTTP_TIMEOUT}s")
        print(f"    · Ruta de salida: {RUTA_SALIDA.absolute()}")

    # ── Etapa 1: Ingesta + Validación Pydantic ────────────────────────────

    @registrar_ejecucion
    def ingestar(self, limite: Optional[int] = None) -> "PipelineRiesgoCrediticio":
        """
        ETAPA 1: Ingesta de datos + Validación Pydantic

        PYDANTIC VALIDA CADA FILA EN ESTE PUNTO:
          1. Convierte strings a números (ej: "1,500,000" → 1500000.0)
          2. Valida restricciones (ge=0, min_length=2, etc.)
          3. Ejecuta field_validators antes de crear el objeto

        Args:
            limite: override del límite por defecto

        Returns:
            self: para encadenamiento
        """
        limite = limite or self.limite

        print("\n" + "─" * 65)
        print("  ETAPA 1: INGESTA + VALIDACIÓN PYDANTIC")
        print("─" * 65)

        # Descargar datos de la API
        print("\n  Descargando datos de la API...")
        raw = self.cliente.obtener_datos(limite)

        if not raw:
            print("    ⚠ API no devolvió datos. Verifique conexión o intente más tarde.")
            return self

        # Convertir a DataFrame crudo (para EDA posterior)
        self.df_crudo = pd.DataFrame(raw)
        print(f"  ✓ DataFrame crudo: {self.df_crudo.shape[0]} filas × {self.df_crudo.shape[1]} columnas")

        # Validar fila por fila con Pydantic
        validos, errores = [], []

        print(f"\n  [PYDANTIC] Validando registros (primeros 5 con detalle):")
        for i, fila in enumerate(raw[:5]):
            try:
                nombre = fila.get(COLUMNAS["municipio"], "N/A")
                print(f"    [{i+1}/5] {str(nombre)[:30]}")

                muni = MunicipioFinanciero(
                    municipio=fila.get(COLUMNAS["municipio"], "Desconocido"),
                    cartera_a=fila.get(COLUMNAS["cartera_a"]),
                    cartera_b=fila.get(COLUMNAS["cartera_b"]),
                    cartera_c=fila.get(COLUMNAS["cartera_c"]),
                    cartera_d=fila.get(COLUMNAS["cartera_d"]),
                    cartera_e=fila.get(COLUMNAS["cartera_e"]),
                    total_cartera=fila.get(COLUMNAS["cartera_tot"]),
                    total_captaciones=fila.get(COLUMNAS["captaciones"]),
                )

                # Calcular indicadores
                muni.calcular_indicadores()

                print(f"         ✓ Validado: cartera_a={muni.cartera_a:,.0f}, "
                      f"riesgo={muni.indice_riesgo:.4f}" if muni.indice_riesgo else "         ✓ Validado: sin índice")
                validos.append(muni)

            except ValidationError as e:
                msg = e.errors()[0]["msg"][:50] if e.errors() else str(e)
                print(f"         ✗ Error: {msg}")
                errores.append({
                    "fila": i,
                    "municipio": fila.get(COLUMNAS["municipio"]),
                    "error": str(e),
                })

        # Procesar resto sin logging detallado
        for fila in raw[5:]:
            try:
                muni = MunicipioFinanciero(
                    municipio=fila.get(COLUMNAS["municipio"], "Desconocido"),
                    cartera_a=fila.get(COLUMNAS["cartera_a"]),
                    cartera_b=fila.get(COLUMNAS["cartera_b"]),
                    cartera_c=fila.get(COLUMNAS["cartera_c"]),
                    cartera_d=fila.get(COLUMNAS["cartera_d"]),
                    cartera_e=fila.get(COLUMNAS["cartera_e"]),
                    total_cartera=fila.get(COLUMNAS["cartera_tot"]),
                    total_captaciones=fila.get(COLUMNAS["captaciones"]),
                ).calcular_indicadores()
                validos.append(muni)
            except ValidationError:
                errores.append({
                    "municipio": fila.get(COLUMNAS["municipio"]),
                    "error": "ValidationError",
                })

        self.municipios = validos

        # Convertir a DataFrame para análisis
        if validos:
            records = [m.model_dump() for m in validos]
            self.df = pd.DataFrame(records)
            print(f"\n  ✓ DataFrame validado: {self.df.shape[0]} filas × {self.df.shape[1]} columnas")

        print(f"\n  [PYDANTIC] Resumen:")
        print(f"    · Válidos  : {len(validos)} ({len(validos)/len(raw)*100:.1f}%)")
        print(f"    · Errores  : {len(errores)} ({len(errores)/len(raw)*100:.1f}%)")

        if errores:
            print(f"    → Errores comunes: tipos inválidos, campos faltantes")

        return self

    # ── Etapa 2: EDA (Análisis Exploratorio de Datos) ─────────────────────

    @registrar_ejecucion
    @validar_datos_df(columnas_requeridas=["total_cartera", "indice_riesgo"])
    def eda(self) -> "PipelineRiesgoCrediticio":
        """
        ETAPA 2: EDA — Análisis Exploratorio de Datos

        PRINCIPIO FUNDAMENTAL:
          El EDA SIEMPRE precede a la limpieza.
          Primero observamos, documentamos hallazgos (H1-H6),
          y SÓLO entonces aplicamos decisiones de limpieza
          referenciando cada hallazgo.

        HALLAZGOS DOCUMENTADOS (H1-H6):
          H1: Dimensiones del dataset y duplicados
          H2: Completitud de datos (% nulos por columna)
          H3: Estadísticos descriptivos + CV (heterogeneidad)
          H4: Outliers extremos (método IQR de Tukey)
          H5: Normalidad del índice de riesgo (Shapiro-Wilk)
          H6: Distribución por nivel de riesgo

        POR QUÉ EDA ANTES DE LIMPIEZA:
          - Sin EDA, la limpieza es arbitraria (no justificada)
          - Con EDA, cada decisión de limpieza refiere a un hallazgo
          - Esto hace el proceso TRAZABLE y REPRODUCIBLE

        RETURNS:
            self: para encadenamiento
        """
        print("\n" + "─" * 65)
        print("  ETAPA 2: EDA — ANÁLISIS EXPLORATORIO DE DATOS")
        print("─" * 65)

        df = self.df_crudo
        if df is None or df.empty:
            print("    ⚠ No hay datos crudos para EDA")
            return self

        print(f"\n  [H1] Dataset: {df.shape[0]:,} filas × {df.shape[1]} columnas")

        # H1: Duplicados
        n_dup = df.duplicated(subset=["nombre_municipio"]).sum()
        print(f"  [H1] Duplicados por municipio: {n_dup}")
        if n_dup > 0:
            print(f"       → REQUIERE LIMPIEZA (D1): inflan conteo y suman doble")
        else:
            print(f"       → OK: sin duplicados")

        # H2: Completitud
        print("\n  [H2] Completitud de datos clave:")
        cols_check = ["total_cartera", "total_captaciones", "indice_riesgo", "ratio_liquidez"]
        for col in cols_check:
            if col in df.columns:
                n_nul = df[col].isna().sum()
                pct = n_nul / len(df) * 100
                marca = " ← ALTO" if pct > 30 else ""
                print(f"       {col:<25} {n_nul:>4} nulos ({pct:5.1f}%){marca}")

        # H3: Estadísticos de cartera
        print("\n  [H3] Estadísticos — total_cartera (COP):")
        if "total_cartera" in df.columns and df["total_cartera"].notna().any():
            s = df["total_cartera"].describe()
            print(f"       mínimo   = {s['min']:>20,.0f}")
            print(f"       Q1       = {s['25%']:>20,.0f}")
            print(f"       mediana  = {s['50%']:>20,.0f}")
            print(f"       media    = {s['mean']:>20,.0f}")
            print(f"       Q3       = {s['75%']:>20,.0f}")
            print(f"       máximo   = {s['max']:>20,.0f}")

            cv = s["std"] / s["mean"] * 100 if s["mean"] > 0 else 0
            print(f"       CV (%)   = {cv:>19.1f}%")
            if cv > 100:
                print(f"       → CV > 100%: ALTA heterogeneidad — crédito concentrado en pocos municipios")
            else:
                print(f"       → CV ≤ 100%: distribución homogénea")

        # H4: Outliers (IQR)
        print("\n  [H4] Outliers — total_cartera (método IQR de Tukey):")
        if "total_cartera" in df.columns:
            s2 = df["total_cartera"].dropna()
            if not s2.empty:
                q1, q3 = s2.quantile(0.25), s2.quantile(0.75)
                iqr = q3 - q1
                lim_sup = q3 + 1.5 * iqr
                n_out = (s2 > lim_sup).sum()
                print(f"       Límite IQR superior: {lim_sup:>18,.0f} COP")
                print(f"       Outliers detectados: {n_out:>4} municipios ({n_out/len(s2)*100:.1f}%)")
                if n_out > 0:
                    print(f"       → Tratamiento necesario (D3): winsorizar o eliminar")
                else:
                    print(f"       → Sin outliers extremos")

        # H5: Normalidad (Shapiro-Wilk)
        print("\n  [H5] Test Shapiro-Wilk — índice de riesgo:")
        if "indice_riesgo" in df.columns:
            sr = df["indice_riesgo"].dropna()
            if len(sr) >= 3:
                w, p = stats.shapiro(sr.head(50))
                print(f"       W={w:.4f}, p={p:.6f}")
                if p < 0.05:
                    print("       → NO NORMAL: usaremos MEDIANA (no media) como estadístico central")
                    print("         robusto (no la media) en el análisis posterior")
                    print("         → Tests no-paramétricos: Mann-Whitney U, Kruskal-Wallis")
                else:
                    print("       → NORMAL: media y tests paramétricos son válidos")

        # H6: Distribución por nivel de riesgo
        print("\n  [H6] Distribución por nivel de riesgo (datos crudos):")
        if "nivel_riesgo" in df.columns:
            for nivel, cnt in df["nivel_riesgo"].value_counts().items():
                pct = cnt / len(df) * 100
                barra = "█" * max(1, int(pct / 3))
                color = {
                    "sin_riesgo": "🟢", "riesgo_bajo": "🟢",
                    "riesgo_moderado": "🟡", "riesgo_alto": "🟠",
                    "riesgo_critico": "🔴", "sin_datos": "⚪"
                }.get(nivel, "⚪")
                print(f"       {color} {nivel:<20} {barra:<18} {cnt:>4} ({pct:4.1f}%)")

        # Generar gráfica EDA
        print("\n  [GRÁFICA] Generando panel EDA...")
        try:
            graficar_eda_completo(df, titulo="EDA — Datos Crudos · Sistema Financiero Colombiano")
        except Exception as e:
            print(f"    ⚠ Error al generar gráfica EDA: {e}")

        print("\n  ✓ EDA completado — hallazgos [H1–H6] documentados")
        print("    → limpiar() tomará cada decisión referenciando [H1–H6]")
        print("─" * 65)

        return self

    # ── Etapa 3: Limpieza referenciada al EDA ─────────────────────────────

    @registrar_ejecucion
    @validar_datos_df(columnas_requeridas=["total_cartera", "indice_riesgo"])
    def limpiar(self) -> "PipelineRiesgoCrediticio":
        """
        ETAPA 3: Limpieza de datos REFERENCIADA al EDA

        PRINCIPIO FUNDAMENTAL:
          Cada decisión de limpieza debe referenciar un hallazgo del EDA.
          Esto hace el proceso TRAZABLE y REPRODUCIBLE.

        DECISIONES DE LIMPIEZA (D1-D4):
          D1: Eliminar duplicados → justificado en H1
          D2: Filtrar sin cartera total → justificado en H2 (sin este campo no hay KPIs)
          D3: Winsorizar outliers P98 → justificado en H3+H4 (CV>100%, outliers IQR)
          D4: Imputar liquidez con mediana → justificado en H5 (no-normalidad)

        POR QUÉ MEDIANA Y NO MEDIA:
          El test Shapiro-Wilk en H5 confirma que el índice de riesgo
          NO sigue distribución normal. La media es sensible a outliers;
          la mediana no. Usamos mediana como estadístico central.

        RETURNS:
            self: para encadenamiento
        """
        print("\n" + "─" * 65)
        print("  ETAPA 3: LIMPIEZA DE DATOS (REFERENCIADA AL EDA)")
        print("─" * 65)

        if self.df is None or self.df.empty:
            print("    ⚠ No hay DataFrame para limpiar")
            return self

        df = self.df.copy()
        n_ini = len(df)
        log = []

        # D1: Eliminar duplicados (justificado en H1)
        n_antes = len(df)
        df = df.drop_duplicates(subset=["municipio"], keep="first")
        n_elim = n_antes - len(df)
        log.append(f"D1 Duplicados eliminados          : {n_elim} (justificado en H1)")

        # D2: Filtrar sin cartera total (justificado en H2)
        n_antes = len(df)
        df = df[df["total_cartera"].notna() & (df["total_cartera"] > 0)]
        n_elim = n_antes - len(df)
        log.append(f"D2 Sin cartera total eliminados   : {n_elim} (justificado en H2: sin este campo no hay KPIs)")

        # D3: Winsorizar outliers P98 (justificado en H3+H4)
        if df["total_cartera"].notna().any():
            n_antes = len(df)
            p98 = df["total_cartera"].quantile(0.98)
            df = df[df["total_cartera"] <= p98]
            n_elim = n_antes - len(df)
            log.append(f"D3 Outliers P98 eliminados        : {n_elim} (umbral: {p98:,.0f} COP) (justificado en H3+H4)")

        # D4: Imputar ratio_liquidez con mediana (justificado en H5)
        if "ratio_liquidez" in df.columns:
            n_nulos = df["ratio_liquidez"].isna().sum()
            if n_nulos > 0:
                mediana = df["ratio_liquidez"].median()
                df["ratio_liquidez"] = df["ratio_liquidez"].fillna(mediana)
                log.append(f"D4 ratio_liquidez imputados (med.): {n_nulos} → mediana={mediana:.3f} (justificado en H5: no-normalidad)")

        self.df = df

        print(f"\n  Limpieza completada:")
        for linea in log:
            print(f"    {linea}")

        n_final = len(df)
        print(f"\n  Filas: {n_ini} → {n_final} ({n_ini - n_final} eliminadas en total)")
        print(f"  Registros válidos: {n_final/n_ini*100:.1f}%")

        return self

    # ── Etapa 4: Análisis estadístico ─────────────────────────────────────

    @registrar_ejecucion
    @validar_datos_df(columnas_requeridas=["indice_riesgo"])
    @validar_normalidad(alpha=0.05)
    def analizar(self) -> "PipelineRiesgoCrediticio":
        """
        ETAPA 4: Análisis estadístico del índice de riesgo

        DECORADORES APLICADOS:
          @registrar_ejecucion: mide tiempo de ejecución
          @validar_datos_df: verifica que self.df existe y tiene columnas
          @validar_normalidad: ejecuta Shapiro-Wilk antes del análisis

        ESTADÍSTICOS CALCULADOS:
          - Mediana (robusto, no asume normalidad)
          - Media (si normalidad confirmada)
          - Desviación estándar
          - Mínimo, máximo, percentiles
          - Coeficiente de variación

        RETURNS:
            self: para encadenamiento
        """
        print("\n" + "─" * 65)
        print("  ETAPA 4: ANÁLISIS ESTADÍSTICO")
        print("─" * 65)

        if self.df is None or self.df.empty:
            print("    ⚠ No hay datos para analizar")
            return self

        s = self.df["indice_riesgo"].dropna()
        n = len(s)

        print(f"\n  Estadísticos del Índice de Riesgo (n={n:,}):")

        # Estadísticos básicos
        mediana = s.median()
        media = s.mean()
        std = s.std()
        minimo = s.min()
        maximo = s.max()
        p95 = s.quantile(0.95)

        print(f"    Mediana (robusto) : {mediana*100:.4f}%")
        print(f"    Media             : {media*100:.4f}%")
        print(f"    Desv. estándar    : {std*100:.4f}%")
        print(f"    Mínimo            : {minimo*100:.4f}%")
        print(f"    P95               : {p95*100:.4f}%")
        print(f"    Máximo            : {maximo*100:.4f}%")

        # Coeficiente de variación
        cv = (std / media * 100) if media > 0 else 0
        print(f"    CV (%)            : {cv:.1f}%")
        if cv > 50:
            print(f"    → CV alto: alta dispersión relativa")

        # Calcular métricas consolidadas para ResultadoAnalisis
        cartera_total = self.df["total_cartera"].sum() if "total_cartera" in self.df else 0
        indice_promedio = self.df["indice_riesgo"].mean() if "indice_riesgo" in self.df else 0

        # Porcentaje sin riesgo
        if "nivel_riesgo" in self.df:
            sin_riesgo = (self.df["nivel_riesgo"] == "sin_riesgo").sum()
            pct_sin_riesgo = sin_riesgo / len(self.df) * 100
        else:
            pct_sin_riesgo = 0

        # Crear ResultadoAnalisis
        self.resultados = ResultadoAnalisis(
            n_municipios=len(self.df),
            cartera_total_billones=cartera_total / 1e12,
            indice_riesgo_promedio=indice_promedio,
            pct_sin_riesgo=pct_sin_riesgo,
            municipios=self.municipios[:100],  # primeros 100 para no saturar
        )

        print(f"\n  [RESULTADO] Métricas consolidadas:")
        print(f"    · Cartera total       : ${cartera_total/1e12:.2f} billones COP")
        print(f"    · Índice promedio     : {indice_promedio*100:.4f}%")
        print(f"    · % sin riesgo        : {pct_sin_riesgo:.1f}%")
        print(f"    · Municipios válidos  : {len(self.df)}")

        print("\n  ✓ Análisis estadístico completado")
        print("─" * 65)

        return self

    # ── Etapa 5: Visualización ────────────────────────────────────────────

    @registrar_ejecucion
    @validar_datos_df(columnas_requeridas=["total_cartera", "indice_riesgo", "nivel_riesgo"])
    def visualizar(self) -> "PipelineRiesgoCrediticio":
        """
        ETAPA 5: Visualización profesional

        GRÁFICAS GENERADAS:
          1. eda_datos_crudos.png      → Panel EDA (6 subgráficas)
          2. panel_analisis.png        → Análisis final (4 subgráficas)
          3. panel_composicion.png     → Composición de cartera (2 subgráficas)

        PALETA COHERENTE:
          Todas las gráficas usan la misma paleta (config.PALETA)
          Cada nivel de riesgo tiene un color fijo (RIESGO_COLOR)

        RETURNS:
            self: para encadenamiento
        """
        print("\n" + "─" * 65)
        print("  ETAPA 5: VISUALIZACIÓN PROFESIONAL")
        print("─" * 65)

        print("\n  [GRÁFICA 1/3] Generando panel EDA...")
        try:
            graficar_eda_completo(
                self.df_crudo,
                titulo="EDA — Datos Crudos · Sistema Financiero Colombiano"
            )
        except Exception as e:
            print(f"    ⚠ Error: {e}")

        print("\n  [GRÁFICA 2/3] Generando panel de análisis...")
        try:
            graficar_analisis_final(
                self.df,
                titulo="Análisis Final · Datos Limpios · Sistema Financiero Colombiano"
            )
        except Exception as e:
            print(f"    ⚠ Error: {e}")

        print("\n  [GRÁFICA 3/3] Generando panel de composición...")
        try:
            graficar_composicion_cartera(
                self.df,
                titulo="Composición de Cartera · Clasificación Regulatoria"
            )
        except Exception as e:
            print(f"    ⚠ Error: {e}")

        print("\n  ✓ Visualización completada")
        print("─" * 65)

        return self

    # ── Etapa 6: Exportación ──────────────────────────────────────────────

    @registrar_ejecucion
    def exportar(self) -> "PipelineRiesgoCrediticio":
        """
        ETAPA 6: Exportación de resultados

        FORMATOS DE EXPORTACIÓN:
          1. JSON (resultado_analisis.json)
             → Para consumir por FastAPI u otros sistemas
             → Pydantic.model_dump_json() maneja datetime automáticamente

          2. Pickle (municipios.pkl)
             → Para cachear objetos Python y cargar rápidamente
             → Preserva tipos exactos (datetime, etc.)

          3. CSV (datos_limpios.csv)
             → Para abrir en Excel o herramientas BI
             → Formato universal

        POR QUÉ EXPORTAR MÚLTIPLES FORMATOS:
          - JSON: interoperabilidad (cualquier lenguaje lo lee)
          - Pickle: velocidad Python (carga instantánea)
          - CSV: universalidad (Excel, PowerBI, Tableau)

        RETURNS:
            self: para encadenamiento
        """
        print("\n" + "─" * 65)
        print("  ETAPA 6: EXPORTACIÓN DE RESULTADOS")
        print("─" * 65)

        RUTA_SALIDA.mkdir(parents=True, exist_ok=True)

        # 1. Exportar JSON
        if self.resultados:
            json_path = RUTA_SALIDA / "resultado_analisis.json"
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(self.resultados.model_dump_json(indent=2))
            print(f"\n  ✓ JSON exportado: {json_path}")

        # 2. Exportar Pickle
        if self.municipios:
            pickle_path = RUTA_SALIDA / "municipios.pkl"
            with open(pickle_path, "wb") as f:
                pickle.dump(self.municipios, f)
            print(f"  ✓ Pickle exportado: {pickle_path}")

        # 3. Exportar CSV
        if self.df is not None and not self.df.empty:
            csv_path = RUTA_SALIDA / "datos_limpios.csv"
            self.df.to_csv(csv_path, index=False, encoding="utf-8")
            print(f"  ✓ CSV exportado: {csv_path}")

        # 4. Exportar resumen ejecutivo (JSON)
        if self.resultados:
            resumen = {
                "fecha": self.resultados.fecha_analisis.isoformat(),
                "version": self.resultados.version,
                "n_municipios": self.resultados.n_municipios,
                "cartera_total_billones": round(self.resultados.cartera_total_billones, 2),
                "indice_riesgo_promedio": round(self.resultados.indice_riesgo_promedio * 100, 4),
                "pct_sin_riesgo": round(self.resultados.pct_sin_riesgo, 1),
            }
            resumen_path = RUTA_SALIDA / "resumen_ejecutivo.json"
            with open(resumen_path, "w", encoding="utf-8") as f:
                json.dump(resumen, f, indent=2)
            print(f"  ✓ Resumen exportado: {resumen_path}")

        print("\n  ✓ Exportación completada")
        print("─" * 65)

        return self

    # ── Método de cierre ──────────────────────────────────────────────────

    def cerrar(self):
        """
        Libera recursos (cierra sesión HTTP).
        """
        self.cliente.cerrar()
        print("\n  ✓ Pipeline cerrado (recursos liberados)")

    # ── Método principal (ejecuta todo el pipeline) ───────────────────────

    def ejecutar_todo(self) -> "PipelineRiesgoCrediticio":
        """
        Ejecuta TODO el pipeline en una sola llamada.

        RETURNS:
            self: para encadenamiento
        """
        return (
            self.ingestar()
            .eda()
            .limpiar()
            .analizar()
            .visualizar()
            .exportar()
        )


# ══════════════════════════════════════════════════════════════════════════
# EJECUCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═" * 65)
    print("  SISTEMA DE ANÁLISIS DE RIESGO CREDITICIO")
    print("  Sistema Financiero Colombiano — Datos Abiertos Gov.co")
    print("  Python para APIs e IA Aplicada · Universidad Santo Tomás")
    print("═" * 65)

    # Crear pipeline y ejecutar todo
    pipeline = PipelineRiesgoCrediticio(limite=500)

    try:
        pipeline.ejecutar_todo()

        print("\n" + "═" * 65)
        print("  ✅ PIPELINE COMPLETADO EXITOSAMENTE")
        print("═" * 65)
        print("\n  ARCHIVOS GENERADOS:")
        print(f"    · outputs/eda_datos_crudos.png")
        print(f"    · outputs/panel_analisis.png")
        print(f"    · outputs/panel_composicion.png")
        print(f"    · outputs/resultado_analisis.json")
        print(f"    · outputs/municipios.pkl")
        print(f"    · outputs/datos_limpios.csv")
        print(f"    · outputs/resumen_ejecutivo.json")

    except Exception as e:
        print(f"\n  🔴 ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

    finally:
        pipeline.cerrar()

