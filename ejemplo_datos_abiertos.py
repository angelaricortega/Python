# -*- coding: utf-8 -*-
"""
ejemplo_datos_abiertos.py
=======================================================================
Consumo de datos abiertos de Colombia -> API de Encuestas Poblacionales

Dataset fuente:
  Nombre : Encuesta Motociclistas 2022
  URL    : https://www.datos.gov.co/resource/fr9f-9g4b.json
  Licencia: PUBLIC_DOMAIN

Ejecuta:
  python ejemplo_datos_abiertos.py

Requisitos (ya en requirements.txt):
  pip install requests

La API local debe estar corriendo en http://localhost:8001
  uvicorn main:app --port 8001
=======================================================================
"""

import requests
import json
import sys
import time
from typing import Optional, List

# -- Configuración --------------------------------------------------------------

DATOS_ABIERTOS_URL = "https://www.datos.gov.co/resource/fr9f-9g4b.json"
API_LOCAL_URL      = "http://localhost:8001/encuestas/"
LIMITE_REGISTROS   = 50      # cuántos registros traer del dataset abierto
PAUSA_ENTRE_POST   = 0.05    # segundos entre requests (cortesia con la API local)


# -- Tablas de normalización ----------------------------------------------------

MUNICIPIO_A_DEPARTAMENTO = {
    "MEDELLÍN":    "Antioquia",
    "MEDELLIN":    "Antioquia",
    "QUIBDÓ":      "Chocó",
    "QUIBDO":      "Chocó",
    "BOGOTÁ":      "Bogotá D.C.",
    "BOGOTA":      "Bogotá D.C.",
    "CALI":        "Valle del Cauca",
    "BARRANQUILLA":"Atlántico",
    "CARTAGENA":   "Bolivar",
    "BUCARAMANGA": "Santander",
    "MANIZALES":   "Caldas",
    "PEREIRA":     "Risaralda",
    "ARMENIA":     "Quindio",
    "IBAGUÉ":      "Tolima",
    "IBAGUE":      "Tolima",
    "NEIVA":       "Huila",
    "PASTO":       "Nariño",
    "MONTERÍA":    "Córdoba",
    "MONTERIA":    "Córdoba",
    "VILLAVICENCIO": "Meta",
    "CÚCUTA":      "Norte de Santander",
    "CUCUTA":      "Norte de Santander",
}

NIVEL_EDUCATIVO_MAP = {
    "primaria o menos":          "primaria",
    "secundaria":                "secundaria",
    "técnica / tecnológica":     "tecnico",
    "tecnica / tecnologica":     "tecnico",
    "universitaria o postgrado": "universitario",
}

EDAD_GRUPO_A_ENTERO = {
    "<20":   18,
    "21-25": 23,
    "26-30": 28,
    "31-35": 33,
    "36-40": 38,
    "41-45": 43,
    "46-50": 48,
    "51-55": 53,
    "56-60": 58,
    ">60":   63,
}


# -- Helpers de transformación -------------------------------------------------

def normalizar_municipio(raw: str) -> str:
    """Limpia caracteres especiales y normaliza el nombre del municipio."""
    try:
        normalizado = raw.encode("latin-1").decode("utf-8")
    except Exception:
        normalizado = raw
    return normalizado.strip().title()


def inferir_departamento(municipio_raw: str) -> str:
    """Infiere el departamento a partir del nombre del municipio."""
    limpio = municipio_raw.strip().upper()
    # Intentar con y sin tilde
    for clave, depto in MUNICIPIO_A_DEPARTAMENTO.items():
        if clave.upper() == limpio:
            return depto
    return "Antioquia"   # default para este dataset (mayoria Medellin)


def mapear_nivel(raw: str) -> str:
    key = raw.strip().lower()
    # remover tildes para comparación robusta
    key = key.replace("é", "e").replace("á", "a").replace("i", "i").replace("ó", "o").replace("ú", "u")
    return NIVEL_EDUCATIVO_MAP.get(key, "secundaria")


def edad_desde_grupo(grupo: str) -> int:
    return EDAD_GRUPO_A_ENTERO.get(grupo.strip(), 30)


def genero_desde_hombre(hombre: str) -> str:
    return "masculino" if str(hombre).strip() == "1" else "femenino"


def estrato_seguro(raw: str) -> int:
    try:
        v = int(raw)
        return max(1, min(6, v))
    except (ValueError, TypeError):
        return 3


def likert_seguridad_vial(row: dict) -> int:
    """
    Deriva un indice Likert 1–5 de seguridad vial percibida
    combinando uso de EPP (casco, guantes, botas) y perfil de siniestros.
    Mayor uso de EPP + sin siniestros -> mayor satisfacción percibida.
    """
    epp = sum([
        int(row.get("epp_casco",        "0") or "0"),
        int(row.get("epp_guantes",       "0") or "0"),
        int(row.get("epp_botas",         "0") or "0"),
        int(row.get("epp_reflectivos",   "0") or "0"),
        int(row.get("epp_chaquetaprot",  "0") or "0"),
    ])
    siniestros = int(row.get("perfil_siniestros1", "0") or "0")

    # EPP máximo = 5 puntos, penalizar siniestros
    score = epp - siniestros
    # Escalar a rango [1, 5]
    if   score >= 5: return 5
    elif score >= 3: return 4
    elif score >= 2: return 3
    elif score >= 1: return 2
    else:            return 1


def porcentaje_uso_moto(row: dict) -> float:
    """
    Porcentaje estimado de dependencia de la moto como medio de transporte.
    Combina: dias de uso/semana -> porcentaje de la semana laboral.
    """
    try:
        dias = int(row.get("dias_semana", "5") or "5")
        dias = max(0, min(7, dias))
        return round((dias / 7) * 100, 1)
    except (ValueError, TypeError):
        return 71.4   # default: 5/7 dias


def construir_encuesta(row: dict, indice: int) -> dict:
    """
    Convierte una fila del dataset de datos abiertos al formato
    EncuestaCompleta que acepta nuestra API.
    """
    municipio_raw = row.get("municipio", "Medellin")
    municipio     = normalizar_municipio(municipio_raw)
    departamento  = inferir_departamento(municipio_raw)
    genero        = genero_desde_hombre(row.get("hombre", "1"))
    nivel_raw     = row.get("nivel_educativo", "Secundaria")
    ocupacion     = (
        "Repartidor / Domicilios"   if row.get("trabajo_domicilios", "0") == "1"
        else "Transporte de pasajeros" if row.get("trabajo_transporte_pasajeros", "0") == "1"
        else "Motociclista (uso personal)"
    )

    return {
        "encuestado": {
            "nombre":          f"Motociclista {indice:04d} ({municipio})",
            "edad":            edad_desde_grupo(row.get("edad_grupo", "31-35")),
            "genero":          genero,
            "estrato":         estrato_seguro(row.get("estrato_vivienda", "2")),
            "departamento":    departamento,
            "municipio":       municipio,
            "nivel_educativo": mapear_nivel(nivel_raw),
            "ocupacion":       ocupacion,
        },
        "respuestas": [
            {
                "pregunta_id":   1,
                "enunciado":     "Satisfacción con el servicio de salud en su municipio",
                "tipo_pregunta": "likert",
                "valor":         likert_seguridad_vial(row),
            },
            {
                "pregunta_id":   2,
                "enunciado":     "Nivel de confianza en las instituciones colombianas (%)",
                "tipo_pregunta": "porcentaje",
                "valor":         porcentaje_uso_moto(row),
            },
            {
                "pregunta_id":   3,
                "enunciado":     "¿Ha utilizado servicios digitales del Estado en el último mes?",
                "tipo_pregunta": "si_no",
                "valor":         "si" if row.get("licencia_moto", "0") == "1" else "no",
            },
        ],
        "observaciones_generales": (
            f"[Datos Abiertos] Moto: cilindraje {row.get('cilin_grupo','N/A')} | "
            f"modelo {row.get('modelo_grupo','N/A')} | "
            f"dias/semana: {row.get('dias_semana','N/A')} | "
            f"fuente: datos.gov.co/resource/fr9f-9g4b"
        ),
    }


# -- Funciones de consumo -------------------------------------------------------

def obtener_datos_abiertos(limite: int) -> list[dict]:
    """Descarga registros del API de datos abiertos colombianos."""
    print(f"\n[>>] Consultando datos abiertos de Colombia...")
    print(f"   Dataset: Encuesta Motociclistas 2022")
    print(f"   URL: {DATOS_ABIERTOS_URL}")

    params = {
        "$limit":  limite,
        "$offset": 0,
        "$order":  "uuid",
    }

    try:
        resp = requests.get(DATOS_ABIERTOS_URL, params=params, timeout=20)
        resp.raise_for_status()
        datos = resp.json()
        print(f"   [OK] {len(datos)} registros recibidos\n")
        return datos
    except requests.exceptions.ConnectionError:
        print("   [!!] Sin conexión a internet. Usando datos de ejemplo locales.\n")
        return datos_ejemplo_offline()
    except Exception as e:
        print(f"   [!!] Error al consultar: {e}\n")
        return []


def datos_ejemplo_offline() -> list[dict]:
    """Datos de ejemplo hardcodeados para ejecutar sin internet."""
    return [
        {
            "uuid": "offline_01", "municipio": "MEDELLÍN", "estrato_vivienda": "3",
            "hombre": "1", "edad_grupo": "31-35", "nivel_educativo": "Técnica / Tecnológica",
            "epp_casco": "1", "epp_guantes": "1", "epp_botas": "1",
            "epp_reflectivos": "0", "epp_chaquetaprot": "1",
            "perfil_siniestros1": "0", "dias_semana": "6",
            "licencia_moto": "1", "trabajo_domicilios": "1",
            "trabajo_transporte_pasajeros": "0",
            "cilin_grupo": "100-125", "modelo_grupo": "2021-2022",
        },
        {
            "uuid": "offline_02", "municipio": "QUIBDÓ", "estrato_vivienda": "1",
            "hombre": "0", "edad_grupo": "26-30", "nivel_educativo": "Secundaria",
            "epp_casco": "1", "epp_guantes": "0", "epp_botas": "0",
            "epp_reflectivos": "0", "epp_chaquetaprot": "0",
            "perfil_siniestros1": "1", "dias_semana": "5",
            "licencia_moto": "0", "trabajo_domicilios": "0",
            "trabajo_transporte_pasajeros": "1",
            "cilin_grupo": "<100", "modelo_grupo": "2015-2020",
        },
        {
            "uuid": "offline_03", "municipio": "MEDELLÍN", "estrato_vivienda": "5",
            "hombre": "1", "edad_grupo": "41-45", "nivel_educativo": "Universitaria o postgrado",
            "epp_casco": "1", "epp_guantes": "1", "epp_botas": "1",
            "epp_reflectivos": "1", "epp_chaquetaprot": "1",
            "perfil_siniestros1": "0", "dias_semana": "7",
            "licencia_moto": "1", "trabajo_domicilios": "0",
            "trabajo_transporte_pasajeros": "0",
            "cilin_grupo": "126-200", "modelo_grupo": "2021-2022",
        },
    ]


def enviar_a_api(encuesta: dict, indice: int) -> Optional[dict]:
    """Envia una encuesta a la API local y retorna el resultado."""
    try:
        resp = requests.post(API_LOCAL_URL, json=encuesta, timeout=10)
        if resp.status_code == 201:
            return resp.json()
        else:
            print(f"   [!]  Fila {indice}: HTTP {resp.status_code} -> {resp.text[:150]}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"   [!!] No se pudo conectar a {API_LOCAL_URL}")
        print(f"      Asegúrate de que uvicorn esté corriendo:")
        print(f"      uvicorn main:app --port 8001")
        return None


def imprimir_resumen(resultados: List) -> None:
    """Imprime estadisticas del proceso de carga masiva."""
    exitosos = [r for r in resultados if r is not None]
    fallidos  = len(resultados) - len(exitosos)

    sep = "-" * 60
    print("\n" + sep)
    print("  RESUMEN DE CARGA MASIVA - Datos Abiertos -> API Encuestas")
    print(sep)
    print(f"  Total procesados : {len(resultados)}")
    print(f"  [OK] Exitosos    : {len(exitosos)}")
    print(f"  [!!] Fallidos    : {fallidos}")

    if exitosos:
        generos    = {}
        estratos   = {}
        municipios = {}
        for r in exitosos:
            enc = r["encuestado"]
            generos[enc["genero"]]       = generos.get(enc["genero"], 0) + 1
            estratos[enc["estrato"]]     = estratos.get(enc["estrato"], 0) + 1
            municipios[enc["municipio"]] = municipios.get(enc["municipio"], 0) + 1

        print("\n  Distribucion de generos:")
        for k, v in sorted(generos.items()):
            barra = "#" * (v * 20 // len(exitosos))
            print(f"    {k:<20} {barra} {v}")

        print("\n  Distribucion de estratos:")
        for k in sorted(estratos.keys()):
            barra = "#" * (estratos[k] * 20 // len(exitosos))
            print(f"    Estrato {k}: {barra} {estratos[k]}")

        print("\n  Municipios registrados:")
        for k, v in sorted(municipios.items(), key=lambda x: -x[1]):
            print(f"    {k:<25} {v} encuestas")

        print("\n  IDs generados (primeros 3):")
        for r in exitosos[:3]:
            print(f"    {r['id_encuesta']} | {r['encuestado']['nombre']}")

    print(sep)


# -- Main -----------------------------------------------------------------------

def main():
    sep = "=" * 60
    print(sep)
    print("  Ejemplo: Datos Abiertos Colombia -> API Encuestas")
    print("  Dataset: Encuesta Motociclistas 2022 (datos.gov.co)")
    print(sep)

    # 1. Obtener datos del API abierto
    filas = obtener_datos_abiertos(LIMITE_REGISTROS)
    if not filas:
        print("Sin datos para procesar. Saliendo.")
        sys.exit(1)

    # 2. Transformar y enviar cada registro
    print(f"[>>] Transformando y enviando {len(filas)} registros a {API_LOCAL_URL}...")
    print("     fuente: datos.gov.co | dataset: fr9f-9g4b\n")

    resultados = []
    for i, fila in enumerate(filas, start=1):
        try:
            encuesta_payload = construir_encuesta(fila, i)
        except Exception as e:
            print(f"   [!!] Fila {i}: Error en transformacion: {e}")
            resultados.append(None)
            continue

        resultado = enviar_a_api(encuesta_payload, i)
        resultados.append(resultado)

        if resultado:
            enc = resultado["encuestado"]
            print(f"   [{i:>3}] OK  ID {resultado['id_encuesta'][:8]}..."
                  f" | {enc['nombre'][:35]:<35}"
                  f" | estrato {enc['estrato']} | {enc['genero']}")
        else:
            if resultado is None and i == 1:
                print("\n[STOP] La API local no responde. Deteniendose.")
                print(f"       Ejecuta: uvicorn main:app --port 8001\n")
                imprimir_resumen(resultados)
                sys.exit(1)

        time.sleep(PAUSA_ENTRE_POST)

    # 3. Resumen final
    imprimir_resumen(resultados)

    # 4. Verificar estadisticas en la API
    print("\n[stats] Consultando estadisticas actuales de la API...")
    try:
        stats = requests.get("http://localhost:8001/encuestas/estadisticas/", timeout=5).json()
        print(f"   Total encuestas en DB  : {stats.get('total_encuestas', 'N/A')}")
        print(f"   Promedio Likert global : {stats.get('promedio_satisfaccion', 'N/A')}")
        dist = stats.get("distribucion_departamentos", {})
        if dist:
            depto_list = list(dist.keys())
            print(f"   Departamentos con datos: {', '.join(depto_list[:5])}")
    except Exception as e:
        print(f"   (No se pudo obtener estadisticas: {e})")

    print("\n[OK] Proceso completado. Visita http://localhost:8001/docs para explorar la API.")


if __name__ == "__main__":
    main()
