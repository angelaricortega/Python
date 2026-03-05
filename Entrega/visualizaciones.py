"""
visualizaciones.py — Módulo de Gráficas Profesionales
======================================================
Semana 3: Visualizaciones profesionales con paleta coherente.

CONCEPTOS CLAVE:
  1. Paleta única: TODAS las gráficas usan la misma paleta (config.PALETA)
  2. Nivel de riesgo → color: cada nivel tiene un color fijo (RIESGO_COLOR)
  3. Zero clutter: sin bordes superiores/derechos, grid sutil
  4. Títulos interpretativos: no solo describen, sino que explican

JUSTIFICACIÓN ESTADÍSTICA:
  - EDA antes de limpieza: documentar hallazgos (H1-H6) antes de decidir
  - Boxplot + IQR: detecta outliers sin asumir normalidad
  - Q-Q Plot: test visual de normalidad complementa Shapiro-Wilk
  - Heatmap de correlación: identifica multicolinearidad

MODULARIZACIÓN:
  Cada función genera UNA gráfica específica. Esto permite:
    - Reutilizar en notebook y script
    - Probar individualmente
    - Cambiar estilo en un solo lugar (config.py)
"""

# ── Librería estándar ────────────────────────────────────────────────────
from pathlib import Path
from typing import Optional, Dict, Any

# ── Terceros ─────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats

# ── Locales ──────────────────────────────────────────────────────────────
from config import PALETA, RIESGO_COLOR, RUTA_SALIDA, UMBRALES_RIESGO


# ══════════════════════════════════════════════════════════════════════════
# 1. GRÁFICA EDA COMPLETO (6 subgráficas)
# ══════════════════════════════════════════════════════════════════════════

def graficar_eda_completo(
    df_crudo: pd.DataFrame,
    titulo: str = "EDA — Análisis Exploratorio · Datos Crudos",
    ruta_salida: Optional[Path] = None,
) -> Path:
    """
    Genera panel EDA con 6 subgráficas para documentar hallazgos antes de limpiar.

    HALLAZGOS DOCUMENTADOS (H1-H6):
      H1: Dimensiones del dataset y duplicados
      H2: Completitud de datos (% no nulos por columna)
      H3: Distribución de cartera total (asimetría, outliers)
      H4: Boxplot con outliers IQR
      H5: Histograma + KDE + Q-Q Plot (normalidad)
      H6: Correlación entre variables

    Args:
        df_crudo: DataFrame con datos sin limpiar
        titulo: título principal de la figura
        ruta_salida: directorio donde guardar (default: config.RUTA_SALIDA)

    Returns:
        Path: ruta del archivo guardado
    """
    if df_crudo.empty:
        raise ValueError("df_crudo está vacío")

    ruta = ruta_salida or RUTA_SALIDA
    ruta.mkdir(parents=True, exist_ok=True)

    # Filtrar datos válidos para gráficas
    df_v = df_crudo[
        df_crudo["total_cartera"].notna() &
        df_crudo["indice_riesgo"].notna()
    ].copy()

    if df_v.empty:
        raise ValueError("No hay datos válidos (total_cartera e indice_riesgo requeridos)")

    # Crear figura con GridSpec para layout personalizado
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle(titulo, fontsize=14, fontweight="bold", y=0.99)

    gs = gridspec.GridSpec(
        2, 3, figure=fig,
        hspace=0.50, wspace=0.38,
        left=0.06, right=0.97,
        top=0.91, bottom=0.07,
    )

    # Ejes
    ax1 = fig.add_subplot(gs[0, 0])  # Histograma cartera
    ax2 = fig.add_subplot(gs[0, 1])  # Boxplot
    ax3 = fig.add_subplot(gs[0, 2])  # Heatmap completitud
    ax4 = fig.add_subplot(gs[1, 0])  # Histograma + KDE índice
    ax5 = fig.add_subplot(gs[1, 1])  # Q-Q Plot
    ax6 = fig.add_subplot(gs[1, 2])  # Heatmap correlación

    # ── H1: Histograma de cartera total ──────────────────────────────────
    if "total_cartera" in df_v.columns:
        vals = df_v["total_cartera"] / 1e9  # miles de millones
        median_val = vals.median()

        ax1.hist(vals, bins=35, color=PALETA["primario"], alpha=0.80,
                 edgecolor="white", linewidth=0.5)
        ax1.axvline(median_val, color=PALETA["secundario"], linewidth=2.5,
                    linestyle="--", label=f"Mediana: {median_val:.0f} B COP")

        ax1.set_title(
            "H1 — Distribución de Cartera Total\n(asimetría derecha → outliers)",
            fontsize=11, fontweight="bold"
        )
        ax1.set_xlabel("Cartera (miles de millones COP)", fontsize=10)
        ax1.set_ylabel("Frecuencia", fontsize=10)
        ax1.legend(loc="upper right", fontsize=9)

        # Anotación interpretativa
        ax1.annotate(
            "Cola derecha → justifica\ntratamiento de outliers (D3)",
            xy=(vals.quantile(0.85), ax1.get_ylim()[1] * 0.55),
            fontsize=8, color=PALETA["riesgo_alto"],
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF3CD",
                     edgecolor=PALETA["riesgo_alto"], alpha=0.90),
        )

    # ── H2: Boxplot de cartera ───────────────────────────────────────────
    if "total_cartera" in df_v.columns:
        datos_box = df_v["total_cartera"].dropna() / 1e9

        bp = ax2.boxplot(
            datos_box, vert=True, patch_artist=True,
            boxprops=dict(facecolor=PALETA["primario"], alpha=0.50,
                         edgecolor=PALETA["neutro"], linewidth=1),
            medianprops=dict(color=PALETA["secundario"], linewidth=3),
            whiskerprops=dict(color=PALETA["neutro"], linewidth=1.5),
            capprops=dict(color=PALETA["neutro"], linewidth=2),
            flierprops=dict(marker="o", color=PALETA["riesgo_crit"],
                           markersize=6, alpha=0.70, markeredgewidth=0),
        )

        ax2.set_title(
            "H2 — Boxplot · Outliers IQR\n(puntos = valores atípicos)",
            fontsize=11, fontweight="bold"
        )
        ax2.set_ylabel("Cartera (miles de millones COP)", fontsize=10)
        ax2.set_xticks([])

        # Calcular límites IQR
        q1, q3 = np.percentile(datos_box, [25, 75])
        iqr = q3 - q1
        lim_sup = q3 + 1.5 * iqr

        ax2.text(
            1.7, 0.95,
            f"Límite IQR: {lim_sup:,.0f} B",
            transform=ax2.transAxes, fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="#F8F9FA",
                     edgecolor=PALETA["neutro"], alpha=0.80),
        )

    # ── H3: Heatmap de completitud ───────────────────────────────────────
    cols_check = [c for c in ["cartera_a", "cartera_b", "cartera_c",
                               "cartera_d", "cartera_e", "total_cartera",
                               "total_captaciones", "indice_riesgo",
                               "ratio_liquidez"]
                  if c in df_crudo.columns]

    if cols_check:
        completitud = pd.DataFrame({
            c: [(~df_crudo[c].isna()).mean() * 100] for c in cols_check
        })

        sns.heatmap(
            completitud, ax=ax3, annot=True, fmt=".0f",
            cmap="RdYlGn", vmin=0, vmax=100,
            linewidths=0.8, cbar_kws={"label": "% datos presentes", "shrink": 0.8},
            annot_kws={"size": 9, "weight": "bold", "color": "#1E293B"},
        )

        ax3.set_title(
            "H3 — Completitud por Columna (%)\n(rojo = muchos nulos)",
            fontsize=11, fontweight="bold"
        )
        ax3.set_xticklabels(ax3.get_xticklabels(), rotation=40, ha="right", fontsize=8)
        ax3.set_yticks([])

    # ── H4: Histograma + KDE índice de riesgo ────────────────────────────
    if "indice_riesgo" in df_v.columns:
        sr = df_v["indice_riesgo"].dropna() * 100  # a porcentaje
        median_pct = sr.median()

        ax4.hist(sr, bins=30, color=PALETA["primario"], alpha=0.70,
                 edgecolor="white", linewidth=0.5, density=True,
                 label="Histograma")
        sns.kdeplot(sr, ax=ax4, color=PALETA["secundario"],
                    linewidth=2.5, label="KDE")

        ax4.axvline(median_pct, color=PALETA["neutro"], linewidth=2,
                    linestyle=":", label=f"Mediana={median_pct:.2f}%")

        # Líneas de umbrales
        for nombre, umbral in UMBRALES_RIESGO.items():
            if umbral > 0:
                ax4.axvline(umbral * 100, color=RIESGO_COLOR[nombre],
                           linewidth=1.5, linestyle="--", alpha=0.60,
                           label=f"{nombre.replace('_', ' ').title()}")

        ax4.set_title(
            "H4 — Índice de Riesgo con KDE\n(cola derecha → no normal)",
            fontsize=11, fontweight="bold"
        )
        ax4.set_xlabel("Índice de Riesgo (%)", fontsize=10)
        ax4.set_ylabel("Densidad", fontsize=10)
        ax4.legend(ncol=2, fontsize=8, loc="upper right")

    # ── H5: Q-Q Plot de normalidad ───────────────────────────────────────
    if "indice_riesgo" in df_v.columns:
        sr2 = df_v["indice_riesgo"].dropna()

        if len(sr2) >= 3:
            (osm, osr), (slope, intercept, r) = stats.probplot(
                sr2, dist="norm", fit=True
            )

            ax5.scatter(osm, osr, color=PALETA["primario"], alpha=0.65, s=25)
            ax5.plot(
                [min(osm), max(osm)],
                [slope * min(osm) + intercept, slope * max(osm) + intercept],
                color=PALETA["secundario"], linewidth=2.5, linestyle="--",
            )

            normalidad = "NORMAL" if r**2 > 0.96 else "NO NORMAL"
            accion = "media válida" if r**2 > 0.96 else "usar mediana"

            ax5.set_title(
                f"H5 — Q-Q Plot · {normalidad}\n(R²={r**2:.3f} → {accion})",
                fontsize=11, fontweight="bold"
            )
            ax5.set_xlabel("Cuantiles teóricos (Normal)", fontsize=10)
            ax5.set_ylabel("Cuantiles observados", fontsize=10)

            # Estadístico de Shapiro
            if len(sr2) <= 5000:
                w, p = stats.shapiro(sr2)
                ax5.text(
                    0.02, 0.98,
                    f"Shapiro: W={w:.3f}, p={p:.4f}",
                    transform=ax5.transAxes, fontsize=8,
                    verticalalignment="top",
                    bbox=dict(boxstyle="round", facecolor="#F8F9FA",
                             edgecolor=PALETA["neutro"], alpha=0.80),
                )

    # ── H6: Heatmap de correlación ───────────────────────────────────────
    cols_corr = [c for c in ["total_cartera", "total_captaciones",
                             "indice_riesgo", "ratio_liquidez"]
                 if c in df_v.columns]

    if len(cols_corr) >= 2:
        corr = df_v[cols_corr].corr()

        mask = np.triu(np.ones_like(corr, dtype=bool))

        sns.heatmap(
            corr, ax=ax6, mask=mask,
            annot=True, fmt=".2f", cmap="coolwarm",
            center=0, vmin=-1, vmax=1,
            linewidths=0.8, square=True,
            annot_kws={"size": 10, "weight": "bold", "color": "#1E293B"},
            cbar_kws={"shrink": 0.85, "label": "Correlación"},
        )

        ax6.set_title(
            "H6 — Correlación (Triángulo Superior)\n(identifica multicolinearidad)",
            fontsize=11, fontweight="bold"
        )
        ax6.tick_params(axis="x", rotation=35, labelsize=9)
        ax6.tick_params(axis="y", rotation=0, labelsize=9)

    # Guardar figura
    archivo = ruta / "eda_datos_crudos.png"
    plt.savefig(
        archivo, dpi=300, bbox_inches="tight",
        facecolor="white", edgecolor="none"
    )
    plt.close(fig)

    print(f"  ✓ EDA guardado: {archivo}")
    return archivo


# ══════════════════════════════════════════════════════════════════════════
# 2. GRÁFICA DE ANÁLISIS FINAL (datos limpios)
# ══════════════════════════════════════════════════════════════════════════

def graficar_analisis_final(
    df: pd.DataFrame,
    titulo: str = "Análisis Final · Datos Limpios",
    ruta_salida: Optional[Path] = None,
) -> Path:
    """
    Genera panel de análisis final con datos limpios (4 subgráficas).

    SUBGRÁFICAS:
      1. Histograma índice de riesgo con media/mediana
      2. Barras por nivel de riesgo (Pattern Matching)
      3. Top 8 municipios por cartera (coloreados por riesgo)
      4. Scatter liquidez vs riesgo (cuadrantes interpretativos)

    Args:
        df: DataFrame con datos limpios
        titulo: título principal
        ruta_salida: directorio de salida

    Returns:
        Path: ruta del archivo guardado
    """
    if df.empty:
        raise ValueError("df está vacío")

    ruta = ruta_salida or RUTA_SALIDA
    ruta.mkdir(parents=True, exist_ok=True)

    df_v = df[
        df["total_cartera"].notna() &
        df["indice_riesgo"].notna() &
        df["nivel_riesgo"].notna()
    ].copy()

    if df_v.empty:
        raise ValueError("No hay datos válidos para gráficas")

    # Crear figura
    fig = plt.figure(figsize=(18, 10))
    fig.suptitle(titulo, fontsize=14, fontweight="bold", y=0.99)

    gs = gridspec.GridSpec(
        2, 2, figure=fig,
        hspace=0.45, wspace=0.35,
        left=0.06, right=0.97,
        top=0.91, bottom=0.08,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    # ── 1. Histograma índice de riesgo ───────────────────────────────────
    sr = df_v["indice_riesgo"].dropna() * 100
    median_val = sr.median()
    mean_val = sr.mean()

    ax1.hist(sr, bins=28, color=PALETA["primario"], alpha=0.75,
             edgecolor="white", linewidth=0.5, density=True)
    sns.kdeplot(sr, ax=ax1, color=PALETA["secundario"], linewidth=2.5)

    ax1.axvline(median_val, color=PALETA["neutro"], linewidth=2,
                linestyle="--", label=f"Mediana: {median_val:.2f}%")
    ax1.axvline(mean_val, color=PALETA["acento"], linewidth=2,
                linestyle=":", label=f"Media: {mean_val:.2f}%")

    ax1.set_title(
        "Distribución del Índice de Riesgo\n(comparar media vs mediana)",
        fontsize=11, fontweight="bold"
    )
    ax1.set_xlabel("Índice de Riesgo (%)", fontsize=10)
    ax1.set_ylabel("Densidad", fontsize=10)
    ax1.legend(fontsize=9)

    # ── 2. Barras por nivel de riesgo ────────────────────────────────────
    if "nivel_riesgo" in df_v.columns:
        conteo = df_v["nivel_riesgo"].value_counts()
        porcentajes = (conteo / len(df_v) * 100).round(1)

        # Ordenar por nivel de riesgo (no alfabéticamente)
        orden = ["sin_riesgo", "riesgo_bajo", "riesgo_moderado",
                 "riesgo_alto", "riesgo_critico", "sin_datos"]

        colores = [RIESGO_COLOR.get(n, PALETA["neutro"]) for n in orden if n in conteo.index]
        valores = [conteo.get(n, 0) for n in orden if n in conteo.index]
        etiquetas = [n.replace("_", " ").title() for n in orden if n in conteo.index]

        barras = ax2.barh(etiquetas, valores, color=colores, alpha=0.85,
                         edgecolor="white", linewidth=1)

        # Anotar valores
        for barra, pct in zip(barras, porcentajes.values()):
            ancho = barra.get_width()
            ax2.text(
                ancho + max(valores) * 0.01,
                barra.get_y() + barra.get_height() / 2,
                f"{int(ancho)} ({pct}%)",
                va="center", fontsize=9, fontweight="bold",
                color="#1E293B",
            )

        ax2.set_title(
            "Distribución por Nivel de Riesgo\n(Pattern Matching)",
            fontsize=11, fontweight="bold"
        )
        ax2.set_xlabel("Cantidad de Municipios", fontsize=10)
        ax2.set_xlim(0, max(valores) * 1.15)

    # ── 3. Top 8 municipios por cartera ──────────────────────────────────
    top8 = df_v.nlargest(8, "total_cartera")[
        ["municipio", "total_cartera", "nivel_riesgo"]
    ].copy()

    top8["cartera_b"] = top8["total_cartera"] / 1e9
    colores_top = [RIESGO_COLOR.get(n, PALETA["neutro"])
                   for n in top8["nivel_riesgo"]]

    barras = ax3.barh(top8["municipio"], top8["cartera_b"], color=colores_top,
                     alpha=0.85, edgecolor="white", linewidth=1)

    ax3.set_title(
        "Top 8 Municipios por Cartera\n(coloreados por nivel de riesgo)",
        fontsize=11, fontweight="bold"
    )
    ax3.set_xlabel("Cartera (miles de millones COP)", fontsize=10)
    ax3.invert_yaxis()  # el mayor arriba

    # Anotar valores
    for barra, val in zip(barras, top8["total_cartera"]):
        ancho = barra.get_width()
        ax3.text(
            ancho + max(top8["cartera_b"]) * 0.01,
            barra.get_y() + barra.get_height() / 2,
            f"${val/1e9:.1f}B",
            va="center", fontsize=9, fontweight="bold",
            color="#1E293B",
        )

    # ── 4. Scatter liquidez vs riesgo ────────────────────────────────────
    if "ratio_liquidez" in df_v.columns and "indice_riesgo" in df_v.columns:
        df_plot = df_v[
            (df_v["ratio_liquidez"].notna()) &
            (df_v["indice_riesgo"].notna())
        ].copy()

        x = df_plot["ratio_liquidez"]
        y = df_plot["indice_riesgo"] * 100

        # Colores por nivel de riesgo
        colores_scatter = [
            RIESGO_COLOR.get(n, PALETA["neutro"])
            for n in df_plot["nivel_riesgo"]
        ]

        scatter = ax4.scatter(x, y, c=colores_scatter, alpha=0.65, s=45,
                             edgecolors="white", linewidth=0.5)

        # Líneas de cuadrantes
        med_liq = df_plot["ratio_liquidez"].median()
        med_riesgo = df_plot["indice_riesgo"].median() * 100

        ax4.axvline(med_liq, color=PALETA["neutro"], linewidth=1.5,
                   linestyle="--", alpha=0.70)
        ax4.axhline(med_riesgo, color=PALETA["neutro"], linewidth=1.5,
                   linestyle="--", alpha=0.70)

        # Anotar cuadrantes
        ax4.text(
            med_liq * 1.02, df_plot["indice_riesgo"].max() * 100 * 0.95,
            "Alto Riesgo\nBaja Liquidez", fontsize=8,
            color=PALETA["riesgo_crit"], fontweight="bold",
        )
        ax4.text(
            med_liq * 0.55, df_plot["indice_riesgo"].max() * 100 * 0.95,
            "Alto Riesgo\nAlta Liquidez", fontsize=8,
            color=PALETA["riesgo_alto"], fontweight="bold",
        )
        ax4.text(
            med_liq * 1.02, med_riesgo * 0.3,
            "Bajo Riesgo\nBaja Liquidez", fontsize=8,
            color=PALETA["riesgo_bajo"], fontweight="bold",
        )
        ax4.text(
            med_liq * 0.55, med_riesgo * 0.3,
            "Bajo Riesgo\nAlta Liquidez", fontsize=8,
            color=PALETA["sin_riesgo"], fontweight="bold",
        )

        ax4.set_title(
            "Liquidez vs Riesgo\n(cuadrantes interpretativos)",
            fontsize=11, fontweight="bold"
        )
        ax4.set_xlabel("Ratio de Liquidez", fontsize=10)
        ax4.set_ylabel("Índice de Riesgo (%)", fontsize=10)

    # Guardar
    archivo = ruta / "panel_analisis.png"
    plt.savefig(
        archivo, dpi=300, bbox_inches="tight",
        facecolor="white", edgecolor="none"
    )
    plt.close(fig)

    print(f"  ✓ Análisis guardado: {archivo}")
    return archivo


# ══════════════════════════════════════════════════════════════════════════
# 3. GRÁFICA DE COMPOSICIÓN DE CARTERA
# ══════════════════════════════════════════════════════════════════════════

def graficar_composicion_cartera(
    df: pd.DataFrame,
    titulo: str = "Composición de Cartera · Clasificación Regulatoria",
    ruta_salida: Optional[Path] = None,
) -> Path:
    """
    Genera panel de composición de cartera (2 subgráficas).

    SUBGRÁFICAS:
      1. Stacked bars: composición A-E de cartera por municipio (%)
      2. Barras horizontales: ratio de liquidez con línea de equilibrio

    Args:
        df: DataFrame con datos limpios
        titulo: título principal
        ruta_salida: directorio de salida

    Returns:
        Path: ruta del archivo guardado
    """
    if df.empty:
        raise ValueError("df está vacío")

    ruta = ruta_salida or RUTA_SALIDA
    ruta.mkdir(parents=True, exist_ok=True)

    df_v = df[df["total_cartera"].notna()].copy()

    if df_v.empty:
        raise ValueError("No hay datos válidos para composición")

    # Crear figura
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 10),
        gridspec_kw={"height_ratios": [1.2, 0.8], "hspace": 0.35}
    )
    fig.suptitle(titulo, fontsize=14, fontweight="bold", y=0.99)

    # ── 1. Stacked bars: composición A-E ─────────────────────────────────
    # Seleccionar top 10 municipios por cartera
    top10 = df_v.nlargest(10, "total_cartera")[
        ["municipio", "cartera_a", "cartera_b", "cartera_c",
         "cartera_d", "cartera_e", "total_cartera"]
    ].copy()

    # Calcular porcentajes
    for col in ["cartera_a", "cartera_b", "cartera_c", "cartera_d", "cartera_e"]:
        top10[f"{col}_pct"] = (top10[col] / top10["total_cartera"] * 100).fillna(0)

    cols_pct = ["cartera_a_pct", "cartera_b_pct", "cartera_c_pct",
                "cartera_d_pct", "cartera_e_pct"]
    cols_labels = ["A (Normal)", "B (Obs)", "C (Sub)", "D (Dud)", "E (Perd)"]
    cols_colors = [PALETA["sin_riesgo"], PALETA["riesgo_bajo"],
                   PALETA["riesgo_mod"], PALETA["riesgo_alto"],
                   PALETA["riesgo_crit"]]

    # Stacked bar
    bottom = np.zeros(len(top10))

    for col, label, color in zip(cols_pct, cols_labels, cols_colors):
        ax1.bar(
            range(len(top10)), top10[col], bottom=bottom,
            label=label, color=color, alpha=0.85, edgecolor="white", linewidth=0.5
        )
        bottom += top10[col]

    ax1.set_xticks(range(len(top10)))
    ax1.set_xticklabels(top10["municipio"], rotation=35, ha="right", fontsize=9)
    ax1.set_ylabel("Porcentaje de Cartera Total (%)", fontsize=10)
    ax1.set_title(
        "Composición de Cartera por Categoría (Top 10)\n(A=Normal, E=Pérdida)",
        fontsize=11, fontweight="bold"
    )
    ax1.legend(loc="upper left", ncol=3, fontsize=9)
    ax1.set_ylim(0, 105)

    # ── 2. Ratio de liquidez ─────────────────────────────────────────────
    liq_top = df_v.nlargest(10, "total_cartera")[
        ["municipio", "ratio_liquidez"]
    ].copy()

    colores_liq = [
        PALETA["sin_riesgo"] if r >= 1.0 else
        PALETA["riesgo_mod"] if r >= 0.8 else
        PALETA["riesgo_alto"]
        for r in liq_top["ratio_liquidez"]
    ]

    barras = ax2.barh(liq_top["municipio"], liq_top["ratio_liquidez"],
                     color=colores_liq, alpha=0.85, edgecolor="white", linewidth=1)

    # Línea de equilibrio (liquidez = 1.0)
    ax2.axvline(1.0, color=PALETA["secundario"], linewidth=2.5,
               linestyle="--", label="Equilibrio (1.0)")

    ax2.set_title(
        "Ratio de Liquidez (Captaciones / Cartera)\n(>1.0 = saludable)",
        fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("Ratio de Liquidez", fontsize=10)
    ax2.legend(loc="upper right", fontsize=9)
    ax2.invert_yaxis()

    # Anotar valores
    for barra, val in zip(barras, liq_top["ratio_liquidez"]):
        ancho = barra.get_width()
        ax2.text(
            ancho + 0.05,
            barra.get_y() + barra.get_height() / 2,
            f"{val:.2f}",
            va="center", fontsize=9, fontweight="bold",
            color="#1E293B",
        )

    # Guardar
    archivo = ruta / "panel_composicion.png"
    plt.savefig(
        archivo, dpi=300, bbox_inches="tight",
        facecolor="white", edgecolor="none"
    )
    plt.close(fig)

    print(f"  ✓ Composición guardada: {archivo}")
    return archivo
