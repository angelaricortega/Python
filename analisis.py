"""
╔══════════════════════════════════════════════════════════════════════════╗
║   Sistema de Análisis de Riesgo Crediticio                              ║
║   Sistema Financiero Colombiano — Datos Abiertos Gov.co                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║   Curso  : Python para APIs e IA Aplicada                               ║
║   Semanas: 1 y 2                                                        ║
║   Univ.  : Universidad Santo Tomás · 2026                               ║
║   Autores: Angela Rico · Sebastian Ramirez                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║   CONCEPTOS APLICADOS                                                   ║
║   Semana 1                                                              ║
║     · Pattern Matching (match/case con guardas)   → clasificar_riesgo() ║
║     · Decoradores simples y decorator factories   → decorators.py       ║
║     · Modularización en archivos separados        → modelos.py          ║
║     · Type hints modernos (Literal, Optional)     → todo el código      ║
║     · EDA → Limpieza justificada estadísticamente → eda() / limpiar()   ║
║   Semana 2                                                              ║
║     · OOP con __init__, atributos y métodos       → ClienteAPI, Pipeline║
║     · requests.Session (conexión TCP persistente) → ClienteAPIFinanciero║
║     · JSON vs Pickle (cuándo usar cada uno)       → exportar_*()        ║
║     · Pydantic v2: BaseModel, Field, validators   → modelos.py          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Librería estándar ────────────────────────────────────────────────────
import json
import pickle
import functools
from datetime import datetime
from pathlib import Path

# ── Terceros ─────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import requests
from scipy import stats


# ══════════════════════════════════════════════════════════════════════════
# 0. CONFIGURACIÓN GLOBAL
# ══════════════════════════════════════════════════════════════════════════

API_BASE = "https://www.datos.gov.co/resource/3kqn-n4za.json"

COLUMNAS = {
    "municipio":   "nombre_municipio",
    "cartera_a":   "cartera_categoria_a",
    "cartera_b":   "cartera_categoria_b",
    "cartera_c":   "cartera_categoria_c",
    "cartera_d":   "cartera_categoria_d",
    "cartera_e":   "cartera_categoria_e",
    "cartera_tot": "total_cartera",
    "captaciones": "total_captaciones",
}

PALETA = {
    "primario":    "#3D008D",
    "secundario":  "#ED1E79",
    "neutro":      "#64748B",
    "sin_riesgo":  "#2ECC71",
    "riesgo_bajo": "#27AE60",
    "riesgo_mod":  "#F39C12",
    "riesgo_alto": "#E67E22",
    "riesgo_crit": "#E74C3C",
    "sin_datos":   "#95A5A6",
}

RUTA_SALIDA = Path("outputs")
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.facecolor":  "white",
    "axes.facecolor":    "#F8FAFC",
    "axes.edgecolor":    "#CBD5E1",
    "axes.grid":         True,
    "grid.color":        "#E2E8F0",
    "grid.linewidth":    0.6,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "font.family":       "sans-serif",
    "font.size":         10,
    "axes.titlesize":    11,
    "axes.titleweight":  "bold",
    "axes.labelsize":    9,
    "xtick.labelsize":   8,
    "ytick.labelsize":   8,
    "legend.fontsize":   8,
    "figure.dpi":        120,
})


# ══════════════════════════════════════════════════════════════════════════
# 1. SEMANA 1 — DECORADORES
# ══════════════════════════════════════════════════════════════════════════

def registrar_ejecucion(func):
    """
    Decorador simple de logging de timestamp y duracion.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ts = datetime.now()
        print(f"\n  [+-> [{ts:%H:%M:%S}] {func.__name__}()")
        resultado = func(*args, **kwargs)
        duracion = (datetime.now() - ts).total_seconds()
        print(f"  [+-] Completado en {duracion:.2f}s")
        return resultado
    return wrapper


def validar_normalidad(alpha: float = 0.05):
    """
    Decorator factory compatible con funciones y métodos de clase.
    Ejecuta Shapiro-Wilk antes de la función decorada.

    Compatibilidad:
      - funciones: f(data)
      - métodos:   obj.metodo(data=...)
      - métodos sin parámetro `data`: intenta inferir desde obj.df["indice_riesgo"]
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = kwargs.get("data", None)

            # Caso 1: método/función con `data` posicional
            if data is None and len(args) >= 2:
                data = args[1]

            # Caso 2: método sin `data` explícito -> inferir desde self.df
            if data is None and len(args) >= 1:
                self_obj = args[0]
                df_obj = getattr(self_obj, "df", None)
                if isinstance(df_obj, pd.DataFrame) and "indice_riesgo" in df_obj.columns:
                    data = df_obj["indice_riesgo"].dropna().tolist()

            # Caso 3: función normal cuyo primer argumento es data
            if data is None and len(args) >= 1 and not hasattr(args[0], "df"):
                data = args[0]

            if data is None:
                print("    ⚠ No se recibió `data` para validar normalidad")
                return func(*args, **kwargs)

            try:
                n = len(data)
            except TypeError:
                print("    ⚠ `data` no es iterable; se omite test de normalidad")
                return func(*args, **kwargs)

            if n < 3:
                print(f"    ⚠ n={n} insuficiente para Shapiro-Wilk (mín. 3)")
                return func(*args, **kwargs)

            # Shapiro con límite práctico para evitar advertencias en muestras muy grandes
            muestra = list(data)[:5000]
            stat, p = stats.shapiro(muestra)

            if p < alpha:
                print(f"    ⚠ Datos NO normales: W={stat:.4f}, p={p:.4f} < α={alpha}")
                print("      → Considera: Mann-Whitney U o Kruskal-Wallis")
            else:
                print(f"    ✓ Normalidad confirmada: p={p:.4f} ≥ α={alpha}")

            return func(*args, **kwargs)  # no duplicar `data`
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════
# 2. SEMANA 1 — PATTERN MATCHING
# ══════════════════════════════════════════════════════════════════════════

# Nota: clasificar_riesgo() y NivelRiesgo se importan desde modelos.py
# para evitar código duplicado. Ver modelos.py para la implementación.
from modelos import clasificar_riesgo, NivelRiesgo as TipoRiesgo

# ══════════════════════════════════════════════════════════════════════════
# 3. SEMANA 2 — PYDANTIC: Modelos de Validación
# ══════════════════════════════════════════════════════════════════════════

# Nota: Los modelos Pydantic se importan desde modelos.py para evitar
# duplicación. Este archivo (analisis.py) es el único consumidor.
from modelos import MunicipioFinanciero, ResultadoAnalisis

# ══════════════════════════════════════════════════════════════════════════
# 4. SEMANA 2 — OOP: Cliente API
# ══════════════════════════════════════════════════════════════════════════

class ClienteAPIFinanciero:
    """
    Cliente HTTP para la API de Datos Abiertos Colombia (Socrata).
    """

    def __init__(self, base_url: str, timeout: int = 12):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "RiesgoCredito-USTA/1.0",
        })

    def obtener_datos(self, limite: int = 500) -> list[dict]:
        url = f"{self.base_url}?$limit={limite}&$offset=0"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            print(f"    ⚠ Timeout ({self.timeout}s). Activando datos sintéticos…")
        except requests.exceptions.HTTPError as e:
            print(f"    ✗ Error HTTP {e.response.status_code}")
        except requests.exceptions.JSONDecodeError:
            print("    ✗ Respuesta no es JSON válido")
        except requests.exceptions.ConnectionError:
            print("    ✗ Sin conexión. Activando datos sintéticos…")
        return []

    def cerrar(self):
        self.session.close()


# ══════════════════════════════════════════════════════════════════════════
# 5. PIPELINE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

class PipelineRiesgo:
    """
    Orquestador del análisis de riesgo crediticio.
    """

    def __init__(self, cliente: ClienteAPIFinanciero):
        self.cliente = cliente
        self.municipios: List[MunicipioFinanciero] = []
        self.df: Optional[pd.DataFrame] = None
        self.df_crudo: Optional[pd.DataFrame] = None

    # ── Etapa 1: Ingesta + Validación Pydantic ────────────────────────────

    @registrar_ejecucion
    def ingestar(self, limite: int = 400) -> "PipelineRiesgo":
        raw = self.cliente.obtener_datos(limite)

        if not raw:
            print("    Usando datos sintéticos (fallback sin conexión)")
            raw = self._datos_sinteticos()

        validos, errores = [], []

        for fila in raw:
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

            except ValidationError as e:
                errores.append({
                    "municipio": fila.get(COLUMNAS["municipio"]),
                    "error": str(e)
                })

        self.municipios = validos
        print(f"    ✓ {len(validos)} válidos | ✗ {len(errores)} rechazados por Pydantic")
        return self

    # ── Etapa 2: DataFrame ────────────────────────────────────────────────

    @registrar_ejecucion
    def construir_dataframe(self) -> "PipelineRiesgo":
        records = [m.model_dump() for m in self.municipios]
        self.df_crudo = pd.DataFrame(records)
        self.df = self.df_crudo.copy()
        print(f"    DataFrame: {self.df.shape[0]} filas × {self.df.shape[1]} columnas")
        return self

    # ── Etapa 3: EDA — Análisis Exploratorio ─────────────────────────────

    @registrar_ejecucion
    def eda(self) -> "PipelineRiesgo":
        df = self.df_crudo
        if df is None or df.empty:
            print("    ⚠ No hay datos crudos para EDA")
            return self

        print("\n" + "─" * 56)
        print("  EDA — DATOS CRUDOS (antes de cualquier limpieza)")
        print("─" * 56)

        print(f"\n  [H1] Dataset: {df.shape[0]:,} filas × {df.shape[1]} columnas")
        n_dup = df.duplicated(subset=["municipio"]).sum()
        print(f"  [H1] Duplicados por municipio: {n_dup}")
        print(f"       → {'REQUIERE LIMPIEZA' if n_dup > 0 else 'OK'}: "
              f"{'inflan conteo y suman doble' if n_dup > 0 else 'sin duplicados'}")

        print("\n  [H2] Completitud de datos clave:")
        cols_check = ["total_cartera", "total_captaciones", "indice_riesgo", "ratio_liquidez"]
        for col in cols_check:
            if col in df.columns:
                n_nul = df[col].isna().sum()
                pct = n_nul / len(df) * 100
                marca = " ← ALTO" if pct > 30 else ""
                print(f"       {col:<25} {n_nul:>4} nulos ({pct:5.1f}%){marca}")

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
            print(f"       → CV {'> 100%: ALTA heterogeneidad — crédito concentrado' if cv > 100 else '≤ 100%: distribución homogénea'}")

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
                print(f"       → {'Tratamiento necesario' if n_out > 0 else 'Sin outliers extremos'}")

        print("\n  [H5] Test Shapiro-Wilk — índice de riesgo:")
        if "indice_riesgo" in df.columns:
            sr = df["indice_riesgo"].dropna()
            if len(sr) >= 3:
                w, p = stats.shapiro(sr.head(50))
                print(f"       W={w:.4f}, p={p:.6f}")
                if p < 0.05:
                    print("       → NO NORMAL: usaremos MEDIANA como estadístico")
                    print("         robusto (no la media) en el análisis posterior")
                else:
                    print("       → NORMAL: media y tests paramétricos son válidos")

        print("\n  [H6] Distribución por nivel de riesgo (datos crudos):")
        if "nivel_riesgo" in df.columns:
            for nivel, cnt in df["nivel_riesgo"].value_counts().items():
                pct = cnt / len(df) * 100
                barra = "█" * max(1, int(pct / 3))
                print(f"       {nivel:<22} {barra:<18} {cnt:>4} ({pct:4.1f}%)")

        print("\n  ✓ EDA completado — hallazgos [H1–H6] documentados")
        print("    → limpiar() toma cada decisión referenciando [H1–H4]")
        print("─" * 56)

        self._graficar_eda()
        return self

    # ── Etapa 4: Limpieza referenciada al EDA ────────────────────────────

    @registrar_ejecucion
    def limpiar(self) -> "PipelineRiesgo":
        if self.df is None or self.df.empty:
            print("    ⚠ No hay DataFrame para limpiar")
            return self

        df = self.df.copy()
        n_ini = len(df)
        log = []

        n_a = len(df)
        df = df.drop_duplicates(subset=["municipio"], keep="first")
        log.append(f"D1 Duplicados eliminados          : {n_a - len(df)}")

        n_a = len(df)
        df = df[df["total_cartera"].notna() & (df["total_cartera"] > 0)]
        log.append(f"D2 Sin cartera total eliminados   : {n_a - len(df)}")

        if df["total_cartera"].notna().any():
            n_a = len(df)
            p98 = df["total_cartera"].quantile(0.98)
            df = df[df["total_cartera"] <= p98]
            log.append(f"D3 Outliers P98 eliminados        : {n_a - len(df)} "
                       f"(umbral: {p98:,.0f} COP)")

        if "ratio_liquidez" in df.columns:
            med = df["ratio_liquidez"].median()
            n_imp = df["ratio_liquidez"].isna().sum()
            df["ratio_liquidez"] = df["ratio_liquidez"].fillna(med)
            log.append(f"D4 ratio_liquidez imputados (med.): {n_imp} "
                       f"→ mediana={med:.3f} (justificado por no-normalidad H5)")

        self.df = df
        print(f"\n    Limpieza (justificada en EDA):")
        for linea in log:
            print(f"      {linea}")
        print(f"\n    Filas: {n_ini} → {len(df)} ({n_ini - len(df)} eliminadas en total)")
        return self

    # ── Etapa 5: Análisis estadístico ────────────────────────────────────

    @registrar_ejecucion
    @validar_normalidad(alpha=0.05)
    def analizar_distribucion(self) -> pd.Series:
        """
        Estadísticos del índice de riesgo.
        """
        if self.df is None or self.df.empty:
            print("    ⚠ No hay datos para analizar")
            return pd.Series(dtype=float)

        s = self.df["indice_riesgo"].dropna()
        print(f"\n    Estadísticos del Índice de Riesgo (n={len(s):,}):")
        print(f"      Mediana (robusto) : {s.median()*100:.4f}%")
        print(f"      Media             : {s.mean()*100:.4f}%")
        print(f"      Desv. estándar    : {s.std()*100:.4f}%")
        print(f"      Mínimo            : {s.min()*100:.4f}%")
        print(f"      P95               : {s.quantile(0.95)*100:.4f}%")
        print(f"      Máximo            : {s.max()*100:.4f}%")
        return s.describe()

    # ── Gráficas EDA ──────────────────────────────────────────────────────

    def _graficar_eda(self):
        df = self.df_crudo.copy()
        if df.empty:
            print("    ⚠ Sin datos para graficar EDA")
            return

        df_v = df[df["total_cartera"].notna() & df["indice_riesgo"].notna()]
        if df_v.empty:
            print("    ⚠ Sin datos válidos para gráficas EDA")
            return

        fig = plt.figure(figsize=(17, 12))
        fig.suptitle(
            "EDA — Análisis Exploratorio · Datos Crudos · Sistema Financiero CO",
            fontsize=13, fontweight="bold", y=0.99,
        )

        gs = gridspec.GridSpec(
            2, 3, figure=fig,
            hspace=0.55, wspace=0.42,
            left=0.07, right=0.96,
            top=0.90, bottom=0.09,
        )
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[0, 2])
        ax4 = fig.add_subplot(gs[1, 0])
        ax5 = fig.add_subplot(gs[1, 1])
        ax6 = fig.add_subplot(gs[1, 2])

        if "total_cartera" in df_v.columns:
            vals = df_v["total_cartera"] / 1e9
            ax1.hist(vals, bins=35, color=PALETA["primario"],
                     alpha=0.82, edgecolor="white")
            ax1.axvline(vals.median(), color=PALETA["secundario"],
                        linewidth=2, linestyle="--",
                        label=f"Mediana: {vals.median():.0f} B")
            ax1.set_title("H3 — Cartera Total por Municipio\n(asimetría detectada → outliers)")
            ax1.set_xlabel("Cartera (miles de millones COP)")
            ax1.set_ylabel("Frecuencia")
            ax1.legend()
            ax1.annotate(
                "Cola derecha → justifica\ntratamiento outliers (D3)",
                xy=(vals.quantile(0.85), ax1.get_ylim()[1] * 0.60),
                fontsize=7.5, color=PALETA["riesgo_alto"],
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3CD", alpha=0.85),
            )

        if "total_cartera" in df_v.columns:
            ax2.boxplot(
                df_v["total_cartera"].dropna() / 1e9,
                vert=True, patch_artist=True,
                boxprops=dict(facecolor=PALETA["primario"], alpha=0.55),
                medianprops=dict(color=PALETA["secundario"], linewidth=2.5),
                flierprops=dict(marker="o", color=PALETA["riesgo_alto"],
                                markersize=4, alpha=0.7, markeredgewidth=0),
                whiskerprops=dict(color=PALETA["neutro"], linewidth=1.2),
                capprops=dict(color=PALETA["neutro"], linewidth=1.5),
            )
            ax2.set_title("H4 — Boxplot Cartera Total\n(puntos = outliers IQR)")
            ax2.set_ylabel("Cartera (miles de millones COP)")
            ax2.set_xticks([])

        cols_ch = ["cartera_a", "cartera_b", "cartera_c", "cartera_d",
                   "cartera_e", "total_cartera", "total_captaciones",
                   "indice_riesgo", "ratio_liquidez"]
        cols_ch = [c for c in cols_ch if c in df.columns]
        comp = pd.DataFrame({c: [(~df[c].isna()).mean() * 100] for c in cols_ch})
        sns.heatmap(
            comp, ax=ax3, annot=True, fmt=".0f",
            cmap="RdYlGn", vmin=0, vmax=100,
            linewidths=0.6, cbar_kws={"label": "% datos presentes"},
            annot_kws={"size": 8, "weight": "bold"},
        )
        ax3.set_title("H2 — Completitud por Columna (%)\n(rojo = muchos nulos)")
        ax3.set_xticklabels(ax3.get_xticklabels(), rotation=38, ha="right", fontsize=7)
        ax3.set_yticks([])

        if "indice_riesgo" in df_v.columns:
            sr = df_v["indice_riesgo"].dropna() * 100
            ax4.hist(sr, bins=30, color=PALETA["primario"],
                     alpha=0.72, edgecolor="white", density=True, label="Histograma")
            sr.plot.kde(ax=ax4, color=PALETA["secundario"], linewidth=2, label="KDE")
            ax4.axvline(sr.median(), color=PALETA["neutro"], linewidth=1.5,
                        linestyle=":", label=f"Mediana={sr.median():.2f}%")
            ax4.set_title("H5 — Índice de Riesgo con KDE\n(cola derecha → no normal)")
            ax4.set_xlabel("Índice de Riesgo (%)")
            ax4.set_ylabel("Densidad")
            ax4.legend()

        if "indice_riesgo" in df_v.columns:
            sr2 = df_v["indice_riesgo"].dropna()
            (osm, osr), (slope, intercept, r) = stats.probplot(sr2, dist="norm")
            ax5.scatter(osm, osr, color=PALETA["primario"], alpha=0.65, s=22)
            ax5.plot(
                [min(osm), max(osm)],
                [slope * min(osm) + intercept, slope * max(osm) + intercept],
                color=PALETA["secundario"], linewidth=2, linestyle="--",
            )
            ax5.set_title(
                f"H5 — Q-Q Plot Índice de Riesgo\n"
                f"(R²={r**2:.3f} → {'normal' if r**2 > 0.96 else 'NO normal → usar mediana'})"
            )
            ax5.set_xlabel("Cuantiles teóricos (normal)")
            ax5.set_ylabel("Cuantiles observados")

        cols_corr = [c for c in ["total_cartera", "total_captaciones",
                                 "indice_riesgo", "ratio_liquidez"]
                     if c in df_v.columns]
        corr = df_v[cols_corr].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(
            corr, ax=ax6, mask=mask,
            annot=True, fmt=".2f", cmap="coolwarm",
            center=0, vmin=-1, vmax=1,
            linewidths=0.6, square=True,
            annot_kws={"size": 9, "weight": "bold"},
            cbar_kws={"shrink": 0.85},
        )
        ax6.set_title("Correlación entre Variables\n(triángulo inferior)")
        ax6.tick_params(axis="x", rotation=35)
        ax6.tick_params(axis="y", rotation=0)

        ruta = RUTA_SALIDA / "eda_datos_crudos.png"
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"    Gráficas EDA → {ruta}")

    # ── Gráficas de análisis final ────────────────────────────────────────

    @registrar_ejecucion
    def visualizar(self) -> "PipelineRiesgo":
        self._panel_riesgo()
        self._panel_composicion()
        return self

    def _panel_riesgo(self):
        df = self.df.copy()
        if df.empty:
            print("    ⚠ Sin datos para panel de riesgo")
            return

        df_v = df[df["indice_riesgo"].notna() & df["total_cartera"].notna()]
        if df_v.empty:
            print("    ⚠ Sin datos válidos para panel de riesgo")
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 11))
        fig.suptitle(
            "Panel de Riesgo Crediticio — Datos Limpios\nSistema Financiero Colombiano",
            fontsize=13, fontweight="bold",
        )
        fig.subplots_adjust(
            hspace=0.48, wspace=0.36,
            left=0.08, right=0.96,
            top=0.88, bottom=0.09,
        )

        ax = axes[0, 0]
        sr = df_v["indice_riesgo"] * 100
        ax.hist(sr, bins=28, color=PALETA["primario"], alpha=0.82, edgecolor="white")
        ax.axvline(sr.median(), color=PALETA["secundario"], linewidth=2,
                   linestyle="--", label=f"Mediana: {sr.median():.2f}%")
        ax.axvline(sr.mean(), color=PALETA["neutro"], linewidth=1.5,
                   linestyle=":", label=f"Media: {sr.mean():.2f}%")
        ax.set_title("Índice de Riesgo — Datos Limpios")
        ax.set_xlabel("Índice de Riesgo (%)")
        ax.set_ylabel("Frecuencia")
        ax.legend()

        ax = axes[0, 1]
        orden = ["sin_datos", "sin_riesgo", "riesgo_bajo",
                 "riesgo_moderado", "riesgo_alto", "riesgo_critico"]
        conteo = (df["nivel_riesgo"].value_counts()
                  .reindex(orden, fill_value=0)
                  .pipe(lambda s: s[s > 0]))
        col_map = {
            "sin_datos": PALETA["sin_datos"],
            "sin_riesgo": PALETA["sin_riesgo"],
            "riesgo_bajo": PALETA["riesgo_bajo"],
            "riesgo_moderado": PALETA["riesgo_mod"],
            "riesgo_alto": PALETA["riesgo_alto"],
            "riesgo_critico": PALETA["riesgo_crit"],
        }
        bars = ax.bar(
            range(len(conteo)), conteo.values,
            color=[col_map[k] for k in conteo.index],
            edgecolor="white", linewidth=0.8,
        )
        ax.set_xticks(range(len(conteo)))
        ax.set_xticklabels([k.replace("_", "\n") for k in conteo.index], fontsize=7.5)
        for bar, val in zip(bars, conteo.values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.25,
                    str(val), ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold")
        ax.set_title("Municipios por Nivel de Riesgo\n(Pattern Matching)")
        ax.set_ylabel("N° Municipios")

        ax = axes[1, 0]
        top10 = df_v.nlargest(10, "total_cartera").copy()
        top10["cartera_B"] = top10["total_cartera"] / 1e9
        colores_t = [
            PALETA["riesgo_crit"] if r > 0.05
            else PALETA["riesgo_mod"] if r > 0.01
            else PALETA["riesgo_bajo"]
            for r in top10["indice_riesgo"]
        ]
        barras = ax.barh(
            top10["municipio"].str[:18], top10["cartera_B"],
            color=colores_t, edgecolor="white", linewidth=0.7,
        )
        for barra, val in zip(barras, top10["cartera_B"]):
            ax.text(val + top10["cartera_B"].max() * 0.012,
                    barra.get_y() + barra.get_height() / 2,
                    f"{val:.0f} B", va="center", fontsize=7.5)
        ax.set_title("Top 10 Municipios — Cartera Total\n(color = nivel de riesgo)")
        ax.set_xlabel("Cartera (miles de millones COP)")
        ax.invert_yaxis()

        ax = axes[1, 1]
        df_sc = df_v.dropna(subset=["ratio_liquidez"])
        if not df_sc.empty:
            sc = ax.scatter(
                df_sc["ratio_liquidez"],
                df_sc["indice_riesgo"] * 100,
                c=np.log1p(df_sc["total_cartera"]),
                cmap="viridis", alpha=0.72, s=48,
                edgecolors="white", linewidths=0.3,
            )
            cbar = plt.colorbar(sc, ax=ax, pad=0.02)
            cbar.set_label("log(Cartera + 1)", fontsize=8)
            cbar.ax.tick_params(labelsize=7)

            ax.axhline(5, color=PALETA["riesgo_alto"], linewidth=1.3,
                       linestyle="--", alpha=0.75, label="Umbral riesgo alto (5%)")
            ax.axvline(1.0, color=PALETA["primario"], linewidth=1.3,
                       linestyle=":", alpha=0.75, label="Fondeo equilibrado (ratio=1)")

            xl, yl = ax.get_xlim(), ax.get_ylim()
            ax.text(xl[0] + (xl[1]-xl[0])*0.03, yl[1]*0.88,
                    "Subfondeo\n+ Riesgo Alto",
                    fontsize=7, color=PALETA["riesgo_crit"],
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.75))
            ax.text(xl[1]*0.55, yl[0] + (yl[1]-yl[0])*0.04,
                    "Bien fondeado\n+ Bajo Riesgo",
                    fontsize=7, color=PALETA["riesgo_bajo"],
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.75))

            ax.set_title("Liquidez vs Riesgo Crediticio\n(color = tamaño de cartera)")
            ax.set_xlabel("Ratio Liquidez (Captaciones / Cartera)")
            ax.set_ylabel("Índice de Riesgo (%)")
            ax.legend(fontsize=7.5)

        ruta = RUTA_SALIDA / "panel_analisis.png"
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"    Panel de riesgo → {ruta}")

    def _panel_composicion(self):
        df = self.df.copy()
        if df.empty:
            print("    ⚠ Sin datos para panel de composición")
            return

        df_v = df.dropna(subset=["cartera_a", "total_cartera"])

        cols_comp = [c for c in ["cartera_a", "cartera_b", "cartera_c", "cartera_d", "cartera_e"]
                     if c in df_v.columns]
        if not cols_comp or len(df_v) < 5:
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(
            "Composición Regulatoria de Cartera · Top 15 Municipios",
            fontsize=12, fontweight="bold",
        )
        fig.subplots_adjust(
            wspace=0.40,
            left=0.10, right=0.96,
            top=0.86, bottom=0.15,
        )

        top15 = df_v.nlargest(15, "total_cartera").set_index("municipio")
        top15 = top15[cols_comp].fillna(0)
        total_row = top15.sum(axis=1).replace(0, np.nan)
        top15_pct = top15.div(total_row, axis=0) * 100

        colores_comp = {
            "cartera_a": "#2ECC71",
            "cartera_b": "#F1C40F",
            "cartera_c": "#E67E22",
            "cartera_d": "#E74C3C",
            "cartera_e": "#8B0000",
        }
        labels_comp = {
            "cartera_a": "A — Normal",
            "cartera_b": "B — Observación",
            "cartera_c": "C — Subestándar",
            "cartera_d": "D — Dudosa",
            "cartera_e": "E — Pérdida",
        }

        bottom = np.zeros(len(top15_pct))
        for col in cols_comp:
            vals = top15_pct[col].values
            ax1.barh(
                range(len(top15_pct)), vals, left=bottom,
                color=colores_comp.get(col, "#BDC3C7"),
                label=labels_comp.get(col, col),
                edgecolor="white", linewidth=0.4,
            )
            bottom += vals

        ax1.set_yticks(range(len(top15_pct)))
        ax1.set_yticklabels([m[:17] for m in top15_pct.index], fontsize=7.5)
        ax1.set_xlabel("% de Cartera por Categoría Regulatoria")
        ax1.set_title("Composición de Cartera por Municipio\n(categorías A-E Superfinanciera)")
        ax1.invert_yaxis()
        ax1.legend(loc="lower right", fontsize=7.5, framealpha=0.88, ncol=1)
        ax1.set_xlim(0, 107)

        df_liq = df.dropna(subset=["ratio_liquidez"]).nlargest(20, "total_cartera")
        colores_liq = [
            PALETA["riesgo_crit"] if r < 0.5
            else PALETA["riesgo_mod"] if r < 1.0
            else PALETA["riesgo_bajo"]
            for r in df_liq["ratio_liquidez"]
        ]
        ax2.barh(
            range(len(df_liq)), df_liq["ratio_liquidez"].values,
            color=colores_liq, edgecolor="white", linewidth=0.5,
        )
        ax2.axvline(1.0, color=PALETA["primario"], linewidth=2,
                    linestyle="--", label="Equilibrio (ratio = 1)")
        ax2.set_yticks(range(len(df_liq)))
        ax2.set_yticklabels([m[:17] for m in df_liq["municipio"]], fontsize=7.5)
        ax2.invert_yaxis()
        ax2.set_xlabel("Captaciones / Cartera")
        ax2.set_title("Ratio de Liquidez por Municipio\n(rojo < 0.5  |  naranja < 1  |  verde ≥ 1)")
        ax2.legend(fontsize=8, framealpha=0.88)

        ruta = RUTA_SALIDA / "panel_composicion.png"
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"    Panel de composición → {ruta}")

    # ── Exportación JSON ──────────────────────────────────────────────────

    @registrar_ejecucion
    def exportar_json(self) -> Path:
        """
        Exporta resultado en JSON.
        """
        if self.df is None or self.df.empty:
            raise ValueError("No hay datos en self.df para exportar")

        resultado = ResultadoAnalisis(
            n_municipios=int(len(self.df)),
            cartera_total_billones=float(self.df["total_cartera"].sum() / 1e12),
            indice_riesgo_promedio=float(self.df["indice_riesgo"].mean()),
            pct_sin_riesgo=float(
                (self.df["nivel_riesgo"] == "sin_riesgo").sum() / len(self.df) * 100
            ),
            municipios=self.municipios,
        )
        ruta = RUTA_SALIDA / "resultado_analisis.json"
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(resultado.model_dump_json(indent=2))
        print(f"    JSON → {ruta}  (legible, portable, listo para FastAPI)")
        return ruta

    # ── Exportación Pickle ────────────────────────────────────────────────

    @registrar_ejecucion
    def exportar_pickle(self) -> Path:
        """
        Exporta en Pickle.
        """
        ruta = RUTA_SALIDA / "municipios.pkl"
        with open(ruta, "wb") as f:
            pickle.dump(self.municipios, f)
        print(f"    Pickle → {ruta}  (tipos Python nativos, solo Python)")
        return ruta

    # ── Reporte en consola ────────────────────────────────────────────────

    @registrar_ejecucion
    def imprimir_reporte(self) -> "PipelineRiesgo":
        if self.df is None or self.df.empty:
            print("    ⚠ No hay datos para reporte")
            return self

        df = self.df
        n = len(df)
        ct = df["total_cartera"].sum() / 1e12
        ri = df["indice_riesgo"].median() * 100
        rim = df["indice_riesgo"].mean() * 100
        pct = (df["nivel_riesgo"] == "sin_riesgo").sum() / n * 100

        print("\n" + "═" * 62)
        print("  REPORTE — SISTEMA FINANCIERO COLOMBIANO")
        print("═" * 62)
        print(f"  Fecha                     : {datetime.now():%Y-%m-%d %H:%M}")
        print(f"  Municipios (post-limpieza): {n:>10,}")
        print(f"  Cartera total             : {ct:>9.2f} Billones COP")
        print(f"  Índice riesgo mediana     : {ri:>9.4f} %  ← estadístico robusto")
        print(f"  Índice riesgo media       : {rim:>9.4f} %")
        print(f"  Municipios sin riesgo     : {pct:>9.1f} %")
        print()
        print("  Distribución por nivel de riesgo:")
        for nivel, cnt in df["nivel_riesgo"].value_counts().items():
            pn = cnt / n * 100
            barra = "█" * max(1, int(pn / 2))
            print(f"    {nivel:<24} {barra:<24} {cnt:>4} ({pn:4.1f}%)")
        print("═" * 62 + "\n")
        return self

    # ── Interpretación Automática ─────────────────────────────────────────

    @registrar_ejecucion
    def interpretar_resultados(self) -> "PipelineRiesgo":
        if self.df is None or self.df.empty:
            print("    ⚠ No hay datos para interpretar")
            return self

        df = self.df
        n = len(df)
        ri_mediana = df["indice_riesgo"].median() * 100
        riesgo_alto_critico = df[df["nivel_riesgo"].isin(["riesgo_alto", "riesgo_critico"])]
        pct_peligro = (len(riesgo_alto_critico) / n) * 100
        
        print("\n" + "💡 " * 31)
        print("  INTERPRETACIÓN AUTOMATIZADA DE RESULTADOS")
        print("💡 " * 31)
        
        # 1. Análisis de tendencia central
        print(f"\n  ▶ 1. MEDIANA DE RIESGO: El índice de mora representativo es de {ri_mediana:.2f}%.")
        if ri_mediana < 5.0:
            print("       Interpretación: El sistema en general muestra un comportamiento SANO,")
            print("       con el municipio promedio manteniendo sus niveles de mora controlados.")
        elif ri_mediana < 10.0:
            print("       Interpretación: El sistema muestra un comportamiento de ALERTA MODERADA.")
            print("       Se recomienda monitoreo constante de la cartera vigente.")
        else:
            print("       Interpretación: El sistema está en un estado CRÍTICO generalizado,")
            print("       la cartera irrecuperable de los municipios evaluados es muy alta.")

        # 2. Análisis de concentración de riesgo
        print(f"\n  ▶ 2. CONCENTRACIÓN DE PELIGRO: {pct_peligro:.1f}% de los municipios están en nivel Alto o Crítico.")
        if pct_peligro > 30.0:
            print("       Alerta: Una proporción alarmante del sistema está comprometida.")
            print("       Se deben priorizar políticas de salvamento o reestructuración de deuda urgentemente.")
        elif pct_peligro > 0.0:
            print("       Atención: La mayoría del sistema está estable, pero existen bolsas de riesgo focalizadas.")
            print("       (Ver gráficas en carpeta 'outputs' para identificar los municipios específicos).")
        else:
            print("       Excelente: No se registran municipios en niveles de riesgo preocupantes.")

        # 3. Análisis de liquidez
        df_liq = df.dropna(subset=["ratio_liquidez"])
        if not df_liq.empty:
            liq_mediana = df_liq["ratio_liquidez"].median()
            print(f"\n  ▶ 3. RATIO DE LIQUIDEZ: La mediana de captaciones vs cartera es {liq_mediana:.2f}x.")
            if liq_mediana < 0.8:
                print("       Riesgo Estructural: Hay un déficit general de fondeo. Los municipios prestan más")
                print("       dinero del que logran captar de ahorradores, dependiendo de fondeo externo.")
            elif liq_mediana < 1.0:
                print("       Situación Ajustada: El nivel de préstamos está a la par con el ahorro.")
            else:
                print("       Sistema Líquido: Existe un colchón saludable de captaciones frente a la cartera total.")
        
        print("\n" + "💡 " * 31 + "\n")
        return self

    # ── Datos sintéticos (fallback) ───────────────────────────────────────

    @staticmethod
    def _datos_sinteticos() -> list[dict]:
        rng = np.random.default_rng(42)
        muns = [
            "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
            "Cúcuta", "Bucaramanga", "Pereira", "Santa Marta", "Ibagué",
            "Manizales", "Pasto", "Neiva", "Villavicencio", "Armenia",
            "Sincelejo", "Valledupar", "Montería", "Popayán", "Tunja",
            "Florencia", "Quibdó", "Riohacha", "Mocoa", "Yopal",
            "Leticia", "Puerto Carreño", "San Andrés", "Inírida", "Mitú",
        ] * 2

        data = []
        for mun in muns:
            cartera = rng.uniform(5e8, 8e11)
            mora = rng.uniform(0, 0.18) * cartera
            data.append({
                COLUMNAS["municipio"]: mun,
                COLUMNAS["cartera_a"]: cartera * rng.uniform(0.60, 0.80),
                COLUMNAS["cartera_b"]: cartera * rng.uniform(0.05, 0.15),
                COLUMNAS["cartera_c"]: mora * 0.40,
                COLUMNAS["cartera_d"]: mora * 0.35,
                COLUMNAS["cartera_e"]: mora * 0.25,
                COLUMNAS["cartera_tot"]: cartera,
                COLUMNAS["captaciones"]: cartera * rng.uniform(0.40, 2.0),
            })
        return data


# ══════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════

def main():
    """
    Orden correcto del pipeline:
      Ingesta → DataFrame → EDA → Limpieza → Análisis → Visualización → Export
    """
    print("\n[PIPELINE] Sistema de Analisis de Riesgo Crediticio")
    print("  Colombia - Datos Abiertos Gov.co\n")

    cliente = ClienteAPIFinanciero(base_url=API_BASE, timeout=10)

    try:
        pipeline = PipelineRiesgo(cliente)

        # Solo métodos encadenables (retornan self)
        (pipeline
            .ingestar(limite=350)
            .construir_dataframe()
            .eda()
            .limpiar()
        )

        # Métodos no encadenables / con retornos distintos
        pipeline.analizar_distribucion()   # ← corregido (sin pasar data)
        pipeline.visualizar()
        pipeline.exportar_json()
        pipeline.exportar_pickle()
        pipeline.imprimir_reporte()
        pipeline.interpretar_resultados()

        # ── Demo de Pattern Matching ──────────────────────────────────────
        print("\n📋  Demo: Pattern Matching — clasificar_riesgo()")
        print("─" * 52)
        casos = [
            ({"indice_riesgo": None},  "sin_datos"),
            ({"indice_riesgo": 0.0},   "sin_riesgo"),
            ({"indice_riesgo": 0.003}, "riesgo_bajo"),
            ({"indice_riesgo": 0.025}, "riesgo_moderado"),
            ({"indice_riesgo": 0.08},  "riesgo_alto"),
            ({"indice_riesgo": 0.22},  "riesgo_critico"),
            ({},                       "sin_datos"),
        ]
        for obs, esperado in casos:
            resultado = clasificar_riesgo(obs)
            ok = "✓" if resultado == esperado else "✗"
            print(f"  {ok} {str(obs):38} → {resultado}")

        print(f"\n✅  Análisis completado. Outputs en: {RUTA_SALIDA.resolve()}")
        print("   · eda_datos_crudos.png    — hallazgos EDA H1–H6")
        print("   · panel_analisis.png      — riesgo crediticio")
        print("   · panel_composicion.png   — composición de cartera")
        print("   · resultado_analisis.json")
        print("   · municipios.pkl\n")

    finally:
        cliente.cerrar()


if __name__ == "__main__":
    main()
