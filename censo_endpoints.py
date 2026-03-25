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
)

logger = logging.getLogger("censo_api")
router = APIRouter(prefix="/censo-2018", tags=["Censo 2018"])


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Upload masivo de CSV
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/upload-csv/",
    summary="Cargar archivo CSV del Censo 2018 (OPTIMIZADO)",
    description=(
        "Sube un archivo CSV del DANE con datos del Censo 2018. "
        "El procesamiento es batch (de 50,000 en 50,000 registros) para evitar "
        "saturación de memoria. Versión OPTIMIZADA para millones de registros."
    ),
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
    description=(
        "Genera un resumen estadístico completo: conteo total, distribución por "
        "sexo, edad (rangos), departamento, grupo étnico, nivel educativo, estado civil y trabajo."
    ),
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
            distribucion_por_grupo_etnico={},
            distribucion_por_nivel_educativo={},
            distribucion_por_estado_civil={},
            distribucion_por_trabajo={},
            indice_masculinidad=None,
            indice_dependencia=None,
        )

    # IMPORTANTE: p_edadr contiene CÓDIGOS DE RANGO (1-21), NO edades individuales
    # Por lo tanto, NO calculamos promedio/min/max de edad porque no tiene sentido estadístico
    # En su lugar, usamos los códigos directamente para los índices demográficos

    # Mediana de edad (requiere subconsulta)
    # Nota: percentile_cont no está disponible en SQLite, usamos aproximación
    try:
        mediana_result = await db.execute(
            select(func.percentile_cont(0.5).within_group(RegistroCenso2018ORM.p_edadr))
            .where(RegistroCenso2018ORM.p_edadr.isnot(None))
        )
        edad_mediana = mediana_result.scalar() or 0
    except Exception:
        # Fallback para SQLite: calcular mediana manualmente
        edades_result = await db.execute(
            select(RegistroCenso2018ORM.p_edadr)
            .where(RegistroCenso2018ORM.p_edadr.isnot(None))
            .order_by(RegistroCenso2018ORM.p_edadr)
        )
        edades = [e[0] for e in edades_result.all()]
        if edades:
            n = len(edades)
            if n % 2 == 0:
                edad_mediana = (edades[n//2 - 1] + edades[n//2]) / 2
            else:
                edad_mediana = edades[n//2]
        else:
            edad_mediana = 0
    
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
        if codigo == 5:
            distribucion_por_departamento["Antioquia"] = count
        elif codigo == 14:
            distribucion_por_departamento["Cundinamarca"] = count
        elif codigo == 11001:
            distribucion_por_departamento["Bogotá D.C."] = count
        elif codigo and 1 <= codigo <= 32:
            distribucion_por_departamento[f"Depto {codigo}"] = count

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

    return EstadisticasCenso2018(
        total_registros=total_registros,
        distribucion_por_sexo=distribucion_por_sexo,
        distribucion_por_departamento=distribucion_por_departamento,
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
    description=(
        "Calcula el índice de masculinidad: (Hombres / Mujeres) × 100. "
        "Un valor > 100 indica más hombres, < 100 indica más mujeres."
    ),
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
        desglose["departamento"] = obtener_nombre_departamento(departamento)
    
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
    description=(
        "Calcula el índice de dependencia: ((Población <15 + Población >64) / Población 15-64) × 100. "
        "Mide la presión demográfica sobre la población en edad activa."
    ),
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
        from censo_codes import obtener_nombre_departamento
        desglose["departamento"] = obtener_nombre_departamento(departamento)
    
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
    description="Lista registros del censo con paginación. Máximo 1000 registros por página.",
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
    description="Recupera un registro específico por su ID. Retorna 404 si no existe.",
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
    description="Elimina permanentemente todos los registros del censo cargados. Esta operación es irreversible.",
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
