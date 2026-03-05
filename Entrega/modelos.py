"""
modelos.py — Contratos de Datos con Pydantic v2
================================================
Semana 2: Pydantic como capa de QA automática en la ingesta de datos.

CONCEPTO CLAVE — "Schema First":
  Primero definimos el contrato (qué forma deben tener los datos),
  y Pydantic verifica automáticamente que cada objeto creado cumpla ese contrato.

COMPARACIÓN con tipado normal de Python:
  Sin Pydantic:  x: int = "hola"   → sin error en tiempo de ejecución
  Con Pydantic:  campo: int = "hola" → ValidationError inmediato

POR QUÉ PYDANTIC EN ESTE PROYECTO:
  1. Validación automática de datos sucios de la API
  2. Conversión de tipos (strings con comas → floats)
  3. Documentación viva (los modelos son su propia documentación)
  4. Integración con FastAPI (semanas 3+) — los mismos modelos se usan
     para validar requests y generar documentación Swagger automática

CLASIFICACIÓN REGULATORIA (Circular 100 Superfinanciera):
  A = Normal          → cartera sana (numerador = 0)
  B = En observación  → señal de alerta temprana
  C = Subestándar  ┐
  D = Dudosa       ├─ Cartera en mora (numerador del NPL Ratio)
  E = Pérdida      ┘

  NPL Ratio = (C + D + E) / Total Cartera
"""

# ── Librería estándar ────────────────────────────────────────────────────
from datetime import datetime
from typing import Optional, List, Literal

# ── Terceros ─────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator, ValidationError, model_validator


# ══════════════════════════════════════════════════════════════════════════
# 0. TIPOS PERSONALIZADOS (Type Aliases)
# ══════════════════════════════════════════════════════════════════════════

# Literal: restringe valores a un conjunto específico de strings
# TipoRiesgo solo puede ser uno de estos 6 valores
NivelRiesgo = Literal[
    "sin_riesgo",
    "riesgo_bajo",
    "riesgo_moderado",
    "riesgo_alto",
    "riesgo_critico",
    "sin_datos",
]


# ══════════════════════════════════════════════════════════════════════════
# 1. UTILIDADES INTERNAS (funciones privadas para validación)
# ══════════════════════════════════════════════════════════════════════════

def _parse_numero_flexible(v) -> Optional[float]:
    """
    Convierte valores numéricos (incluyendo strings con formato regional) a float.

    CASOS SOPORTADOS:
      None, "", NaN              → None
      int/float                  → float
      "1500000"                  → 1500000.0
      "1,500,000"                → 1500000.0  (formato US)
      "1.500.000"                → 1500000.0  (formato EU)
      "$ 1.500.000,25"           → 1500000.25 (con símbolo de moneda)
      "1,500,000.25"             → 1500000.25 (formato US con decimales)

    REGLA HEURÍSTICA:
      - Si hay ',' y '.', el último separador se asume decimal.
      - Si hay solo uno:
          * si aparece una sola vez y tiene 1-2 dígitos al final → decimal
          * en otro caso → separador de miles

    POR QUÉ ESTA FUNCIÓN:
      La API de Datos Abiertos puede devolver números en formatos inconsistentes.
      Esta función normaliza TODO a float antes de que Pydantic valide.
    """
    # Missing / NA (incluye np.nan, pd.NA, None)
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    # Numérico puro
    if isinstance(v, (int, float, np.number)):
        out = float(v)
        if not np.isfinite(out):
            return None
        return out

    # String vacío
    s = str(v).strip()
    if s == "":
        return None

    # Limpieza básica (quitar símbolos de moneda, espacios)
    s = (
        s.replace("$", "")
         .replace("COP", "")
         .replace("cop", "")
         .replace(" ", "")
         .replace("\u00A0", "")   # non-breaking space
    )

    # Si no hay separadores, intento directo
    if "," not in s and "." not in s:
        try:
            return float(s)
        except ValueError:
            return None

    # Hay separadores: determinar cuál es decimal
    if "," in s and "." in s:
        # Ambos presentes → el último es decimal
        last_comma = s.rfind(",")
        last_dot = s.rfind(".")
        if last_comma > last_dot:
            # Formato EU: 1.234.567,89
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            # Formato US: 1,234,567.89
            s = s.replace(",", "")
        return float(s)

    # Solo comas
    if "," in s:
        if s.count(",") > 1:
            # Múltiples comas → separador de miles: 1,234,567
            s = s.replace(",", "")
            return float(s)
        # Una sola coma → verificar si es decimal
        left, right = s.split(",", 1)
        if len(right) in (1, 2):  # probable decimal: 12,5 / 12,50
            s = f"{left}.{right}"
        else:                     # probable miles: 1,500
            s = f"{left}{right}"
        return float(s)

    # Solo puntos
    if "." in s:
        if s.count(".") > 1:
            # Múltiples puntos → separador de miles: 1.234.567
            s = s.replace(".", "")
            return float(s)
        # Un solo punto → verificar si es decimal
        left, right = s.split(".", 1)
        if len(right) in (1, 2):  # probable decimal: 12.5 / 12.50
            s = f"{left}.{right}"
        else:                     # probable miles: 1.500
            s = f"{left}{right}"
        return float(s)

    return float(s)


def clasificar_riesgo(obs: dict) -> NivelRiesgo:
    """
    Clasifica el nivel de riesgo a partir de `indice_riesgo`.

    USA PATTERN MATCHING (Python 3.10+):
      match/case es más expresivo que if-elif-else cuando hay múltiples
      condiciones basadas en la estructura o valor de los datos.

    UMBRALES BASADOS EN:
      - Circular 98 Superfinanciera (Colombia)
      - Basel II/III (estándares internacionales)
      - NPL Ratio (Non-Performing Loans)

    CLASIFICACIÓN:
      sin_riesgo     : NPL = 0%      (cartera perfectamente sana)
      riesgo_bajo    : NPL < 1%      (cartera sana, monitoreo routine)
      riesgo_mod     : NPL < 5%      (alerta temprana, revisar)
      riesgo_alto    : NPL < 15%     (deterioro, acción requerida)
      riesgo_critico : NPL >= 15%    (crítico, intervención inmediata)
    """
    # Caso: diccionario vacío o None
    if not obs:
        return "sin_datos"

    # Obtener valor
    idx = obs.get("indice_riesgo")

    # Caso: valor None o NaN
    if idx is None or (isinstance(idx, float) and idx != idx):  # NaN check
        return "sin_datos"

    # Pattern matching para clasificación
    match idx:
        case 0.0:
            return "sin_riesgo"
        case default if default < 0.01:
            return "riesgo_bajo"
        case default if default < 0.05:
            return "riesgo_moderado"
        case default if default < 0.15:
            return "riesgo_alto"
        case _:
            return "riesgo_critico"


# ══════════════════════════════════════════════════════════════════════════
# 2. MODELO BASE — VariableEstadistica
# ══════════════════════════════════════════════════════════════════════════

class VariableEstadistica(BaseModel):
    """
    Modelo de una variable estadística del dataset financiero.

    PROPÓSITO:
      Demostrar validación de tipos, restricciones numéricas y
      validadores personalizados en un modelo simple.

    CONCEPTOS PYDANTIC DEMOSTRADOS:
      - Field(...): campo obligatorio
      - Field(ge=0, le=1): restricciones numéricas (greater or equal, less or equal)
      - field_validator(mode="before"): limpiar datos ANTES de validar
      - field_validator(mode="after"): validar/advertir DESPUÉS de validar
      - validate_assignment: validar también al asignar atributos (no solo al crear)
    """

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="Nombre de la variable en el dataset",
    )

    desviacion_std: float = Field(
        ...,
        gt=0,  # greater than (estrictamente positivo)
        description="Desviación estándar — debe ser estrictamente positiva",
    )

    probabilidad: float = Field(
        ...,
        ge=0,  # greater or equal
        le=1,  # less or equal
        description="Probabilidad perteneciente a [0, 1]",
    )

    unidad: str = Field(
        default="COP",
        description="Unidad de medida (pesos colombianos por defecto)",
    )

    valor_maximo: Optional[float] = Field(
        default=None,
        ge=0,
        description="Valor máximo observado (None si no disponible)",
    )

    # Config: validar también al asignar (no solo al crear el objeto)
    model_config = {
        "validate_assignment": True,
    }

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, v) -> str:
        """
        mode="before": se ejecuta ANTES de validar el tipo.
        Limpia el string antes de que Pydantic verifique que es str.
        """
        return str(v).strip().title() if v else ""

    @field_validator("probabilidad", mode="after")
    @classmethod
    def advertir_probabilidad_extrema(cls, v: float) -> float:
        """
        mode="after": se ejecuta DESPUÉS de validar el tipo.
        Útil para advertencias, no para bloquear (retorna el mismo valor).
        """
        if v in (0.0, 1.0):
            print(f"    ⚠ Probabilidad exacta {v} — verificar si es correcta")
        return v


# ══════════════════════════════════════════════════════════════════════════
# 3. MODELO PRINCIPAL — MunicipioFinanciero
# ══════════════════════════════════════════════════════════════════════════

class MunicipioFinanciero(BaseModel):
    """
    Contrato Pydantic para registros del sistema financiero colombiano.

    CAMPOS:
      municipio        : nombre del municipio (string, obligatorio)
      cartera_a        : categoría A (normal) en COP
      cartera_b        : categoría B (observación) en COP
      cartera_c        : categoría C (subestándar) en COP
      cartera_d        : categoría D (dudosa) en COP
      cartera_e        : categoría E (pérdida) en COP
      total_cartera    : cartera total en COP
      total_captaciones: captaciones totales en COP

    INDICADORES DERIVADOS (calculados):
      indice_riesgo    : (C+D+E) / total_cartera  [0, 1]
      ratio_liquidez   : total_captaciones / total_cartera [0, ∞)
      nivel_riesgo     : clasificación por umbrales (Literal)

    POR QUÉ Optional[]:
      La API puede devolver campos faltantes. Optional[float] permite
      que el campo sea float O None, sin lanzar ValidationError.
    """

    # Campo obligatorio: nombre del municipio
    municipio: str = Field(
        ...,
        min_length=2,
        description="Nombre del municipio",
    )

    # Campos de cartera (opcionales, pueden ser None si la API no los devuelve)
    cartera_a: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera normal (COP) — categoría A",
    )
    cartera_b: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera en observación (COP) — categoría B",
    )
    cartera_c: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera subestándar (COP) — categoría C",
    )
    cartera_d: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera dudosa (COP) — categoría D",
    )
    cartera_e: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera pérdida (COP) — categoría E",
    )
    total_cartera: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cartera total del municipio (COP)",
    )
    total_captaciones: Optional[float] = Field(
        default=None,
        ge=0,
        description="Captaciones totales del municipio (COP)",
    )

    # Indicadores derivados (calculados externamente o con calcular_indicadores())
    indice_riesgo: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Índice de riesgo NPL = (C+D+E) / total_cartera",
    )
    ratio_liquidez: Optional[float] = Field(
        default=None,
        ge=0,
        description="Ratio de liquidez = captaciones / cartera",
    )
    nivel_riesgo: Optional[NivelRiesgo] = Field(
        default=None,
        description="Nivel de riesgo clasificado por umbrales",
    )

    # Config: validar también al asignar
    model_config = {
        "validate_assignment": True,
    }

    @field_validator("municipio", mode="before")
    @classmethod
    def normalizar_municipio(cls, v) -> str:
        """
        Limpia nombre de municipio:
          "  BOGOTÁ D.C.  " → "Bogotá D.C."
        """
        return str(v).strip().title() if v else "Desconocido"

    @field_validator(
        "cartera_a", "cartera_b", "cartera_c", "cartera_d", "cartera_e",
        "total_cartera", "total_captaciones",
        mode="before",
    )
    @classmethod
    def limpiar_numeros(cls, v) -> Optional[float]:
        """
        Coerción robusta de strings con formato regional a float.
        Se ejecuta ANTES de validar el tipo (mode="before").

        Ejemplos:
          "1,500,000"    → 1500000.0
          "1.500.000"    → 1500000.0
          "$1.500.000,50" → 1500000.50
        """
        return _parse_numero_flexible(v)

    def calcular_indicadores(self) -> "MunicipioFinanciero":
        """
        Calcula indicadores derivados:
          - indice_riesgo = (C + D + E) / total_cartera
          - ratio_liquidez = total_captaciones / total_cartera
          - nivel_riesgo = clasificación por umbrales

        RETORNA self para encadenamiento (fluent interface):
          muni = MunicipioFinanciero(...).calcular_indicadores()

        POR QUÉ self:
          Permite crear el objeto y calcular indicadores en una línea.
          También permite validar que los indicadores calculados cumplen
          las restricciones de Pydantic inmediatamente.
        """
        # Sumar cartera en mora (C + D + E)
        mora = sum(
            x for x in [self.cartera_c, self.cartera_d, self.cartera_e]
            if x is not None
        )

        # Calcular índice de riesgo
        if self.total_cartera is not None and self.total_cartera > 0:
            self.indice_riesgo = mora / self.total_cartera

            # Calcular ratio de liquidez
            if self.total_captaciones is not None:
                self.ratio_liquidez = self.total_captaciones / self.total_cartera
            else:
                self.ratio_liquidez = None
        else:
            self.indice_riesgo = None
            self.ratio_liquidez = None

        # Clasificar nivel de riesgo
        self.nivel_riesgo = clasificar_riesgo({"indice_riesgo": self.indice_riesgo})

        return self


# ══════════════════════════════════════════════════════════════════════════
# 4. MODELO DE SALIDA — ResultadoAnalisis
# ══════════════════════════════════════════════════════════════════════════

class ResultadoAnalisis(BaseModel):
    """
    Encapsula el resultado completo del pipeline para exportación.

    PROPÓSITO:
      Serializar todo el análisis a JSON para:
        - Enviar a una API (FastAPI)
        - Guardar en archivo para reproducibilidad
        - Compartir con otros analistas

    CAMPOS:
      fecha_analisis           : timestamp automático (datetime)
      version                  : versión del pipeline (semántica)
      n_municipios             : cantidad de municipios válidos
      cartera_total_billones   : suma de cartera total (en billones COP)
      indice_riesgo_promedio   : promedio del índice de riesgo
      pct_sin_riesgo           : porcentaje de municipios sin riesgo
      municipios               : lista de MunicipiosFinancieros validados
    """

    fecha_analisis: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de cuando se ejecutó el análisis",
    )

    version: str = Field(
        default="1.0.0",
        description="Versión del pipeline (semántica: mayor.menor.parche)",
    )

    n_municipios: int = Field(
        ...,
        ge=0,
        description="Cantidad de municipios válidos analizados",
    )

    cartera_total_billones: float = Field(
        ...,
        ge=0,
        description="Cartera total del sistema (en billones de COP)",
    )

    indice_riesgo_promedio: float = Field(
        ...,
        ge=0,
        le=1,
        description="Índice de riesgo promedio (NPL Ratio)",
    )

    pct_sin_riesgo: float = Field(
        ...,
        ge=0,
        le=100,
        description="Porcentaje de municipios sin riesgo (NPL=0%)",
    )

    municipios: List[MunicipioFinanciero] = Field(
        default_factory=list,
        description="Lista de municipios con sus indicadores",
    )

    # Config: permitir tipos arbitrarios (datetime)
    model_config = {
        "arbitrary_types_allowed": True,
    }


# ══════════════════════════════════════════════════════════════════════════
# 5. OOP — HERENCIA Y POLIMORFISMO
# ══════════════════════════════════════════════════════════════════════════
#
# CONCEPTO APLICADO — Semana 2 (Clases):
#   La clase base AnalizadorEstadistico define la interfaz común.
#   Las clases hijas (Poblacional, Muestral) SOBREESCRIBEN el método
#   calcular_varianza() para cambiar el ddof (degrees of freedom).
#
# HERENCIA:
#   Las clases hijas heredan TODOS los métodos de la base
#   (calcular_media, calcular_mediana, resumen) sin re-escribirlos.
#
# POLIMORFISMO:
#   El MISMO método calcular_varianza() se comporta DIFERENTE
#   según la subclase que lo invoque:
#     - Poblacional: ddof=0 → divide entre N
#     - Muestral:    ddof=1 → divide entre N-1 (corrección de Bessel)
#
# ANALOGÍA CON CLASE (Semana II):
#   Igual que el ejemplo Moneda/Coin pero aplicado a estadística:
#   Moneda.__init__(valor)  →  AnalizadorEstadistico.__init__(datos)
#   Moneda.lanzar()         →  AnalizadorEstadistico.calcular_varianza()
#
# POR QUÉ ddof=1 EN MUESTRAS:
#   Al estimar la varianza de una POBLACIÓN a partir de una MUESTRA,
#   la muestra tiende a subestimar la varianza real.
#   La corrección de Bessel (N-1) corrige este sesgo.
#   Esto es FUNDAMENTAL en inferencia estadística.


class AnalizadorEstadistico:
    """
    CLASE BASE para análisis estadístico de datos financieros.

    CONCEPTO OOP — Clase base (Semana 2):
      Define atributos y métodos comunes que serán HEREDADOS
      por las subclases. No se instancia directamente.

    ATRIBUTOS (definidos en __init__):
      nombre : str          — nombre del análisis
      datos  : np.ndarray   — array de datos numéricos
      n      : int          — cantidad de observaciones

    MÉTODOS HEREDADOS (sin re-escribir en subclases):
      calcular_media()     → promedio aritmético
      calcular_mediana()   → valor central
      calcular_std()       → desviación estándar
      resumen()            → dict con todos los estadísticos

    MÉTODO POLIMÓRFICO (se sobreescribe en subclases):
      calcular_varianza()  → varianza (cambia ddof según subclase)
    """

    # ── Atributo de CLASE (compartido por todas las instancias) ──────
    tipo_analisis: str = "base"

    def __init__(self, nombre: str, datos: list | np.ndarray):
        """
        CONSTRUCTOR (__init__): se ejecuta al crear la instancia.

        CONCEPTO OOP — Constructor (Semana 2):
          El constructor inicializa el ESTADO del objeto.
          self.nombre y self.datos son atributos de INSTANCIA
          (cada objeto tiene su propia copia, a diferencia de
          tipo_analisis que es atributo de CLASE).

        Args:
            nombre: nombre descriptivo del análisis
            datos: lista o array de valores numéricos
        """
        self.nombre = nombre
        self.datos = np.array(datos, dtype=float)
        self.n = len(self.datos)

    def calcular_media(self) -> float:
        """Promedio aritmético: sum(x) / n."""
        return round(float(np.mean(self.datos)), 4)

    def calcular_mediana(self) -> float:
        """Valor central: P50 (robusto a outliers)."""
        return round(float(np.median(self.datos)), 4)

    def calcular_varianza(self) -> float:
        """
        MÉTODO POLIMÓRFICO — será sobreescrito por subclases.

        POLIMORFISMO (Semana 2):
          Este método tiene la MISMA FIRMA en la clase base
          y en las subclases, pero el COMPORTAMIENTO cambia:
            - AnalizadorPoblacional: ddof=0 (divide entre N)
            - AnalizadorMuestral:    ddof=1 (divide entre N-1)

          Esto permite que el código que usa AnalizadorEstadistico
          funcione con CUALQUIER subclase sin modificarse.
        """
        # Implementación base: ddof=0 por defecto
        return round(float(np.var(self.datos, ddof=0)), 4)

    def calcular_std(self) -> float:
        """Desviación estándar: sqrt(varianza)."""
        return round(float(np.sqrt(self.calcular_varianza())), 4)

    def calcular_cv(self) -> float:
        """Coeficiente de variación: (std / media) × 100."""
        media = self.calcular_media()
        if media == 0:
            return 0.0
        return round(float((self.calcular_std() / abs(media)) * 100), 4)

    def resumen(self) -> dict:
        """
        Genera resumen completo de estadísticos.

        CONCEPTO OOP — Método (Semana 2):
          Este método usa otros métodos del mismo objeto (self).
          Gracias al polimorfismo, calcular_varianza() y calcular_std()
          retornan valores diferentes según la subclase.
        """
        return {
            "nombre": self.nombre,
            "tipo": self.tipo_analisis,
            "n": self.n,
            "media": self.calcular_media(),
            "mediana": self.calcular_mediana(),
            "varianza": self.calcular_varianza(),
            "std": self.calcular_std(),
            "cv_pct": self.calcular_cv(),
            "minimo": round(float(np.min(self.datos)), 4),
            "maximo": round(float(np.max(self.datos)), 4),
        }


class AnalizadorPoblacional(AnalizadorEstadistico):
    """
    Análisis estadístico para POBLACIÓN completa (ddof=0).

    CONCEPTO OOP — Herencia (Semana 2):
      Esta clase HEREDA todo de AnalizadorEstadistico.
      Solo sobreescribe calcular_varianza() para usar ddof=0.

    CUÁNDO USAR:
      Cuando se tiene la TOTALIDAD de los datos (censo completo).
      Ejemplo: TODOS los municipios de Colombia, no una muestra.

    FÓRMULA:
      σ² = Σ(xᵢ - μ)² / N
    """

    # Atributo de clase sobreescrito
    tipo_analisis: str = "poblacional"

    def calcular_varianza(self) -> float:
        """
        Varianza POBLACIONAL: divide entre N (ddof=0).

        POLIMORFISMO EN ACCIÓN:
          Misma firma que la clase base, pero ddof=0.
          Si se llama resumen(), usará ESTA versión.
        """
        return round(float(np.var(self.datos, ddof=0)), 4)


class AnalizadorMuestral(AnalizadorEstadistico):
    """
    Análisis estadístico para MUESTRA (ddof=1, corrección de Bessel).

    CONCEPTO OOP — Herencia + Polimorfismo (Semana 2):
      Esta clase HEREDA todo de AnalizadorEstadistico.
      Solo sobreescribe calcular_varianza() para usar ddof=1.

    CUÁNDO USAR:
      Cuando se tiene una MUESTRA de la población.
      Ejemplo: 500 municipios de ~1,100 totales.

    FÓRMULA:
      s² = Σ(xᵢ - x̄)² / (N - 1)

    POR QUÉ ddof=1 (Corrección de Bessel):
      La muestra tiende a subestimar la varianza de la población.
      Dividir entre N-1 en vez de N corrige ese sesgo.
      Es la práctica estándar en inferencia estadística.
    """

    # Atributo de clase sobreescrito
    tipo_analisis: str = "muestral"

    def calcular_varianza(self) -> float:
        """
        Varianza MUESTRAL: divide entre N-1 (ddof=1).

        POLIMORFISMO EN ACCIÓN:
          Misma firma que la clase base, pero ddof=1.
          Si se llama resumen(), usará ESTA versión.
        """
        return round(float(np.var(self.datos, ddof=1)), 4)


# ══════════════════════════════════════════════════════════════════════════
# 6. INTEGRACIÓN CON PANDAS
# ══════════════════════════════════════════════════════════════════════════

def validar_dataframe(
    df: pd.DataFrame,
    calcular_kpis: bool = True,
) -> tuple[list[MunicipioFinanciero], list[dict]]:
    """
    Valida un DataFrame fila por fila usando MunicipioFinanciero.

    PATRÓN DE VALIDACIÓN:
      1. Renombrar columnas del DataFrame al nombre esperado por Pydantic
      2. Iterar fila por fila convirtiendo a dict con fila.to_dict()
      3. Capturar ValidationError por separado para no abortar por 1 fila
      4. Retornar (válidos, errores) para que quien llama decida qué hacer

    POR QUÉ NO ABORTAR:
      En análisis de datos reales, es común tener algunos registros
      corruptos. Mejor procesar el 99% válido y reportar el 1% error,
      que abortar todo el pipeline por un typo.

    Args:
        df: DataFrame con columnas del sistema financiero
        calcular_kpis: si True, ejecuta .calcular_indicadores() por cada fila válida

    Returns:
        (lista de modelos válidos, lista de dicts con errores)
    """
    # Mapeo de columnas: nombre API → nombre Pydantic
    mapeo = {
        "nombre_municipio":      "municipio",
        "cartera_categoria_a":   "cartera_a",
        "cartera_categoria_b":   "cartera_b",
        "cartera_categoria_c":   "cartera_c",
        "cartera_categoria_d":   "cartera_d",
        "cartera_categoria_e":   "cartera_e",
        "total_cartera":         "total_cartera",
        "total_captaciones":     "total_captaciones",
    }

    # Renombrar columnas que existan en el DataFrame
    df_r = df.rename(columns={k: v for k, v in mapeo.items() if k in df.columns})

    validos: list[MunicipioFinanciero] = []
    errores: list[dict] = []

    for idx, fila in df_r.iterrows():
        try:
            # Convertir fila a dict y crear modelo Pydantic
            registro = MunicipioFinanciero(**fila.to_dict())

            # Calcular indicadores si se solicita
            if calcular_kpis:
                registro.calcular_indicadores()

            validos.append(registro)

        except ValidationError as e:
            # Capturar error para reporte (no abortar)
            errores.append({
                "fila_idx": int(idx) if isinstance(idx, (int, np.integer)) else idx,
                "municipio": fila.get("municipio", "?"),
                "errores": e.errors(),
            })

    return validos, errores


# ══════════════════════════════════════════════════════════════════════════
# DEMO — Ejecutar con: python modelos.py
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  DEMO — modelos.py")
    print("  Semana 2: Validación con Pydantic v2")
    print("=" * 65)

    # ── 1. VariableEstadistica: tipos de campos ──────────────────────────
    print("\n1. VariableEstadistica — campo válido con normalización:")
    v1 = VariableEstadistica(
        nombre="  índice de mora  ",
        desviacion_std=0.015,
        probabilidad=0.27,
        valor_maximo=0.85,
    )
    print(f"   nombre          : {v1.nombre}")
    print(f"   desviacion_std  : {v1.desviacion_std}")
    print(f"   probabilidad    : {v1.probabilidad}")
    print(f"   unidad (default): {v1.unidad}")
    print(f"   valor_maximo    : {v1.valor_maximo}")

    print("\n2. VariableEstadistica — desviación negativa (error esperado):")
    try:
        VariableEstadistica(nombre="mora", desviacion_std=-0.5, probabilidad=0.3)
    except ValidationError as e:
        print(f"   ValidationError en campo '{e.errors()[0]['loc'][0]}':")
        print(f"   → {e.errors()[0]['msg']}")

    print("\n3. VariableEstadistica — probabilidad exacta 1.0 (advertencia):")
    v3 = VariableEstadistica(nombre="mora total", desviacion_std=0.1, probabilidad=1.0)
    print(f"   Objeto creado: probabilidad={v3.probabilidad} (advertencia emitida arriba)")

    # ── 2. MunicipioFinanciero: datos sucios de API ──────────────────────
    print("\n4. MunicipioFinanciero — datos sucios (strings con separadores):")
    muni = MunicipioFinanciero(
        municipio="  bogotá d.c.  ",
        cartera_a="1,500,000,000",
        cartera_c="50.000.000",
        cartera_d="25.000.000",
        cartera_e="10.000.000",
        total_cartera="1,600,000,000",
        total_captaciones="2.000.000.000",
    ).calcular_indicadores()
    print(f"   municipio       : {muni.municipio}")
    print(f"   cartera_a       : {muni.cartera_a:,.0f} COP")
    print(f"   total_cartera   : {muni.total_cartera:,.0f} COP")
    print(f"   indice_riesgo   : {muni.indice_riesgo:.4%}")
    print(f"   ratio_liquidez  : {muni.ratio_liquidez:.3f}")
    print(f"   nivel_riesgo    : {muni.nivel_riesgo}")

    print("\n5. MunicipioFinanciero — valor inválido (string no numérico):")
    try:
        MunicipioFinanciero(municipio="Cali", total_cartera="error_tipeo")
    except ValidationError as e:
        print(f"   ValidationError: {e.errors()[0]['msg']}")

    # ── 3. Integración con Pandas ────────────────────────────────────────
    print("\n6. validar_dataframe() — 3 filas (1 válida, 1 coercible, 1 error):")
    df_test = pd.DataFrame([
        # válida
        {"municipio": "Medellín", "total_cartera": "500000000",
         "total_captaciones": "800000000"},
        # coercible (separadores)
        {"municipio": "Cali", "total_cartera": "1,200,000,000",
         "total_captaciones": "600.000.000"},
        # error (texto)
        {"municipio": "Bogotá", "total_cartera": "texto_invalido",
         "total_captaciones": "200000000"},
    ])
    validos, errores = validar_dataframe(df_test)
    print(f"   Válidos : {len(validos)}")
    print(f"   Errores : {len(errores)}")
    for err in errores:
        print(f"   ✗ '{err['municipio']}': {err['errores'][0]['msg']}")

    # ── 4. Serialización JSON con Pydantic ───────────────────────────────
    print("\n7. model_dump_json() — serialización con datetime:")
    resultado = ResultadoAnalisis(
        n_municipios=len(validos),
        cartera_total_billones=0.5,
        indice_riesgo_promedio=0.02,
        pct_sin_riesgo=66.7,
        municipios=validos,
    )
    json_str = resultado.model_dump_json(indent=2)
    print(f"   fecha_analisis en JSON: {resultado.fecha_analisis.isoformat()}")
    print(f"   Extracto JSON (100 chars): {json_str[:100]}…")

    # ── 5. model_dump() → dict Python ───────────────────────────────────
    print("\n8. model_dump() → dict Python:")
    d = muni.model_dump()
    print(f"   Campos: {list(d.keys())}")

    print("\n✅ Demo completada.")
