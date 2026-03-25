"""
Diccionario de códigos del Censo 2018 Colombia - Tabla Individual
Fuente: DANE - Documentación Censo Nacional de Población y Vivienda 2018

Este archivo centraliza los catálogos oficiales para validación de datos censales.
"""

# Sexo (P_SEXO)
SEXO = {
    1: "Hombre",
    2: "Mujer"
}

# Pertenencia étnica (PA1_GRP_ETNIC)
GRUPO_ETNICO = {
    1: "Indígena",
    2: "Raizal de San Andrés y Providencia",
    3: "Palenquero de San Basilio",
    4: "Negro(a), Mulato(a), Afrocolombiano(a)",
    5: "Ninguno de los anteriores",  # No étnico
    6: "Indígena",  # Puede haber duplicación en codificación
    9: "Ignorado"
}

# Estado civil (P_EST_CIVIL) - para mayores de 12 años
ESTADO_CIVIL = {
    1: "Soltero(a)",
    2: "Casado(a)",
    3: "Unido(a)",
    4: "Separado(a)",
    5: "Divorciado(a)",
    6: "Viudo(a)",
    7: "Soltero(a) - menor 12 años",
    9: "Ignorado"
}

# Trabajó la semana pasada (P_TRABAJO) - para mayores de 5 años
TRABAJO = {
    0: "Menor de 5 años (no pregunta)",
    1: "Sí trabajó",
    2: "No trabajó, tenía empleo",
    3: "No trabajó, buscó empleo",
    4: "No trabajó, quehaceres del hogar",
    5: "No trabajó, estudiaba",
    6: "No trabajó, jubilado/pensionado",
    7: "No trabajó, otra razón",
    8: "No trabajó, sin especificar",
    9: "Ignorado"
}

# Sabe leer y escribir (P_ALFABETA) - para mayores de 5 años
ALFABETA = {
    1: "Sí sabe",
    2: "No sabe",
    9: "Ignorado"
}

# Asistencia educativa (PA_ASISTENCIA) - para mayores de 5 años
ASISTENCIA = {
    1: "Sí asiste",
    2: "No asiste",
    9: "Ignorado"
}

# Enfermedad crónica (P_ENFERMO)
ENFERMO = {
    1: "Sí tiene",
    2: "No tiene",
    9: "Ignorado"
}

# Nivel educativo (P_NIVEL_ANOSR) - años aprobados
NIVEL_EDUCATIVO_ANOS = {
    0: "Ninguno",
    1: "Primero",
    2: "Segundo",
    3: "Tercero",
    4: "Cuarto",
    5: "Quinto",
    6: "Sexto",
    7: "Séptimo",
    8: "Octavo",
    9: "Noveno",
    10: "Décimo",
    11: "Once",
    99: "Ignorado"
}

# Tipo de registro (TIPO_REG)
TIPO_REG = {
    1: "Vivienda",
    2: "Hogar",
    5: "Persona"
}

# Departamentos de Colombia (U_DPTO) - códigos DANE
DEPARTAMENTOS_DANE = {
    1: "Amazonas",
    2: "Antioquia",
    3: "Arauca",
    4: "Atlántico",
    5: "Bolívar",
    6: "Boyacá",
    7: "Caldas",
    8: "Caquetá",
    9: "Casanare",
    10: "Cauca",
    11: "Cesar",
    12: "Chocó",
    13: "Córdoba",
    14: "Cundinamarca",
    15: "Guainía",
    16: "Guaviare",
    17: "Huila",
    18: "La Guajira",
    19: "Magdalena",
    20: "Meta",
    21: "Nariño",
    22: "Norte de Santander",
    23: "Putumayo",
    24: "Quindío",
    25: "Risaralda",
    26: "San Andrés y Providencia",
    27: "Santander",
    28: "Sucre",
    29: "Tolima",
    30: "Valle del Cauca",
    31: "Vaupés",
    32: "Vichada",
    11001: "Bogotá D.C."  # Código especial
}

# ══════════════════════════════════════════════════════════════════════════════
# TRANSFORMACIÓN DE EDAD - RANGOS ESTÁRIOS A VALOR NUMÉRICO
# ══════════════════════════════════════════════════════════════════════════════

# Rango etario del Censo 2018 (P_EDADR)
RANGOS_EDAD_DANE = {
    1: {"rango": "00-04", "min": 0, "max": 4, "punto_medio": 2},
    2: {"rango": "05-09", "min": 5, "max": 9, "punto_medio": 7},
    3: {"rango": "10-14", "min": 10, "max": 14, "punto_medio": 12},
    4: {"rango": "15-19", "min": 15, "max": 19, "punto_medio": 17},
    5: {"rango": "20-24", "min": 20, "max": 24, "punto_medio": 22},
    6: {"rango": "25-29", "min": 25, "max": 29, "punto_medio": 27},
    7: {"rango": "30-34", "min": 30, "max": 34, "punto_medio": 32},
    8: {"rango": "35-39", "min": 35, "max": 39, "punto_medio": 37},
    9: {"rango": "40-44", "min": 40, "max": 44, "punto_medio": 42},
    10: {"rango": "45-49", "min": 45, "max": 49, "punto_medio": 47},
    11: {"rango": "50-54", "min": 50, "max": 54, "punto_medio": 52},
    12: {"rango": "55-59", "min": 55, "max": 59, "punto_medio": 57},
    13: {"rango": "60-64", "min": 60, "max": 64, "punto_medio": 62},
    14: {"rango": "65-69", "min": 65, "max": 69, "punto_medio": 67},
    15: {"rango": "70-74", "min": 70, "max": 74, "punto_medio": 72},
    16: {"rango": "75-79", "min": 75, "max": 79, "punto_medio": 77},
    17: {"rango": "80-84", "min": 80, "max": 84, "punto_medio": 82},
    18: {"rango": "85-89", "min": 85, "max": 89, "punto_medio": 87},
    19: {"rango": "90-94", "min": 90, "max": 94, "punto_medio": 92},
    20: {"rango": "95-99", "min": 95, "max": 99, "punto_medio": 97},
    21: {"rango": "100+", "min": 100, "max": 120, "punto_medio": 100},
}

# Grupos de edad amplios para análisis demográfico
GRUPOS_EDAD_AMPLIOS = {
    "Primera infancia (0-9 años)": [1, 2],
    "Niñez (10-14 años)": [3],
    "Adolescencia (15-19 años)": [4],
    "Juventud (20-29 años)": [5, 6],
    "Adultez temprana (30-44 años)": [7, 8, 9],
    "Adultez media (45-59 años)": [10, 11, 12],
    "Adultez mayor (60-74 años)": [13, 14, 15],
    "Vejez (75+ años)": [16, 17, 18, 19, 20, 21],
}


def transformar_edad_rango_a_numero(codigo_rango: int) -> int:
    """
    Transforma un código de rango etario del DANE a un valor numérico único.
    
    Usa el punto medio del rango para análisis estadístico.
    
    Ejemplos:
        1 (00-04) → 2
        4 (15-19) → 17
        10 (45-49) → 47
        21 (100+) → 100
    
    Args:
        codigo_rango: Código del rango etario (1-21)
    
    Returns:
        Punto medio del rango en años
    
    Raises:
        ValueError: Si el código no está en el catálogo DANE
    """
    if codigo_rango not in RANGOS_EDAD_DANE:
        raise ValueError(
            f"Código de rango etario inválido: {codigo_rango}. "
            f"Códigos válidos: 1-21 (catálogo DANE)"
        )
    return RANGOS_EDAD_DANE[codigo_rango]["punto_medio"]


def transformar_numero_a_rango_edad(edad: int) -> dict:
    """
    Transforma una edad numérica a su rango etario correspondiente.
    
    Args:
        edad: Edad en años (0-120)
    
    Returns:
        Diccionario con código, rango y punto medio
    
    Raises:
        ValueError: Si la edad está fuera de rango (0-120)
    """
    if edad < 0 or edad > 120:
        raise ValueError(
            f"Edad inválida: {edad}. Rango aceptado: 0-120 años"
        )
    
    for codigo, datos in RANGOS_EDAD_DANE.items():
        if datos["min"] <= edad <= datos["max"]:
            return {
                "codigo": codigo,
                "rango": datos["rango"],
                "punto_medio": datos["punto_medio"],
            }
    
    # Caso especial: 100+
    return {
        "codigo": 21,
        "rango": "100+",
        "punto_medio": 100,
    }


def obtener_rango_etario_descripcion(codigo: int) -> str:
    """
    Obtiene la descripción textual de un rango etario.
    
    Args:
        codigo: Código del rango (1-21)
    
    Returns:
        Descripción del rango (ej: "de 20 A 24 Años")
    """
    if codigo not in RANGOS_EDAD_DANE:
        return f"Rango inválido ({codigo})"
    
    datos = RANGOS_EDAD_DANE[codigo]
    return f"de {datos['min']:02d} A {datos['max']} Años"


# Funciones de utilidad para conversión de códigos

def obtener_nombre_departamento(codigo: int) -> str:
    """Obtiene el nombre del departamento dado su código DANE."""
    return DEPARTAMENTOS_DANE.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_sexo(codigo: int) -> str:
    """Obtiene el nombre del sexo dado su código DANE."""
    return SEXO.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_grupo_etnico(codigo: int) -> str:
    """Obtiene el nombre del grupo étnico dado su código DANE."""
    return GRUPO_ETNICO.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_estado_civil(codigo: int) -> str:
    """Obtiene el nombre del estado civil dado su código DANE."""
    return ESTADO_CIVIL.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_trabajo(codigo: int) -> str:
    """Obtiene la descripción de la situación laboral dado su código DANE."""
    return TRABAJO.get(codigo, f"Desconocido ({codigo})")
