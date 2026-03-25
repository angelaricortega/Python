"""
censo_endpoints.py — Endpoints para carga y análisis del Censo 2018.

Endpoints implementados:
- POST /censo-2018/upload-batch/      → Carga masiva de CSV del DANE
- POST /censo-2018/upload-csv/        → Carga de CSV con procesamiento batch
- GET /censo-2018/estadisticas/       → Estadísticas descriptivas completas
- GET /censo-2018/indice/masculinidad/ → Índice de masculinidad
- GET /censo-2018/indice/dependencia/  → Índice de dependencia demográfica
- GET /censo-2018/registros/          → Listar registros con paginación
- GET /censo-2018/registros/{id}      → Obtener registro específico

Justificación técnica:
─────────────────────────────────────────────────────────────────────────────
Los endpoints están implementados con async/await para:
- No bloquear el event loop durante carga de archivos grandes
- Permitir consultas concurrentes a la base de datos
- Escalar a miles de requests simultáneos

El procesamiento batch carga de 10,000 en 10,000 registros para:
- Evitar saturación de memoria RAM
- Permitir rollback en caso de error
- Proporcionar feedback progresivo al usuario
─────────────────────────────────────────────────────────────────────────────
"""

import io
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, crear_tablas
from models_censo import (
    RegistroCenso2018ORM,
    RegistroCenso2018Base,
    RegistroCenso2018Create,
    RegistroCenso2018Response,
    EstadisticasCenso2018,
    IndiceDemografico,
)
from censo_codes import (
    DEPARTAMENTOS_DANE,
    SEXO,
    GRUPO_ETNICO,
    ESTADO_CIVIL,
    TRABAJO,
    RANGOS_EDAD_DANE,
    GRUPOS_EDAD_AMPLIOS,
    obtener_nombre_municipio,
)

logger = logging.getLogger("censo_api")
router = APIRouter(prefix="/censo-2018", tags=["Censo 2018"])


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Upload masivo de CSV
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/upload-csv/",
    summary="Cargar archivo CSV del Censo 2018 (OPTIMIZADO)",
    description="""
Carga masiva de datos del Censo Nacional de Población y Vivienda 2018 del DANE desde un archivo CSV.

## Formato esperado del archivo

El CSV debe ser el archivo oficial del DANE. Los nombres de columna se normalizan automáticamente
a mayúsculas y se eliminan espacios, por lo que `u_dpto`, `U_DPTO` y `U_DPTO ` son equivalentes.

### Columnas obligatorias

| Columna | Descripción |
|---------|-------------|
| `U_DPTO` | Código DIVIPOLA del departamento (5=Antioquia, 11=Bogotá, etc.) |
| `P_SEXO` | Sexo (1=Hombre, 2=Mujer) |

### Columnas opcionales reconocidas (completo)

| Columna | Descripción |
|---------|-------------|
| `U_MPIO` | Código de municipio (DIVIPOLA) |
| `P_EDADR` | **Código de rango etario** (1-21, ver tabla abajo) — NO es edad en años |
| `PA1_GRP_ETNIC` | Grupo étnico (1=Indígena, 2=Gitano ROM, 3=Raizal, 4=Palenquero, 5=Negro/Afrocolombiano, 6=Ninguno) |
| `P_NIVEL_ANOSR` | Nivel educativo máximo alcanzado (código DANE) |
| `P_ESTADO_CIVIL` | Estado civil (1=Unión libre, 2=Separado/a, 3=Viudo/a, 4=Soltero/a, 5=Casado/a, 9=N/A) |
| `P_TRABAJO` | Situación laboral (1=Trabajó, 2=Tenía trabajo pero no trabajó, 3=Buscó trabajo, 4=Estudió, etc.) |
| `PA_LO_ATENDIERON` | Atención en salud (1=Sí, 2=No) |
| `PA1_CALIDAD_SERV` | Calidad del servicio de salud (1=Buena, 2=Regular, 3=Mala) |
| `PA_HABLA_LENG` | Habla lengua nativa (1=Sí, 2=No) |
| `PA1_ENTIENDE` | Entiende lengua nativa aunque no la hable (1=Sí, 2=No) |
| `PB_OTRAS_LENG` | Habla otras lenguas (1=Sí, 2=No) |
| `PB1_QOTRAS_LENG` | Cuál otra lengua (texto, max 100 caracteres) |
| `PA_VIVIA_1ANO` | Dónde vivía hace un año (código DANE) |

### Tabla de rangos etarios `P_EDADR`

El DANE **no captura edades individuales** sino rangos quinquenales. Guardar el código como
número y derivar una edad sería inventar datos. La API almacena el **código del rango**:

| Código | Rango | Código | Rango |
|--------|-------|--------|-------|
| 1 | 00-04 años | 12 | 55-59 años |
| 2 | 05-09 años | 13 | 60-64 años |
| 3 | 10-14 años | 14 | 65-69 años |
| 4 | 15-19 años | 15 | 70-74 años |
| 5 | 20-24 años | 16 | 75-79 años |
| 6 | 25-29 años | 17 | 80-84 años |
| 7 | 30-34 años | 18 | 85-89 años |
| 8 | 35-39 años | 19 | 90-94 años |
| 9 | 40-44 años | 20 | 95-99 años |
| 10 | 45-49 años | 21 | 100+ años |
| 11 | 50-54 años | — | — |

Códigos fuera del rango 1-21 son rechazados.

## Estrategia de procesamiento (bulk insert por chunks)

El archivo se lee **50,000 filas a la vez** usando `pandas.read_csv(chunksize=50000)` para no
cargar el CSV completo en RAM. Cada chunk se valida y se inserta en bloque
(`RegistroCenso2018ORM.__table__.insert()` con lista de dicts), que es entre 10× y 50× más
rápido que `session.add()` fila por fila.

### Flujo por chunk
1. Normalizar nombres de columna a mayúsculas.
2. Verificar que `U_DPTO` y `P_SEXO` existan; si no, **todo el chunk se omite**.
3. Por cada fila, validar rangos básicos:
   - `U_DPTO` ∈ [1, 99]
   - `P_SEXO` ∈ [1, 2]
   - `P_EDADR` ∈ [1, 21] (si presente)
4. Insertar el chunk completo en una sola transacción.
5. Acumular contadores y muestras de error.

## Campos de respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `mensaje` | string | Resumen legible con tiempo y conteos |
| `total_procesados` | int | Total de filas leídas del CSV (incluyendo las fallidas) |
| `exitosos` | int | Filas insertadas exitosamente en la BD |
| `fallidos` | int | Filas rechazadas por validación o error de parsing |
| `tiempo_segundos` | float | Tiempo total de procesamiento en segundos |
| `errores` | array | Muestra de hasta 5 errores: `{"fila": N, "error": "..."}` |

## Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Procesamiento completado (exitosos puede ser 0 si todo falló) |
| 400 | El archivo no tiene extensión `.csv` |
| 500 | Error inesperado al leer o procesar el archivo |

## Nota de rendimiento

Un archivo de 1 millón de registros tarda entre 30 y 120 segundos según el hardware.
Para archivos superiores a 500 MB, aumentar el timeout del cliente HTTP.
""",
    response_model=dict,
)
async def upload_censo_csv_optimizado(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Carga masiva OPTIMIZADA de CSV del Censo 2018.
    
    OPTIMIZACIONES:
    1. Bulk insert con SQLAlchemy (execute + values)
    2. Validación mínima (solo rangos básicos)
    3. Chunks de 50,000 registros (en lugar de 10,000)
    4. Transacciones por lote eficientes
    5. Sin overhead de Pydantic por fila
    
    RETORNA:
    - Total de registros procesados
    - Registros exitosos vs fallidos
    - Tiempo total de procesamiento
    """
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use solo archivos .csv")
    
    logger.info(f"CENSO UPLOAD OPTIMIZADO | Archivo: {file.filename}")
    inicio_total = time.time()
    
    try:
        # Leer CSV con pandas directamente
        contenido = await file.read()
        
        # Leer en chunks para memoria eficiente
        chunk_size = 50000  # 50k registros por chunk
        total_registros = 0
        registros_exitosos = 0
        registros_fallidos = 0
        errores_muestra = []
        
        # Usar StringIO para leer desde bytes
        csv_buffer = io.BytesIO(contenido)
        
        for chunk_num, chunk_df in enumerate(pd.read_csv(csv_buffer, chunksize=chunk_size, low_memory=False)):
            logger.info(f"Procesando chunk {chunk_num + 1} con {len(chunk_df)} registros...")
            
            # Normalizar nombres de columnas
            chunk_df.columns = [str(c).upper().strip() for c in chunk_df.columns]
            
            # Verificar columnas mínimas
            if 'U_DPTO' not in chunk_df.columns or 'P_SEXO' not in chunk_df.columns:
                registros_fallidos += len(chunk_df)
                if len(errores_muestra) < 5:
                    errores_muestra.append({"chunk": chunk_num, "error": "Columnas requeridas no encontradas"})
                continue
            
            # Preparar datos para bulk insert (lista de diccionarios)
            registros_para_insertar = []
            
            for idx, row in chunk_df.iterrows():
                try:
                    # Validación mínima pero crítica
                    u_dpto = int(row.get('U_DPTO')) if pd.notna(row.get('U_DPTO')) else None
                    p_sexo = int(row.get('P_SEXO')) if pd.notna(row.get('P_SEXO')) else None
                    
                    # EDAD: Se guarda el CÓDIGO DEL RANGO (1-21), NO se transforma
                    # El DANE usa rangos estarios, no edades individuales
                    # Para análisis usaremos el rango completo, no un punto medio inventado
                    p_edadr = int(row.get('P_EDADR')) if pd.notna(row.get('P_EDADR')) else None
                    
                    # Validar que el código de rango esté en el catálogo DANE (1-21)
                    if p_edadr and (p_edadr < 1 or p_edadr > 21):
                        registros_fallidos += 1
                        continue
                    
                    # Validar rangos básicos (rápido)
                    if u_dpto and (u_dpto < 1 or u_dpto > 99):
                        registros_fallidos += 1
                        continue
                    
                    if p_sexo and (p_sexo < 1 or p_sexo > 2):
                        registros_fallidos += 1
                        continue
                    
                    # Construir registro para bulk insert
                    registro = {
                        'tipo_reg': int(row.get('TIPO_REG', 5)) if pd.notna(row.get('TIPO_REG')) else 5,
                        'u_dpto': u_dpto,
                        'u_mpio': int(row.get('U_MPIO')) if pd.notna(row.get('U_MPIO')) else None,
                        'ua_clase': int(row.get('UA_CLASE')) if pd.notna(row.get('UA_CLASE')) else None,
                        'cod_encuestas': int(row.get('COD_ENCUESTAS')) if pd.notna(row.get('COD_ENCUESTAS')) else None,
                        'u_vivienda': int(row.get('U_VIVIENDA')) if pd.notna(row.get('U_VIVIENDA')) else None,
                        'p_nrohog': int(row.get('P_NROHOG')) if pd.notna(row.get('P_NROHOG')) else None,
                        'p_nro_per': int(row.get('P_NRO_PER')) if pd.notna(row.get('P_NRO_PER')) else None,
                        'p_sexo': p_sexo,
                        'p_edadr': p_edadr,
                        'p_parentescor': int(row.get('P_PARENTESCOR')) if pd.notna(row.get('P_PARENTESCOR')) else None,
                        'pa1_grp_etnic': int(row.get('PA1_GRP_ETNIC')) if pd.notna(row.get('PA1_GRP_ETNIC')) else None,
                        'pa11_cod_etnia': int(row.get('PA11_COD_ETNIA')) if pd.notna(row.get('PA11_COD_ETNIA')) else None,
                        'pa12_clan': str(row.get('PA12_CLAN', ''))[:50] if pd.notna(row.get('PA12_CLAN')) else None,
                        'p_enfermo': int(row.get('P_ENFERMO')) if pd.notna(row.get('P_ENFERMO')) else None,
                        'condicion_fisica': int(row.get('CONDICION_FISICA')) if pd.notna(row.get('CONDICION_FISICA')) else None,
                        'p_alfabeta': int(row.get('P_ALFABETA')) if pd.notna(row.get('P_ALFABETA')) else None,
                        'pa_asistencia': int(row.get('PA_ASISTENCIA')) if pd.notna(row.get('PA_ASISTENCIA')) else None,
                        'p_nivel_anosr': int(row.get('P_NIVEL_ANOSR')) if pd.notna(row.get('P_NIVEL_ANOSR')) else None,
                        'p_trabajo': int(row.get('P_TRABAJO')) if pd.notna(row.get('P_TRABAJO')) else None,
                        'p_est_civil': int(row.get('P_EST_CIVIL')) if pd.notna(row.get('P_EST_CIVIL')) else None,
                        # Variables de fecundidad
                        'pa_hnv': int(row.get('PA_HNV')) if pd.notna(row.get('PA_HNV')) else None,
                        'pa1_thnv': int(row.get('PA1_THNV')) if pd.notna(row.get('PA1_THNV')) else None,
                        'pa2_hnvh': int(row.get('PA2_HNVH')) if pd.notna(row.get('PA2_HNVH')) else None,
                        'pa3_hnvm': int(row.get('PA3_HNVM')) if pd.notna(row.get('PA3_HNVM')) else None,
                        'pa_hnvs': int(row.get('PA_HNVS')) if pd.notna(row.get('PA_HNVS')) else None,
                        'pa1_thsv': int(row.get('PA1_THSV')) if pd.notna(row.get('PA1_THSV')) else None,
                        'pa2_hsvh': int(row.get('PA2_HSVH')) if pd.notna(row.get('PA2_HSVH')) else None,
                        'pa3_hsvm': int(row.get('PA3_HSVM')) if pd.notna(row.get('PA3_HSVM')) else None,
                        'pa_hfc': int(row.get('PA_HFC')) if pd.notna(row.get('PA_HFC')) else None,
                        'pa1_thfc': int(row.get('PA1_THFC')) if pd.notna(row.get('PA1_THFC')) else None,
                        'pa2_hfch': int(row.get('PA2_HFCH')) if pd.notna(row.get('PA2_HFCH')) else None,
                        'pa3_hfcm': int(row.get('PA3_HFCM')) if pd.notna(row.get('PA3_HFCM')) else None,
                        'pa_uhnv': int(row.get('PA_UHNV')) if pd.notna(row.get('PA_UHNV')) else None,
                        'pa1_mes_uhnv': int(row.get('PA1_MES_UHNV')) if pd.notna(row.get('PA1_MES_UHNV')) else None,
                        'pa2_ano_uhnv': int(row.get('PA2_ANO_UHNV')) if pd.notna(row.get('PA2_ANO_UHNV')) else None,
                        # Migración
                        'pa_lug_nac': int(row.get('PA_LUG_NAC')) if pd.notna(row.get('PA_LUG_NAC')) else None,
                        'pa_vivia_5anos': int(row.get('PA_VIVIA_5ANOS')) if pd.notna(row.get('PA_VIVIA_5ANOS')) else None,
                        'pa_vivia_1ano': int(row.get('PA_VIVIA_1ANO')) if pd.notna(row.get('PA_VIVIA_1ANO')) else None,
                        # Atención en salud
                        'pa_lo_atendieron': int(row.get('PA_LO_ATENDIERON')) if pd.notna(row.get('PA_LO_ATENDIERON')) else None,
                        'pa1_calidad_serv': int(row.get('PA1_CALIDAD_SERV')) if pd.notna(row.get('PA1_CALIDAD_SERV')) else None,
                        # Lenguaje
                        'pa_habla_leng': int(row.get('PA_HABLA_LENG')) if pd.notna(row.get('PA_HABLA_LENG')) else None,
                        'pa1_entiende': int(row.get('PA1_ENTIENDE')) if pd.notna(row.get('PA1_ENTIENDE')) else None,
                        'pb_otras_leng': int(row.get('PB_OTRAS_LENG')) if pd.notna(row.get('PB_OTRAS_LENG')) else None,
                        'pb1_qotras_leng': str(row.get('PB1_QOTRAS_LENG', ''))[:100] if pd.notna(row.get('PB1_QOTRAS_LENG')) else None,
                        # Metadatos
                        'archivo_origen': file.filename,
                        'fila_original': total_registros + idx + 1,
                    }
                    registros_para_insertar.append(registro)
                    registros_exitosos += 1
                    
                except Exception as e:
                    registros_fallidos += 1
                    if len(errores_muestra) < 5:
                        errores_muestra.append({"fila": total_registros + idx, "error": str(e)[:100]})
            
            # BULK INSERT - mucho más rápido que add_all()
            if registros_para_insertar:
                await db.execute(RegistroCenso2018ORM.__table__.insert(), registros_para_insertar)
                await db.commit()
            
            total_registros += len(chunk_df)
            logger.info(f"Chunk {chunk_num + 1} completado. Exitosos: {registros_exitosos}, Fallidos: {registros_fallidos}")
        
        tiempo_total = time.time() - inicio_total
        logger.info(f"CENSO UPLOAD COMPLETADO | Total: {total_registros} | Tiempo: {tiempo_total:.2f}s")
        
        return {
            "mensaje": f"Carga completada en {tiempo_total:.2f} segundos. {registros_exitosos} registros creados, {registros_fallidos} filas fallidas.",
            "total_procesados": total_registros,
            "exitosos": registros_exitosos,
            "fallidos": registros_fallidos,
            "tiempo_segundos": round(tiempo_total, 2),
            "errores": errores_muestra,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CENSO UPLOAD ERROR | {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar CSV: {str(e)[:500]}")


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Estadísticas descriptivas
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/estadisticas/",
    summary="Estadísticas descriptivas del Censo 2018",
    description="""
Genera un resumen estadístico completo de todos los registros del Censo 2018 cargados en la base de datos.

## Aclaración crítica sobre la edad

El Censo 2018 del DANE **no captura edades individuales**. El campo `p_edadr` contiene un
**código de rango etario** (entero 1-21). La API **no transforma** estos códigos a edades
numéricas porque hacerlo requeriría asumir un punto medio arbitrario (e.g. tomar 17 para
el rango 15-19 años), lo que introduce sesgo estadístico. En su lugar se ofrecen dos
distribuciones basadas en los rangos originales del DANE.

## Campos del response

### Totales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `total_registros` | int | Total de personas registradas en la BD |

### Distribuciones (dict `{etiqueta: conteo}`)

| Campo | Descripción |
|-------|-------------|
| `distribucion_por_sexo` | Claves: `"Hombre"`, `"Mujer"` |
| `distribucion_por_departamento` | Claves: nombre del departamento (DIVIPOLA), ordenado por conteo desc |
| `distribucion_por_municipio` | **Top 15** municipios por conteo; claves: `"Nombre Municipio (Depto)"` |
| `distribucion_por_grupo_etnico` | Claves: etiqueta del grupo étnico según catálogo DANE |
| `distribucion_por_nivel_educativo` | Claves: descripción del nivel según catálogo DANE |
| `distribucion_por_estado_civil` | Claves: descripción del estado civil |
| `distribucion_por_trabajo` | Claves: descripción de la situación laboral |
| `distribucion_por_grupos_edad` | Grupos amplios: `"0-14 años"`, `"15-64 años"`, `"65+ años"` |
| `distribucion_por_rangos_edad` | 21 rangos quinquenales del DANE: `"00-04 años"` … `"100+ años"` |

### Índices demográficos

| Campo | Tipo | Fórmula | Interpretación |
|-------|------|---------|----------------|
| `indice_masculinidad` | float\|null | (Hombres / Mujeres) × 100 | >100 → más hombres; <100 → más mujeres; null si no hay mujeres |
| `indice_dependencia` | float\|null | ((Pob. <15 + Pob. >64) / Pob. 15-64) × 100 | >60 alta presión; 40-60 equilibrio; <40 baja presión; null si no hay población activa |

Los índices demográficos usan los **códigos DANE directamente**:
- Población joven (<15 años): códigos `p_edadr` 1, 2, 3
- Población activa (15-64 años): códigos 4 al 13
- Adultos mayores (65+ años): códigos 14 al 21

## Comportamiento con BD vacía

Si no hay registros cargados, retorna un objeto con `total_registros = 0` y todos los
diccionarios vacíos. Los índices serán `null`.

## Rendimiento

Todas las consultas son asíncronas y no bloquean el event loop. Para millones de registros
se recomienda tener índices en `p_sexo`, `u_dpto` y `p_edadr` (creados automáticamente al
cargar datos).

## Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Estadísticas generadas exitosamente |
| 500 | Error en base de datos |
""",
    response_model=EstadisticasCenso2018,
)
async def obtener_estadisticas_censo(db: AsyncSession = Depends(get_db)):
    """
    Estadísticas descriptivas del Censo 2018.

    NOTA SOBRE EDAD: El Censo 2018 usa RANGOS ESTÁRIOS (códigos 1-21), no edades individuales.
    - Código 1 = 00-04 años, Código 4 = 15-19 años, etc.
    - NO transformamos a edad numérica porque sería inventar datos inexistentes.
    - Las estadísticas de edad muestran distribución por RANGOS, no por edad individual.

    CONSULTAS:
    - Total de registros
    - Distribución por rangos de edad (códigos 1-21)
    - Distribución por sexo
    - Distribución por departamento
    - Distribución por grupo étnico
    - Distribución por nivel educativo
    - Distribución por estado civil
    - Distribución por situación laboral
    - Índices demográficos (calculados usando rangos)
    """
    # Total de registros
    total_result = await db.execute(select(func.count()).select_from(RegistroCenso2018ORM))
    total_registros = total_result.scalar()

    if total_registros == 0:
        return EstadisticasCenso2018(
            total_registros=0,
            distribucion_por_sexo={},
            distribucion_por_departamento={},
            distribucion_por_municipio={},
            distribucion_por_grupo_etnico={},
            distribucion_por_nivel_educativo={},
            distribucion_por_estado_civil={},
            distribucion_por_trabajo={},
            indice_masculinidad=None,
            indice_dependencia=None,
        )

    # IMPORTANTE: p_edadr contiene CÓDIGOS DE RANGO (1-21), NO edades individuales.
    # No se calculan promedio/mediana/min/max de edad porque estadísticamente no tiene sentido
    # aplicar aritmética sobre códigos ordinales de rango. Se usan directamente para índices.

    # Distribución por sexo
    sexo_dist = await db.execute(
        select(RegistroCenso2018ORM.p_sexo, func.count())
        .group_by(RegistroCenso2018ORM.p_sexo)
    )
    distribucion_por_sexo = {}
    for codigo, count in sexo_dist.all():
        if codigo == 1:
            distribucion_por_sexo["Hombre"] = count
        elif codigo == 2:
            distribucion_por_sexo["Mujer"] = count

    # Distribución por departamento
    depto_dist = await db.execute(
        select(RegistroCenso2018ORM.u_dpto, func.count())
        .group_by(RegistroCenso2018ORM.u_dpto)
        .order_by(func.count().desc())
    )
    distribucion_por_departamento = {}
    for codigo, count in depto_dist.all():
        if codigo is not None:
            nombre = DEPARTAMENTOS_DANE.get(codigo, f"Depto {codigo}")
            distribucion_por_departamento[nombre] = count

    # Distribución por grupo étnico
    etnia_dist = await db.execute(
        select(RegistroCenso2018ORM.pa1_grp_etnic, func.count())
        .group_by(RegistroCenso2018ORM.pa1_grp_etnic)
        .order_by(func.count().desc())
    )
    distribucion_por_grupo_etnico = {}
    for codigo, count in etnia_dist.all():
        if codigo == 5:
            distribucion_por_grupo_etnico["Ninguno de los anteriores"] = count
        elif codigo == 6:
            distribucion_por_grupo_etnico["Indígena"] = count
        elif codigo == 4:
            distribucion_por_grupo_etnico["Negro(a), Mulato(a), Afrocolombiano(a)"] = count
        elif codigo == 9:
            distribucion_por_grupo_etnico["Ignorado"] = count
        elif codigo:
            distribucion_por_grupo_etnico[f"Grupo {codigo}"] = count
    
    # Distribución por nivel educativo
    nivel_dist = await db.execute(
        select(RegistroCenso2018ORM.p_nivel_anosr, func.count())
        .group_by(RegistroCenso2018ORM.p_nivel_anosr)
    )
    distribucion_por_nivel_educativo = {}
    for nivel, count in nivel_dist.all():
        if nivel is not None:
            if nivel < 6:
                clave = "Primaria"
            elif nivel < 11:
                clave = "Secundaria"
            elif nivel == 11:
                clave = "Media"
            elif nivel == 99:
                clave = "Ignorado"
            else:
                clave = f"Nivel {nivel}"
            distribucion_por_nivel_educativo[clave] = distribucion_por_nivel_educativo.get(clave, 0) + count
    
    # Distribución por estado civil
    estado_civil_dist = await db.execute(
        select(RegistroCenso2018ORM.p_est_civil, func.count())
        .group_by(RegistroCenso2018ORM.p_est_civil)
    )
    distribucion_por_estado_civil = {}
    for codigo, count in estado_civil_dist.all():
        if codigo is not None:
            etiqueta = ESTADO_CIVIL.get(codigo, f"Código {codigo}")
            distribucion_por_estado_civil[etiqueta] = distribucion_por_estado_civil.get(etiqueta, 0) + count

    # Distribución por trabajo
    trabajo_dist = await db.execute(
        select(RegistroCenso2018ORM.p_trabajo, func.count())
        .group_by(RegistroCenso2018ORM.p_trabajo)
    )
    distribucion_por_trabajo = {}
    for codigo, count in trabajo_dist.all():
        if codigo is not None:
            etiqueta = TRABAJO.get(codigo, f"Código {codigo}")
            distribucion_por_trabajo[etiqueta] = distribucion_por_trabajo.get(etiqueta, 0) + count
    
    # Calcular índices demográficos
    hombres = distribucion_por_sexo.get("Hombre", 0)
    mujeres = distribucion_por_sexo.get("Mujer", 0)

    indice_masculinidad = None
    if mujeres > 0:
        indice_masculinidad = round((hombres / mujeres) * 100, 2)

    # Índice de dependencia - USANDO RANGOS ESTÁRIOS (códigos 1-21)
    # Rangos del DANE:
    #   < 15 años = códigos 1-3 (00-04, 05-09, 10-14)
    #   15-64 años = códigos 4-13 (15-19, 20-24, ..., 60-64)
    #   > 64 años = códigos 14-21 (65-69, 70-74, ..., 100+)
    
    poblacion_joven = await db.execute(
        select(func.count()).where(
            RegistroCenso2018ORM.p_edadr.in_([1, 2, 3])  # 00-14 años
        )
    )
    poblacion_adulta_mayor = await db.execute(
        select(func.count()).where(
            RegistroCenso2018ORM.p_edadr.in_([14, 15, 16, 17, 18, 19, 20, 21])  # 65+ años
        )
    )
    poblacion_activa = await db.execute(
        select(func.count()).where(
            RegistroCenso2018ORM.p_edadr.in_([4, 5, 6, 7, 8, 9, 10, 11, 12, 13])  # 15-64 años
        )
    )

    indice_dependencia = None
    pop_activa = poblacion_activa.scalar()
    if pop_activa and pop_activa > 0:
        dependencia = ((poblacion_joven.scalar() or 0) + (poblacion_adulta_mayor.scalar() or 0)) / pop_activa * 100
        indice_dependencia = round(dependencia, 2)

    # Distribución por grupos de edad amplios
    distribucion_por_grupos_edad = {}
    for grupo_nombre, codigos in GRUPOS_EDAD_AMPLIOS.items():
        total_grupo = await db.execute(
            select(func.count()).where(RegistroCenso2018ORM.p_edadr.in_(codigos))
        )
        count = total_grupo.scalar() or 0
        if count > 0:
            distribucion_por_grupos_edad[grupo_nombre] = count

    # Distribución por rangos etarios detallados (19-21 rangos del DANE)
    distribucion_por_rangos_edad = {}
    edad_dist = await db.execute(
        select(RegistroCenso2018ORM.p_edadr, func.count())
        .group_by(RegistroCenso2018ORM.p_edadr)
        .order_by(RegistroCenso2018ORM.p_edadr)
    )
    for codigo, count in edad_dist.all():
        if codigo and codigo in RANGOS_EDAD_DANE:
            rango_str = RANGOS_EDAD_DANE[codigo]["rango"]
            distribucion_por_rangos_edad[f"{rango_str} años"] = count

    # Distribución por municipio — top 15, cruzado con catálogo DIVIPOLA
    mpio_dist = await db.execute(
        select(RegistroCenso2018ORM.u_dpto, RegistroCenso2018ORM.u_mpio, func.count())
        .group_by(RegistroCenso2018ORM.u_dpto, RegistroCenso2018ORM.u_mpio)
        .order_by(func.count().desc())
        .limit(15)
    )
    distribucion_por_municipio = {}
    for dpto, mpio, count in mpio_dist.all():
        if dpto is not None and mpio is not None:
            nombre = obtener_nombre_municipio(dpto, mpio)
            distribucion_por_municipio[nombre] = count

    return EstadisticasCenso2018(
        total_registros=total_registros,
        distribucion_por_sexo=distribucion_por_sexo,
        distribucion_por_departamento=distribucion_por_departamento,
        distribucion_por_municipio=distribucion_por_municipio,
        distribucion_por_grupo_etnico=distribucion_por_grupo_etnico,
        distribucion_por_nivel_educativo=distribucion_por_nivel_educativo,
        distribucion_por_estado_civil=distribucion_por_estado_civil,
        distribucion_por_trabajo=distribucion_por_trabajo,
        distribucion_por_grupos_edad=distribucion_por_grupos_edad,
        distribucion_por_rangos_edad=distribucion_por_rangos_edad,
        indice_masculinidad=indice_masculinidad,
        indice_dependencia=indice_dependencia,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Índice de masculinidad
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/indice/masculinidad/",
    summary="Índice de masculinidad",
    description="""
Calcula el **índice de masculinidad** para los registros del Censo 2018 cargados en la BD,
con filtro opcional por departamento.

## Fórmula

```
Índice de masculinidad = (Hombres / Mujeres) × 100
```

## Interpretación

| Valor | Significado |
|-------|-------------|
| > 100 | Más hombres que mujeres (e.g. 105 → 105 hombres por cada 100 mujeres) |
| = 100 | Paridad numérica exacta entre sexos |
| < 100 | Más mujeres que hombres (e.g. 95 → 95 hombres por cada 100 mujeres) |
| `null` | No hay mujeres en los datos filtrados (división por cero evitada) |

En Colombia el índice nacional ronda 96-97, reflejando ligera mayoría femenina.

## Parámetro de filtro

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `departamento` | int (opcional) | Código DIVIPOLA del departamento. Ejemplos: 5=Antioquia, 11=Bogotá D.C., 76=Valle del Cauca |

Si se omite, el índice se calcula sobre **todos** los registros de la BD.

## Campos del response (`IndiceDemografico`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre` | string | `"Índice de masculinidad"` |
| `valor` | float | Resultado numérico (0 si no se puede calcular) |
| `descripcion` | string | Descripción textual del indicador |
| `formula` | string | `"(Hombres / Mujeres) × 100"` |
| `desglose` | dict | `{"hombres": N, "mujeres": N, "total": N}` y opcionalmente `"departamento": "Nombre"` |

## Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Índice calculado (verificar `valor` para saber si fue posible calcularlo) |
| 500 | Error en base de datos |
""",
    response_model=IndiceDemografico,
)
async def obtener_indice_masculinidad(
    departamento: Optional[int] = Query(None, description="Filtrar por departamento (código DANE)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Índice de masculinidad.
    
    FÓRMULA: (Hombres / Mujeres) × 100
    
    INTERPRETACIÓN:
    - > 100: Más hombres que mujeres
    - = 100: Igualdad numérica
    - < 100: Más mujeres que hombres
    """
    query = select(
        RegistroCenso2018ORM.p_sexo,
        func.count().label('count')
    ).where(
        RegistroCenso2018ORM.p_sexo.in_([1, 2])
    )
    
    if departamento:
        query = query.where(RegistroCenso2018ORM.u_dpto == departamento)
    
    query = query.group_by(RegistroCenso2018ORM.p_sexo)
    
    result = await db.execute(query)
    conteo = {sexo: count for sexo, count in result.all()}
    
    hombres = conteo.get(1, 0)
    mujeres = conteo.get(2, 0)
    
    indice = (hombres / mujeres * 100) if mujeres > 0 else None
    
    desglose = {
        "hombres": hombres,
        "mujeres": mujeres,
        "total": hombres + mujeres,
    }
    
    if departamento:
        desglose["departamento"] = DEPARTAMENTOS_DANE.get(departamento, f"Depto {departamento}")

    return IndiceDemografico(
        nombre="Índice de masculinidad",
        valor=indice or 0,
        descripcion="Relación entre población masculina y femenina",
        formula="(Hombres / Mujeres) × 100",
        desglose=desglose,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Índice de dependencia
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/indice/dependencia/",
    summary="Índice de dependencia demográfica",
    description="""
Calcula el **índice de dependencia demográfica** para los registros del Censo 2018 cargados,
con filtro opcional por departamento.

## Fórmula

```
Índice de dependencia = ((Población <15 años + Población >64 años) / Población 15-64 años) × 100
```

## Interpretación

| Rango | Nivel | Significado |
|-------|-------|-------------|
| < 40 | Bajo | Poca presión sobre la población activa |
| 40 – 60 | Medio | Equilibrio relativo |
| > 60 | Alto | Gran presión demográfica sobre la población en edad de trabajar |
| `null` | N/A | No hay población en edad activa (15-64) en los datos filtrados |

## Correspondencia entre grupos etarios y códigos DANE `p_edadr`

| Grupo | Rango de años | Códigos `p_edadr` |
|-------|--------------|-------------------|
| Población joven (numerador) | 0-14 años | 1, 2, 3 |
| Población activa (denominador) | 15-64 años | 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 |
| Adultos mayores (numerador) | 65+ años | 14, 15, 16, 17, 18, 19, 20, 21 |

Los códigos corresponden exactamente a los rangos quinquenales del DANE (ver endpoint
`/upload-csv/` para la tabla completa).

## Parámetro de filtro

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `departamento` | int (opcional) | Código DIVIPOLA (5=Antioquia, 11=Bogotá, 76=Valle del Cauca, etc.) |

## Campos del response (`IndiceDemografico`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre` | string | `"Índice de dependencia demográfica"` |
| `valor` | float | Resultado (0 si no se puede calcular) |
| `descripcion` | string | Descripción del indicador |
| `formula` | string | Fórmula textual |
| `desglose` | dict | `{"poblacion_joven (<15)": N, "poblacion_adulta_mayor (>64)": N, "poblacion_activa (15-64)": N, "total_dependiente": N}` y opcionalmente `"departamento": "Nombre"` |

## Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Índice calculado exitosamente |
| 500 | Error en base de datos |
""",
    response_model=IndiceDemografico,
)
async def obtener_indice_dependencia(
    departamento: Optional[int] = Query(None, description="Filtrar por departamento (código DANE)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Índice de dependencia demográfica.

    FÓRMULA: ((Población <15 años + Población >64) / Población 15-64 años) × 100

    INTERPRETACIÓN:
    - Alto (>60): Gran presión sobre población activa
    - Medio (40-60): Equilibrio relativo
    - Bajo (<40): Poca presión demográfica
    """
    base_conditions = [RegistroCenso2018ORM.p_edadr.isnot(None)]
    
    if departamento:
        base_conditions.append(RegistroCenso2018ORM.u_dpto == departamento)
    
    # Población joven (<15 años) = códigos DANE 1-3 (00-04, 05-09, 10-14)
    poblacion_joven = await db.execute(
        select(func.count()).where(*base_conditions, RegistroCenso2018ORM.p_edadr.in_([1, 2, 3]))
    )
    joven_count = poblacion_joven.scalar() or 0

    # Población adulta mayor (>64 años) = códigos DANE 14-21 (65-69, ..., 100+)
    poblacion_mayor = await db.execute(
        select(func.count()).where(*base_conditions, RegistroCenso2018ORM.p_edadr.in_([14, 15, 16, 17, 18, 19, 20, 21]))
    )
    mayor_count = poblacion_mayor.scalar() or 0

    # Población en edad activa (15-64 años) = códigos DANE 4-13 (15-19, ..., 60-64)
    poblacion_activa = await db.execute(
        select(func.count()).where(*base_conditions, RegistroCenso2018ORM.p_edadr.in_([4, 5, 6, 7, 8, 9, 10, 11, 12, 13]))
    )
    activa_count = poblacion_activa.scalar() or 0
    
    indice = ((joven_count + mayor_count) / activa_count * 100) if activa_count > 0 else None
    
    desglose = {
        "poblacion_joven (<15)": joven_count,
        "poblacion_adulta_mayor (>64)": mayor_count,
        "poblacion_activa (15-64)": activa_count,
        "total_dependiente": joven_count + mayor_count,
    }
    
    if departamento:
        desglose["departamento"] = DEPARTAMENTOS_DANE.get(departamento, f"Depto {departamento}")
    
    return IndiceDemografico(
        nombre="Índice de dependencia demográfica",
        valor=indice or 0,
        descripcion="Relación entre población inactiva y población en edad activa",
        formula="((Población <15 + Población >64) / Población 15-64) × 100",
        desglose=desglose,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Listar registros con paginación
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/registros/",
    summary="Listar registros del Censo 2018",
    description="""
Lista registros individuales del Censo 2018 almacenados en la base de datos, con paginación
y filtros opcionales.

## Parámetros de consulta

| Parámetro | Tipo | Por defecto | Restricción | Descripción |
|-----------|------|-------------|-------------|-------------|
| `skip` | int | 0 | ≥ 0 | Número de registros a omitir (offset de paginación) |
| `limit` | int | 100 | 1 – 1000 | Máximo de registros retornados por página |
| `departamento` | int | (ninguno) | Código DIVIPOLA | Filtra por departamento (5=Antioquia, 11=Bogotá D.C., etc.) |
| `sexo` | int | (ninguno) | 1 o 2 | Filtra por sexo (1=Hombre, 2=Mujer) |

## Paginación

Para recorrer todos los registros use `skip` como cursor:

```
GET /censo-2018/registros/?skip=0&limit=500    ← página 1
GET /censo-2018/registros/?skip=500&limit=500  ← página 2
GET /censo-2018/registros/?skip=1000&limit=500 ← página 3
```

El campo `total` en la respuesta indica cuántos registros coinciden con los filtros,
lo que permite calcular el número total de páginas.

## Campos del response

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `total` | int | Total de registros que coinciden con los filtros (sin paginación) |
| `skip` | int | Offset aplicado |
| `limit` | int | Límite aplicado |
| `registros` | array | Lista de objetos con todos los campos del registro (ver abajo) |

### Estructura de cada registro (`registros[i]`)

Cada objeto incluye todos los campos del modelo `RegistroCenso2018`:
`id`, `u_dpto`, `u_mpio`, `p_sexo`, `p_edadr`, `pa1_grp_etnic`, `p_nivel_anosr`,
`p_estado_civil`, `p_trabajo`, `pa_lo_atendieron`, `pa1_calidad_serv`, `pa_habla_leng`,
`pa1_entiende`, `pb_otras_leng`, `pb1_qotras_leng`, `pa_vivia_1ano`, `archivo_origen`,
`fila_original`, `fecha_carga`.

Los campos opcionales no capturados en el CSV original aparecen como `null`.

## Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Lista retornada (puede ser `registros: []` si no hay datos o los filtros no coinciden) |
| 422 | Parámetro fuera de rango (`sexo` ≠ 1/2, `skip` < 0, `limit` > 1000) |
| 500 | Error en base de datos |
""",
)
async def listar_registros_censo(
    skip: int = Query(0, ge=0, description="Offset de registros"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo registros por página"),
    departamento: Optional[int] = Query(None, description="Filtrar por departamento"),
    sexo: Optional[int] = Query(None, ge=1, le=2, description="Filtrar por sexo"),
    db: AsyncSession = Depends(get_db),
):
    """Lista registros del censo con paginación y filtros opcionales."""
    query = select(RegistroCenso2018ORM)
    
    if departamento:
        query = query.where(RegistroCenso2018ORM.u_dpto == departamento)
    if sexo:
        query = query.where(RegistroCenso2018ORM.p_sexo == sexo)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    registros = result.scalars().all()
    
    # Contar total para paginación
    count_query = select(func.count()).select_from(RegistroCenso2018ORM)
    if departamento:
        count_query = count_query.where(RegistroCenso2018ORM.u_dpto == departamento)
    if sexo:
        count_query = count_query.where(RegistroCenso2018ORM.p_sexo == sexo)
    
    total = (await db.execute(count_query)).scalar()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "registros": [r.to_dict() for r in registros],
    }


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Obtener registro específico
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/registros/{id}/",
    summary="Obtener registro del Censo 2018 por ID",
    description="""
Recupera un único registro del Censo 2018 por su **ID interno** (clave primaria autoincremental
asignada al insertar el registro en la BD).

## Parámetro de ruta

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `id` | int | ID interno del registro (autoasignado en la carga). Empieza en 1. |

El ID **no** corresponde a ningún identificador del DANE — es simplemente el número de fila
en la tabla SQLite. Para descubrir los IDs disponibles use `GET /censo-2018/registros/`.

## Campos del response

El objeto retornado incluye todos los campos del modelo `RegistroCenso2018`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | int | ID interno |
| `u_dpto` | int\|null | Código DIVIPOLA del departamento |
| `u_mpio` | int\|null | Código DIVIPOLA del municipio |
| `p_sexo` | int\|null | 1=Hombre, 2=Mujer |
| `p_edadr` | int\|null | Código de rango etario (1-21, no es edad en años) |
| `pa1_grp_etnic` | int\|null | Código de grupo étnico |
| `p_nivel_anosr` | int\|null | Código de nivel educativo |
| `p_est_civil` | int\|null | Código de estado civil |
| `p_trabajo` | int\|null | Código de situación laboral |
| `pa_lo_atendieron` | int\|null | Atención en salud (1=Sí, 2=No) |
| `pa1_calidad_serv` | int\|null | Calidad del servicio (1=Buena, 2=Regular, 3=Mala) |
| `pa_habla_leng` | int\|null | Habla lengua nativa (1=Sí, 2=No) |
| `pa1_entiende` | int\|null | Entiende lengua nativa (1=Sí, 2=No) |
| `pb_otras_leng` | int\|null | Habla otras lenguas (1=Sí, 2=No) |
| `pb1_qotras_leng` | string\|null | Nombre de la otra lengua (max 100 chars) |
| `pa_vivia_1ano` | int\|null | Código de lugar de residencia hace un año |
| `archivo_origen` | string\|null | Nombre del archivo CSV del que proviene el registro |
| `fila_original` | int\|null | Número de fila en el CSV original |
| `fecha_carga` | string\|null | Timestamp ISO 8601 de cuándo fue insertado |

## Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Registro encontrado y retornado |
| 404 | No existe ningún registro con ese ID. El mensaje sugiere usar `GET /censo-2018/registros/` |
| 422 | El `id` no es un entero válido |
""",
)
async def obtener_registro_censo(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene un registro específico del censo por su ID."""
    result = await db.execute(select(RegistroCenso2018ORM).where(RegistroCenso2018ORM.id == id))
    registro = result.scalar_one_or_none()
    
    if not registro:
        raise HTTPException(
            status_code=404,
            detail=f"Registro con ID {id} no encontrado. Use GET /censo-2018/registros/ para listar."
        )
    
    return registro.to_dict()


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Borrar todos los datos del Censo
# ══════════════════════════════════════════════════════════════════════════════

@router.delete(
    "/borrar-todo/",
    summary="Borrar todos los datos del Censo 2018",
    description="""
Elimina **permanentemente** todos los registros del Censo 2018 de la base de datos.

## ⚠ Advertencia

Esta operación es **irreversible**. No hay papelera de reciclaje ni opción de deshacer.
Una vez ejecutada, los datos solo pueden recuperarse volviendo a cargar el CSV original
con `POST /censo-2018/upload-csv/`.

La operación ejecuta un `DELETE` sin cláusula `WHERE` sobre la tabla completa y hace
`COMMIT` inmediato. El autoincremental de ID **no se reinicia** (SQLite mantiene el
conteo de secuencia internamente); los nuevos registros tras re-cargar seguirán con IDs
mayores al último antes del borrado.

## Comportamiento con BD vacía

Si no hay registros cargados, retorna 200 con `registros_borrados: 0` sin ejecutar el `DELETE`.

## Campos del response

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `mensaje` | string | Confirmación legible. Indica cuántos registros fueron eliminados, o avisa si no había datos. |
| `registros_borrados` | int | Número exacto de registros eliminados (0 si la BD ya estaba vacía) |

## Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Operación completada (exitosa o BD ya vacía) |
| 500 | Error en base de datos durante el borrado |
""",
    response_model=dict,
)
async def borrar_datos_censo(
    db: AsyncSession = Depends(get_db),
):
    """
    Borra todos los registros del Censo 2018 de la base de datos.
    
    ADVERTENCIA: Esta operación es irreversible.
    """
    # Contar registros antes de borrar
    total_result = await db.execute(select(func.count()).select_from(RegistroCenso2018ORM))
    total_registros = total_result.scalar()
    
    if total_registros == 0:
        return {"mensaje": "No hay registros para borrar", "registros_borrados": 0}
    
    # Borrar todos los registros
    await db.execute(RegistroCenso2018ORM.__table__.delete())
    await db.commit()
    
    logger.info(f"CENSO BORRADO | {total_registros} registros eliminados")
    
    return {
        "mensaje": f"Se borraron {total_registros} registros del Censo 2018 exitosamente.",
        "registros_borrados": total_registros,
    }
