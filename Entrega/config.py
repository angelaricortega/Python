"""
config.py — Configuración Global del Proyecto
==============================================
Semana 1: Configuración centralizada para reproducibilidad.

CONCEPTO APLICADO — Modularización (Semana 1):
  Centralizar la configuración en UN solo archivo permite:
  1. Cambiar la paleta de colores → afecta TODAS las gráficas
  2. Cambiar la URL de la API → afecta TODOS los módulos
  3. Cross-platform con pathlib (Windows/Linux/Mac)

  JUSTIFICACIÓN:
    Sin config.py, cada módulo tendría sus propias constantes.
    Un cambio de paleta requeriría editar 5+ archivos.
    Con config.py, se edita UN archivo y todo se actualiza.

PALETA "ROSADITO BONITO":
  Estilo visual coherente usando tonos rosas/magentas como colores
  primarios y secundarios, manteniendo colores semánticos para
  los niveles de riesgo (verde → amarillo → rojo).
"""

# ── Librería estándar ────────────────────────────────────────────────────
from pathlib import Path

# ── Terceros ─────────────────────────────────────────────────────────────
import matplotlib.pyplot as plt


# ══════════════════════════════════════════════════════════════════════════
# 1. API DE DATOS ABIERTOS
# ══════════════════════════════════════════════════════════════════════════

# API Socrata de Datos Abiertos Colombia
# Endpoint: Cartera y captaciones del sistema financiero por municipio
API_BASE = "https://www.datos.gov.co/resource/3kqn-n4za.json"

# Timeout para peticiones HTTP (segundos)
HTTP_TIMEOUT = 15

# Límite por defecto de registros a descargar
DEFAULT_LIMIT = 500


# ══════════════════════════════════════════════════════════════════════════
# 2. MAPEO DE COLUMNAS
# ══════════════════════════════════════════════════════════════════════════

# La API devuelve nombres en snake_case. Este mapeo traduce a nombres
# amigables en español que usaremos en el DataFrame y gráficas.
COLUMNAS = {
    "municipio":       "nombre_municipio",
    "cartera_a":       "cartera_categoria_a",
    "cartera_b":       "cartera_categoria_b",
    "cartera_c":       "cartera_categoria_c",
    "cartera_d":       "cartera_categoria_d",
    "cartera_e":       "cartera_categoria_e",
    "cartera_tot":     "total_cartera",
    "captaciones":     "total_captaciones",
}


# ══════════════════════════════════════════════════════════════════════════
# 3. PALETA DE COLORES COHERENTE — Estilo "Rosadito Bonito" 🌸
# ══════════════════════════════════════════════════════════════════════════
#
# DISEÑO DE LA PALETA:
#   Se eligieron tonos rosas/magentas como colores estructura les porque:
#   1. Transmiten calidez y cercanía (vs. colores corporativos fríos)
#   2. Hot Pink (#FF69B4) como primario: vibrante, alto contraste
#   3. Rose (#FF007F) como secundario: énfasis sin competir
#   4. Colores de riesgo mantienen semántica universal (verde→rojo)
#
#   COHERENCIA VISUAL:
#     Usar UNA paleta en TODAS las gráficas del proyecto asegura
#     que histogramas, barras, heatmaps y scatter plots se vean
#     como parte de un mismo sistema visual.

PALETA = {
    # ── Colores principales (estructura visual "rosadita") ───────────
    "primario":    "#FF69B4",   # Hot Pink — color principal de gráficas
    "secundario":  "#C71585",   # Medium Violet Red — énfasis, destacados
    "terciario":   "#FFB6C1",   # Light Pink — fondos suaves, rellenos
    "acento":      "#DB7093",   # Pale Violet Red — complementario
    "oscuro":      "#8B0A50",   # Deep Pink oscuro — títulos y headers

    # ── Colores para niveles de riesgo (semánticos, universales) ─────
    "sin_riesgo":  "#2ECC71",   # Verde esmeralda — cartera sana
    "riesgo_bajo": "#27AE60",   # Verde bosque — alerta mínima
    "riesgo_mod":  "#F1C40F",   # Amarillo dorado — alerta temprana
    "riesgo_alto": "#E67E22",   # Naranja — deterioro visible
    "riesgo_crit": "#E74C3C",   # Rojo — crítico, intervención urgente
    "sin_datos":   "#BDC3C7",   # Gris claro — sin información

    # ── Colores neutros (fondos, bordes, grid) ──────────────────────
    "neutro":      "#7F8C8D",   # Gris medio — líneas, bordes
    "claro":       "#FFF0F5",   # Lavender Blush — fondo de gráficas 🌸
    "borde":       "#F0B4C8",   # Rosa pálido — bordes suaves
    "texto":       "#4A0028",   # Vino oscuro — texto legible
}

# Mapeo directo: nivel de riesgo → color
# Se usa para asignar colores automáticamente en gráficas de barras,
# pie charts, y cualquier visualización que agrupe por riesgo.
RIESGO_COLOR = {
    "sin_riesgo":      PALETA["sin_riesgo"],
    "riesgo_bajo":     PALETA["riesgo_bajo"],
    "riesgo_moderado": PALETA["riesgo_mod"],
    "riesgo_alto":     PALETA["riesgo_alto"],
    "riesgo_critico":  PALETA["riesgo_crit"],
    "sin_datos":       PALETA["sin_datos"],
}


# ══════════════════════════════════════════════════════════════════════════
# 4. CONFIGURACIÓN DE MATPLOTLIB — Estilo "Rosadito" Global
# ══════════════════════════════════════════════════════════════════════════
#
# CONCEPTO: plt.rcParams permite configurar TODAS las gráficas
# desde UN solo lugar. Al importar config.py, todo plot posterior
# hereda estos ajustes automáticamente.

plt.rcParams.update({
    # ── Colores de fondo (tinte rosado sutil) ────────────────────────
    "figure.facecolor":  "#FFFFFF",      # Fondo de figura blanco
    "axes.facecolor":    "#FFF5F7",      # Fondo de ejes: rosa muy tenue 🌸

    # ── Bordes y grid ────────────────────────────────────────────────
    "axes.edgecolor":    "#F0B4C8",      # Bordes rosa suave
    "axes.grid":         True,           # Grid activado
    "grid.color":        "#FCE4EC",      # Grid rosa muy claro
    "grid.linewidth":    0.6,            # Grosor de grid
    "axes.spines.top":   False,          # Sin borde superior (moderno)
    "axes.spines.right": False,          # Sin borde derecho (moderno)

    # ── Tipografía ───────────────────────────────────────────────────
    "font.family":       "sans-serif",   # Fuente moderna
    "font.size":         10,             # Tamaño base

    # ── Títulos y etiquetas ──────────────────────────────────────────
    "axes.titlesize":    12,             # Tamaño de título
    "axes.titleweight":  "bold",         # Negrita
    "axes.titlecolor":   "#8B0A50",      # Títulos en rosa oscuro 🌸
    "axes.labelsize":    10,             # Tamaño de labels
    "axes.labelcolor":   "#4A0028",      # Labels en vino oscuro
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,

    # ── Calidad ──────────────────────────────────────────────────────
    "figure.dpi":        120,            # 120 DPI pantalla
    "savefig.dpi":       300,            # 300 DPI publicación
})


# ══════════════════════════════════════════════════════════════════════════
# 5. RUTAS DE SALIDA
# ══════════════════════════════════════════════════════════════════════════

# Directorio donde se guardarán:
#   - Gráficas (PNG, 300 DPI)
#   - Resultados (JSON, Pickle)
#   - Logs de ejecución

RUTA_SALIDA = Path("outputs")
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
# 6. UMBRALES ESTADÍSTICOS (Basel II/III, Circular 98 Superfinanciera)
# ══════════════════════════════════════════════════════════════════════════

# Umbrales para clasificación de riesgo NPL (Non-Performing Loans)
# Basados en normativa colombiana y estándares internacionales

UMBRALES_RIESGO = {
    "sin_riesgo":    0.00,    # NPL = 0%
    "riesgo_bajo":   0.01,    # NPL < 1%  (cartera sana)
    "riesgo_mod":    0.05,    # NPL < 5%  (alerta temprana)
    "riesgo_alto":   0.15,    # NPL < 15% (deterioro)
    # >= 15% → riesgo_critico
}

# Tamaño mínimo de muestra para tests paramétricos
# (Teorema Central del Límite: n ≥ 30 para aproximación normal)
MUESTRA_MINIMA_PARAMETRICO = 30

# Nivel de significancia por defecto para tests estadísticos
ALPHA_DEFAULT = 0.05


# ══════════════════════════════════════════════════════════════════════════
# 7. CONFIGURACIÓN DE FASTAPI (Semana 3)
# ══════════════════════════════════════════════════════════════════════════

# Metadatos de la API que aparecerán en Swagger UI (/docs)

API_TITULO = "API de Análisis de Riesgo Crediticio"
API_VERSION = "1.0.0"
API_DESCRIPCION = """
## Sistema Financiero Colombiano — Datos Abiertos Gov.co

Esta API REST permite:
  - **Consultar** análisis de riesgo crediticio por municipio
  - **Crear** nuevos análisis con datos validados
  - **Eliminar** análisis guardados
  - **Obtener** estadísticos del sistema financiero

### Autenticación
No requiere autenticación para fines académicos.

### Tecnologías
  - FastAPI (ASGI)
  - Pydantic v2 (validación)
  - Uvicorn (servidor)
"""
API_CONTACTO = {
    "name": "Angela Rico · Sebastian Ramirez",
    "url": "https://github.com/angelaricortega/Python",
}
API_LICENSE = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT",
}
