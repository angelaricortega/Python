"""
validators.py — Validadores auxiliares para la API de Encuestas Poblacionales.

Centraliza las constantes de dominio colombiano y funciones de validación
reutilizables, manteniendo los modelos Pydantic limpios y enfocados.
"""

from typing import List


# ─────────────────────────────────────────────────────────────────────────────
# Catálogo oficial de departamentos de Colombia
# Fuente: DANE - División Político-Administrativa de Colombia (DIVIPOLA)
# ─────────────────────────────────────────────────────────────────────────────

DEPARTAMENTOS_COLOMBIA: List[str] = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar",
    "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca",
    "Cesar", "Chocó", "Córdoba", "Cundinamarca", "Guainía",
    "Guaviare", "Huila", "La Guajira", "Magdalena", "Meta",
    "Nariño", "Norte de Santander", "Putumayo", "Quindío",
    "Risaralda", "San Andrés y Providencia", "Santander",
    "Sucre", "Tolima", "Valle del Cauca", "Vaupés", "Vichada",
    "Bogotá D.C.",
]

# Versión normalizada (sin tildes, lowercase) para comparación robusta
_REEMPLAZOS_TILDES = {
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
    "ü": "u", "ñ": "n", "Á": "a", "É": "e", "Í": "i",
    "Ó": "o", "Ú": "u", "Ñ": "n",
}

_DEPT_NORMALIZADOS: List[str] = []
for _d in DEPARTAMENTOS_COLOMBIA:
    _norm = _d.lower().strip()
    for _tilde, _sin in _REEMPLAZOS_TILDES.items():
        _norm = _norm.replace(_tilde, _sin)
    _DEPT_NORMALIZADOS.append(_norm)


def normalizar_texto(texto: str) -> str:
    """Convierte a minúsculas y elimina tildes para comparación flexible."""
    resultado = texto.lower().strip()
    for tilde, sin_tilde in _REEMPLAZOS_TILDES.items():
        resultado = resultado.replace(tilde, sin_tilde)
    return resultado


def validar_departamento(departamento: str) -> str:
    """
    Valida y normaliza el nombre de un departamento colombiano.

    Aplicado con mode='before' en Pydantic:
      - Acepta variaciones de capitalización: 'ANTIOQUIA', 'antioquia' → 'Antioquia'
      - Acepta variaciones sin tildes: 'Cordoba' → 'Córdoba'
      - Retorna el nombre oficial del catálogo DANE si hay coincidencia
      - Lanza ValueError con mensaje descriptivo si no existe en el catálogo

    Args:
        departamento: Nombre del departamento a validar.

    Returns:
        Nombre oficial del departamento con tildes y capitalización correcta.

    Raises:
        ValueError: Si el departamento no existe en el catálogo DANE.
    """
    if not isinstance(departamento, str):
        raise ValueError("El departamento debe ser una cadena de texto.")

    dept_norm = normalizar_texto(departamento)

    for i, dept_oficial_norm in enumerate(_DEPT_NORMALIZADOS):
        if dept_norm == dept_oficial_norm:
            return DEPARTAMENTOS_COLOMBIA[i]  # Retorna nombre oficial con tildes

    opciones_listadas = ", ".join(DEPARTAMENTOS_COLOMBIA)
    raise ValueError(
        f"'{departamento}' no es un departamento válido de Colombia. "
        f"Departamentos aceptados (catálogo DANE): {opciones_listadas}"
    )


def validar_rango_likert(valor: int) -> int:
    """
    Valida que un valor esté en la escala Likert colombiana estándar (1-5).

    Escala:
        1 = Muy insatisfecho / Totalmente en desacuerdo
        5 = Muy satisfecho / Totalmente de acuerdo

    Args:
        valor: Entero a validar.

    Returns:
        El mismo valor si es válido.

    Raises:
        ValueError: Si el valor no está en el rango 1-5.
    """
    if not isinstance(valor, int) or not (1 <= valor <= 5):
        raise ValueError(
            f"Escala Likert debe ser un entero entre 1 y 5. Recibido: {valor!r}. "
            f"Escala: 1=Muy insatisfecho, 2=Insatisfecho, 3=Neutral, "
            f"4=Satisfecho, 5=Muy satisfecho."
        )
    return valor


def validar_porcentaje(valor: float) -> float:
    """
    Valida que un valor sea un porcentaje estadísticamente válido (0.0 - 100.0).

    Args:
        valor: Número a validar como porcentaje.

    Returns:
        El valor como float si es válido.

    Raises:
        ValueError: Si el valor está fuera del rango 0-100.
    """
    try:
        v = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"El porcentaje debe ser un valor numérico. Recibido: {valor!r}")

    if not (0.0 <= v <= 100.0):
        raise ValueError(
            f"El porcentaje debe estar entre 0.0 y 100.0. "
            f"Recibido: {v}. Un porcentaje no puede ser negativo ni superar el 100%."
        )
    return round(v, 4)
