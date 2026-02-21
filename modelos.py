"""
modelos.py — Contratos de Datos con Pydantic v2
================================================
Semana 2: Pydantic como capa de QA automática en la ingesta de datos.

Pydantic implementa el patrón "Schema First": primero definimos el contrato
(qué forma deben tener los datos), y Pydantic verifica automáticamente
que cada objeto creado cumpla ese contrato.

Comparación con tipado normal de Python:
  Sin Pydantic: x: int = "hola"   → sin error en tiempo de ejecución
  Con Pydantic: campo: int = "hola" → ValidationError inmediato

Este módulo se diseña para ser reutilizable:
  - analisis.py lo importa para validar registros de la API
  - FastAPI (semanas 3+) lo importará para definir schemas de endpoints
    sin ninguna modificación (ventaja de modularizar desde el inicio)
"""

# ── Librería estándar ────────────────────────────────────────────────────
from datetime import datetime
from typing import Optional, List, Literal

# ── Terceros ─────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator, ValidationError


# ══════════════════════════════════════════════════════════════════════════
# 0. UTILIDADES INTERNAS
#    Funciones privadas para normalizar datos antes de Pydantic.
# ══════════════════════════════════════════════════════════════════════════

NivelRiesgo = Literal[
    "sin_riesgo", "riesgo_bajo", "riesgo_moderado",
    "riesgo_alto", "riesgo_critico", "sin_datos",
]


def _parse_numero_flexible(v) -> Optional[float]:
    """
    Convierte valores numéricos (incluyendo strings con formato regional) a float.

    Casos soportados:
      None, "", NaN                 -> None
      int/float                     -> float
      "1500000"                     -> 1500000.0
      "1,500,000"                   -> 1500000.0
      "1.500.000"                   -> 1500000.0
      "$ 1.500.000,25"              -> 1500000.25
      "1,500,000.25"                -> 1500000.25

    Regla heurística:
      - Si hay ',' y '.', el último separador se asume decimal.
      - Si hay solo uno:
          * si aparece una sola vez y tiene 1-2 dígitos al final -> decimal
          * en otro caso -> separador de miles
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

    s = str(v).strip()
    if s == "":
        return None

    # Limpieza básica
    s = (
        s.replace("$", "")
         .replace("COP", "")
         .replace("cop", "")
         .replace(" ", "")
         .replace("\u00A0", "")   # non-breaking space
    )

    # Si no hay separadores, intento directo
    if "," not in s and "." not in s:
        return float(s)

    # Hay ambos separadores -> el último se interpreta como decimal
    if "," in s and "." in s:
        last_comma = s.rfind(",")
        last_dot = s.rfind(".")
        if last_comma > last_dot:
            # Formato tipo 1.234.567,89
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            # Formato tipo 1,234,567.89
            s = s.replace(",", "")
        return float(s)

    # Solo comas
    if "," in s:
        if s.count(",") > 1:
            # miles: 1,234,567
            s = s.replace(",", "")
            return float(s)

        left, right = s.split(",", 1)
        if len(right) in (1, 2):  # probable decimal: 12,5 / 12,50
            s = f"{left}.{right}"
        else:                     # probable miles: 1,500
            s = f"{left}{right}"
        return float(s)

    # Solo puntos
    if "." in s:
        if s.count(".") > 1:
            # miles: 1.234.567
            s = s.replace(".", "")
            return float(s)

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
    Usa match/case (Python 3.10+).

    Umbrales basados en Circular 98 Superfinanciera y Basel II/III:
      - sin_riesgo    : NPL = 0%
      - riesgo_bajo   : NPL < 1%   (cartera sana)
      - riesgo_mod    : NPL < 5%   (alerta temprana)
      - riesgo_alto   : NPL < 15%  (deterioro)
      - riesgo_crit   : NPL >= 15% (crítico)
    """
    # Caso especial: diccionario vacío
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
# 1. MODELO BASE — VariableEstadistica
# ══════════════════════════════════════════════════════════════════════════

class VariableEstadistica(BaseModel):
    """
    Modelo de una variable estadística del dataset financiero.
    """

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="Nombre de la variable en el dataset",
    )

    desviacion_std: float = Field(
        ...,
        gt=0,
        description="Desviación estándar — debe ser estrictamente positiva",
    )

    probabilidad: float = Field(
        ...,
        ge=0,
        le=1,
        description="Probabilidad perteneciente a [0, 1]",
    )

    unidad: str = Field(default="COP", description="Unidad de medida")

    valor_maximo: Optional[float] = Field(
        default=None,
        ge=0,
        description="Valor máximo observado (None si no disponible)",
    )

    model_config = {
        "validate_assignment": True,
    }

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, v) -> str:
        return str(v).strip().title() if v else ""

    @field_validator("probabilidad", mode="after")
    @classmethod
    def advertir_probabilidad_extrema(cls, v: float) -> float:
        if v in (0.0, 1.0):
            print(f"    ⚠ Probabilidad exacta {v} — verificar si es correcta")
        return v


# ══════════════════════════════════════════════════════════════════════════
# 2. MODELO PRINCIPAL — MunicipioFinanciero
# ══════════════════════════════════════════════════════════════════════════

class MunicipioFinanciero(BaseModel):
    """
    Contrato Pydantic para registros del sistema financiero colombiano.

    Clasificación regulatoria Superfinanciera (Circular 100):
      A = Normal          → cartera sana
      B = En observación  → señal de alerta temprana
      C = Subestándar  ┐
      D = Dudosa       ├─ Cartera en mora (numerador del NPL Ratio)
      E = Pérdida      ┘
    """

    municipio: str = Field(..., min_length=2)

    cartera_a: Optional[float] = Field(None, ge=0, description="Cartera normal (COP)")
    cartera_b: Optional[float] = Field(None, ge=0, description="Cartera observación (COP)")
    cartera_c: Optional[float] = Field(None, ge=0, description="Cartera subestándar (COP)")
    cartera_d: Optional[float] = Field(None, ge=0, description="Cartera dudosa (COP)")
    cartera_e: Optional[float] = Field(None, ge=0, description="Cartera pérdida (COP)")
    total_cartera: Optional[float] = Field(None, ge=0)
    total_captaciones: Optional[float] = Field(None, ge=0)

    # Indicadores derivados — calculados externamente o con calcular_indicadores()
    indice_riesgo: Optional[float] = Field(None, ge=0, le=1)
    ratio_liquidez: Optional[float] = Field(None, ge=0)
    nivel_riesgo: Optional[NivelRiesgo] = None

    model_config = {
        "validate_assignment": True,
    }

    @field_validator("municipio", mode="before")
    @classmethod
    def normalizar_municipio(cls, v) -> str:
        """
        Title Case y strip para nombres de municipio.
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
        """
        return _parse_numero_flexible(v)

    def calcular_indicadores(self) -> "MunicipioFinanciero":
        """
        Calcula indicadores derivados:
          - indice_riesgo = (C + D + E) / total_cartera
          - ratio_liquidez = total_captaciones / total_cartera
          - nivel_riesgo = clasificación por umbrales

        Retorna self para encadenamiento.
        """
        mora = sum(
            x for x in [self.cartera_c, self.cartera_d, self.cartera_e]
            if x is not None
        )

        if self.total_cartera is not None and self.total_cartera > 0:
            self.indice_riesgo = mora / self.total_cartera
            if self.total_captaciones is not None:
                self.ratio_liquidez = self.total_captaciones / self.total_cartera
        else:
            self.indice_riesgo = None
            self.ratio_liquidez = None

        self.nivel_riesgo = clasificar_riesgo({"indice_riesgo": self.indice_riesgo})
        return self


# ══════════════════════════════════════════════════════════════════════════
# 3. MODELO DE SALIDA — ResultadoAnalisis
# ══════════════════════════════════════════════════════════════════════════

class ResultadoAnalisis(BaseModel):
    """
    Encapsula el resultado completo del pipeline para exportación.
    """
    fecha_analisis: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    n_municipios: int = Field(..., ge=0)
    cartera_total_billones: float
    indice_riesgo_promedio: float = Field(..., ge=0, le=1)
    pct_sin_riesgo: float = Field(..., ge=0, le=100)
    municipios: List[MunicipioFinanciero] = Field(default_factory=list)

    model_config = {
        "arbitrary_types_allowed": True,
    }


# ══════════════════════════════════════════════════════════════════════════
# 4. INTEGRACIÓN CON PANDAS
# ══════════════════════════════════════════════════════════════════════════

def validar_dataframe(
    df: pd.DataFrame,
    calcular_kpis: bool = True,
) -> tuple[list[MunicipioFinanciero], list[dict]]:
    """
    Valida un DataFrame fila por fila usando MunicipioFinanciero.

    Patrón:
      1. Renombrar columnas del DataFrame al nombre esperado por Pydantic
      2. Iterar fila por fila convirtiendo a dict con fila.to_dict()
      3. Capturar ValidationError por separado para no abortar por 1 fila
      4. Retornar (válidos, errores) para que quien llama decida qué hacer

    Args:
        df: DataFrame con columnas del sistema financiero
        calcular_kpis: si True, ejecuta .calcular_indicadores() por cada fila válida

    Returns:
        (lista de modelos válidos, lista de dicts con errores)
    """
    mapeo = {
        "nombre_municipio": "municipio",
        "cartera_categoria_a": "cartera_a",
        "cartera_categoria_b": "cartera_b",
        "cartera_categoria_c": "cartera_c",
        "cartera_categoria_d": "cartera_d",
        "cartera_categoria_e": "cartera_e",
        "total_cartera": "total_cartera",
        "total_captaciones": "total_captaciones",
    }

    df_r = df.rename(columns={k: v for k, v in mapeo.items() if k in df.columns})

    validos: list[MunicipioFinanciero] = []
    errores: list[dict] = []

    for idx, fila in df_r.iterrows():
        try:
            registro = MunicipioFinanciero(**fila.to_dict())
            if calcular_kpis:
                registro.calcular_indicadores()
            validos.append(registro)

        except ValidationError as e:
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
    print("=" * 58)
    print("  DEMO — modelos.py")
    print("  Semana 2: Validación con Pydantic v2")
    print("=" * 58)

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

    # ── 5. model_dump() → dict ───────────────────────────────────────────
    print("\n8. model_dump() → dict Python:")
    d = muni.model_dump()
    print(f"   Campos: {list(d.keys())}")

    print("\n✅  Demo completada.")