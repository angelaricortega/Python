"""
models_censo.py — Modelos ORM y Pydantic para el Censo 2018 Colombia.

Fuente: DANE - Censo Nacional de Población y Vivienda 2018
Tabla: Individual (Personas)

Variables seleccionadas para el proyecto:
- U_DPTO: Código de departamento (1-32 + Bogotá D.C.)
- U_MPIO: Código de municipio (según codificación DANE)
- P_SEXO: Sexo (1=Hombre, 2=Mujer)
- P_EDADR: Edad en años (0-100+)
- P_NIVEL_ANOSR: Años de educación aprobados (0-11, 99=Ignorado)
- PA1_GRP_ETNIC: Pertenencia étnica (1-6, 9=Ignorado)
- P_ENFERMO: Enfermedad crónica (1=Sí, 2=No, 9=Ignorado)
- P_EST_CIVIL: Estado civil (1-7, 9=Ignorado)
- P_TRABAJO: Situación laboral (0-9)
- P_ALFABETA: Alfabetismo (1=Sí, 2=No, 9=Ignorado)
- PA_ASISTENCIA: Asistencia educativa (1=Sí, 2=No, 9=Ignorado)

Arquitectura:
- Modelo ORM (SQLAlchemy): Para persistencia en base de datos
- Modelo Pydantic: Para validación de API
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import Column, Integer, String, Date, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Annotated

from database import Base


# ══════════════════════════════════════════════════════════════════════════════
# MODELO ORM: RegistroCenso2018 (SQLAlchemy)
# Para persistencia en base de datos
# ══════════════════════════════════════════════════════════════════════════════

class RegistroCenso2018ORM(Base):
    """
    Modelo ORM para registros individuales del Censo 2018.
    
    Diseñado para millones de registros con índices en columnas de consulta frecuente.
    """
    __tablename__ = "censo_2018_registros"
    
    # Clave primaria
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identificadores geográficos (índices para consultas por región)
    tipo_reg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Tipo de registro (5=Persona)")
    u_dpto: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Código departamento DANE")
    u_mpio: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Código municipio DANE")
    ua_clase: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Clase de área")
    cod_encuestas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    u_vivienda: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    p_nrohog: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Número de hogar")
    p_nro_per: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Número de persona en hogar")
    
    # Variables demográficas principales (índices para análisis)
    p_sexo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Sexo (1=Hombre, 2=Mujer)")
    p_edadr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Edad en años")
    p_parentescor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Parentesco")
    
    # Variables étnicas
    pa1_grp_etnic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Grupo étnico")
    pa11_cod_etnia: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa12_clan: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Variables de salud y discapacidad
    p_enfermo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Enfermedad crónica")
    condicion_fisica: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Variables educativas
    p_alfabeta: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Alfabetismo")
    pa_asistencia: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Asistencia educativa")
    p_nivel_anosr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Años educación aprobados")
    
    # Variables laborales y estado civil
    p_trabajo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Situación laboral")
    p_est_civil: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="Estado civil")
    
    # Variables de fecundidad (para mujeres en edad fértil)
    pa_hnv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa1_thnv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa2_hnvh: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa3_hnvm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa_hnvs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa1_thsv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa2_hsvh: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa3_hsvm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa_hfc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa1_thfc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa2_hfch: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa3_hfcm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa_uhnv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa1_mes_uhnv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa2_ano_uhnv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Variables de nacimiento y migración
    pa_lug_nac: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa_vivia_5anos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa_vivia_1ano: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Variables de atención en salud
    pa_lo_atendieron: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa1_calidad_serv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Variables de lenguaje (población étnica)
    pa_habla_leng: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pa1_entiende: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pb_otras_leng: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pb1_qotras_leng: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Metadatos de carga
    fecha_carga: Mapped[datetime] = mapped_column(default=datetime.now, comment="Fecha de carga del registro")
    archivo_origen: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Archivo CSV de origen")
    fila_original: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Fila en archivo original")
    
    # Índices compuestos para consultas frecuentes
    __table_args__ = (
        Index('idx_dpto_edad', 'u_dpto', 'p_edadr'),
        Index('idx_dpto_sexo', 'u_dpto', 'p_sexo'),
        Index('idx_dpto_etnia', 'u_dpto', 'pa1_grp_etnic'),
        Index('idx_edad_sexo', 'p_edadr', 'p_sexo'),
    )
    
    def to_dict(self) -> dict:
        """Convierte el registro ORM a diccionario."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ══════════════════════════════════════════════════════════════════════════════
# MODELOS PYDANTIC: Para validación de API
# ══════════════════════════════════════════════════════════════════════════════

class RegistroCenso2018Base(BaseModel):
    """
    Modelo base Pydantic para validación de registros del Censo 2018.
    
    Valida códigos oficiales DANE y coherencia de variables demográficas.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo_reg": 5,
                "u_dpto": 5,
                "u_mpio": 1,
                "p_sexo": 1,
                "p_edadr": 35,
                "pa1_grp_etnic": 5,
                "p_enfermo": 2,
                "p_est_civil": 2,
                "p_trabajo": 1,
                "p_alfabeta": 1,
                "pa_asistencia": 2,
                "p_nivel_anosr": 10,
            }
        }
    )
    
    # Identificadores geográficos
    tipo_reg: Optional[int] = Field(default=5, description="Tipo de registro (5=Persona)")
    u_dpto: Optional[int] = Field(default=None, ge=1, le=99, description="Código departamento DANE (1-32)")
    u_mpio: Optional[int] = Field(default=None, ge=0, le=9999, description="Código municipio DANE")
    ua_clase: Optional[int] = Field(default=None, description="Clase de área")
    
    # Variables demográficas principales
    p_sexo: Optional[int] = Field(default=None, ge=1, le=2, description="Sexo (1=Hombre, 2=Mujer)")
    p_edadr: Optional[int] = Field(default=None, ge=0, le=120, description="Edad en años (0-120)")
    p_parentescor: Optional[int] = Field(default=None, description="Parentesco")
    
    # Variables étnicas
    pa1_grp_etnic: Optional[int] = Field(default=None, ge=1, le=9, description="Grupo étnico (1-6, 9=Ignorado)")
    pa11_cod_etnia: Optional[int] = Field(default=None, description="Código de etnia específico")
    pa12_clan: Optional[str] = Field(default=None, max_length=50, description="Clan (población indígena)")
    
    # Variables de salud
    p_enfermo: Optional[int] = Field(default=None, ge=1, le=9, description="Enfermedad crónica (1=Sí, 2=No, 9=Ignorado)")
    condicion_fisica: Optional[int] = Field(default=None, description="Condición física")
    
    # Variables educativas
    p_alfabeta: Optional[int] = Field(default=None, ge=1, le=9, description="Alfabetismo (1=Sí, 2=No, 9=Ignorado)")
    pa_asistencia: Optional[int] = Field(default=None, ge=1, le=9, description="Asistencia educativa")
    p_nivel_anosr: Optional[int] = Field(default=None, ge=0, le=99, description="Años de educación aprobados")
    
    # Variables laborales y estado civil
    p_trabajo: Optional[int] = Field(default=None, ge=0, le=9, description="Situación laboral")
    p_est_civil: Optional[int] = Field(default=None, ge=1, le=9, description="Estado civil")
    
    # Variables de fecundidad (opcionales, solo mujeres 12-49 años)
    pa_hnv: Optional[int] = Field(default=None, description="Hijos nacidos vivos")
    pa1_thnv: Optional[int] = Field(default=None, description="Total hijos nacidos vivos")
    pa2_hnvh: Optional[int] = Field(default=None, description="Hijos nacidos vivos hombres")
    pa3_hnvm: Optional[int] = Field(default=None, description="Hijos nacidos vivos mujeres")
    pa_hnvs: Optional[int] = Field(default=None, description="Hijos nacidos vivos que sobreviven")
    pa1_thsv: Optional[int] = Field(default=None, description="Total hijos que sobreviven")
    pa2_hsvh: Optional[int] = Field(default=None, description="Hijos que sobreviven hombres")
    pa3_hsvm: Optional[int] = Field(default=None, description="Hijos que sobreviven mujeres")
    pa_hfc: Optional[int] = Field(default=None, description="Hijos del cónyuge")
    pa1_thfc: Optional[int] = Field(default=None, description="Total hijos del cónyuge")
    pa2_hfch: Optional[int] = Field(default=None, description="Hijos del cónyuge hombres")
    pa3_hfcm: Optional[int] = Field(default=None, description="Hijos del cónyuge mujeres")
    pa_uhnv: Optional[int] = Field(default=None, description="Último hijo nacido vivo")
    pa1_mes_uhnv: Optional[int] = Field(default=None, description="Mes último hijo nacido")
    pa2_ano_uhnv: Optional[int] = Field(default=None, description="Año último hijo nacido")
    
    # Migración
    pa_lug_nac: Optional[int] = Field(default=None, description="Lugar de nacimiento")
    pa_vivia_5anos: Optional[int] = Field(default=None, description="Dónde vivía hace 5 años")
    pa_vivia_1ano: Optional[int] = Field(default=None, description="Dónde vivía hace 1 año")
    
    # Atención en salud
    pa_lo_atendieron: Optional[int] = Field(default=None, description="Fue atendido en parto")
    pa1_calidad_serv: Optional[int] = Field(default=None, description="Calidad del servicio")
    
    # Lenguaje
    pa_habla_leng: Optional[int] = Field(default=None, description="Habla lengua indígena")
    pa1_entiende: Optional[int] = Field(default=None, description="Entiende lengua indígena")
    pb_otras_leng: Optional[int] = Field(default=None, description="Otras lenguas")
    pb1_qotras_leng: Optional[str] = Field(default=None, max_length=100, description="Qué otras lenguas")
    
    @field_validator("p_sexo", mode="after")
    @classmethod
    def validar_sexo(cls, v: Optional[int]) -> Optional[int]:
        """Valida que el sexo sea un código válido del DANE."""
        from censo_codes import SEXO
        if v is not None and v not in SEXO:
            raise ValueError(
                f"Sexo inválido: {v}. Códigos válidos DANE: {SEXO}"
            )
        return v
    
    @field_validator("pa1_grp_etnic", mode="after")
    @classmethod
    def validar_grupo_etnico(cls, v: Optional[int]) -> Optional[int]:
        """Valida que el grupo étnico sea un código válido del DANE."""
        from censo_codes import GRUPO_ETNICO
        if v is not None and v not in GRUPO_ETNICO:
            raise ValueError(
                f"Grupo étnico inválido: {v}. Códigos válidos: {GRUPO_ETNICO}"
            )
        return v
    
    @field_validator("p_est_civil", mode="after")
    @classmethod
    def validar_estado_civil(cls, v: Optional[int]) -> Optional[int]:
        """Valida que el estado civil sea un código válido del DANE."""
        from censo_codes import ESTADO_CIVIL
        if v is not None and v not in ESTADO_CIVIL:
            raise ValueError(
                f"Estado civil inválido: {v}. Códigos válidos: {ESTADO_CIVIL}"
            )
        return v
    
    @field_validator("p_trabajo", mode="after")
    @classmethod
    def validar_trabajo(cls, v: Optional[int]) -> Optional[int]:
        """Valida que la situación laboral sea un código válido del DANE."""
        from censo_codes import TRABAJO
        if v is not None and v not in TRABAJO:
            raise ValueError(
                f"Situación laboral inválida: {v}. Códigos válidos: {TRABAJO}"
            )
        return v
    
    @field_validator("p_alfabeta", "pa_asistencia", "p_enfermo", mode="after")
    @classmethod
    def validar_binario_mas_ignorado(cls, v: Optional[int], info) -> Optional[int]:
        """Valida variables binarias con opción 'Ignorado' (1=Sí, 2=No, 9=Ignorado)."""
        if v is not None and v not in (1, 2, 9):
            raise ValueError(
                f"{info.field_name} inválido: {v}. Valores válidos: 1=Sí, 2=No, 9=Ignorado"
            )
        return v
    
    @field_validator("p_edadr", mode="after")
    @classmethod
    def validar_edad_censo(cls, v: Optional[int]) -> Optional[int]:
        """Valida edad en rango biológico razonable para censo."""
        if v is not None and not (0 <= v <= 120):
            raise ValueError(
                f"Edad inválida: {v}. Rango aceptado: 0-120 años (restricción biológica)"
            )
        return v
    
    @field_validator("p_nivel_anosr", mode="after")
    @classmethod
    def validar_nivel_educativo(cls, v: Optional[int]) -> Optional[int]:
        """Valida años de educación aprobados."""
        if v is not None and v not in list(range(0, 12)) + [99]:
            raise ValueError(
                f"Nivel educativo inválido: {v}. "
                f"Valores válidos: 0-11 (años aprobados), 99 (Ignorado)"
            )
        return v
    
    @model_validator(mode="after")
    def validar_coherencia_demografica(self) -> "RegistroCenso2018Base":
        """
        Validaciones cruzadas de coherencia demográfica.
        
        Reglas:
        - Menores de 12 años no deberían tener estado civil de casado/unido
        - Menores de 5 años no deberían tener variables de trabajo/educación
        - Variables de fecundidad solo aplican a mujeres 12-49 años
        """
        edad = self.p_edadr
        sexo = self.p_sexo
        estado_civil = self.p_est_civil
        trabajo = self.p_trabajo
        
        # Coherencia estado civil - edad
        if edad is not None and edad < 12 and estado_civil is not None:
            if estado_civil in (2, 3):  # Casado o Unido
                # No es válido pero no rechazamos, solo es data quality issue
                pass
        
        # Coherencia fecundidad - sexo y edad
        if sexo == 1:  # Hombre
            # Limpiar variables de fecundidad para hombres (no aplican)
            for field in ['pa_hnv', 'pa1_thnv', 'pa2_hnvh', 'pa3_hnvm', 
                         'pa_hnvs', 'pa1_thsv', 'pa2_hsvh', 'pa3_hsvm',
                         'pa_hfc', 'pa1_thfc', 'pa2_hfch', 'pa3_hfcm',
                         'pa_uhnv', 'pa1_mes_uhnv', 'pa2_ano_uhnv']:
                if getattr(self, field) is not None:
                    setattr(self, field, None)
        
        if edad is not None and (edad < 12 or edad > 49):
            # Fuera de edad fértil, limpiar variables de fecundidad
            for field in ['pa_hnv', 'pa1_thnv', 'pa2_hnvh', 'pa3_hnvm',
                         'pa_hnvs', 'pa1_thsv', 'pa2_hsvh', 'pa3_hsvm',
                         'pa_hfc', 'pa1_thfc', 'pa2_hfch', 'pa3_hfcm',
                         'pa_uhnv', 'pa1_mes_uhnv', 'pa2_ano_uhnv']:
                if getattr(self, field) is not None:
                    setattr(self, field, None)
        
        return self


class RegistroCenso2018Create(RegistroCenso2018Base):
    """Modelo para crear registros (incluye metadatos de carga)."""
    archivo_origen: Optional[str] = Field(default=None, max_length=255)
    fila_original: Optional[int] = Field(default=None, ge=1)


class RegistroCenso2018Response(RegistroCenso2018Base):
    """Modelo para respuestas de API (incluye ID y metadatos)."""
    id: int
    fecha_carga: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════════════════════
# MODELOS PARA ESTADÍSTICAS Y ANÁLISIS
# ══════════════════════════════════════════════════════════════════════════════

class EstadisticasCenso2018(BaseModel):
    """
    Resumen estadístico del Censo 2018.

    Incluye distribuciones por todas las variables principales.
    
    NOTA SOBRE EDAD: El Censo 2018 usa RANGOS ESTÁRIOS (códigos 1-21).
    NO se reportan edades individuales porque no existen en los datos.
    Se muestran grupos de edad amplios para análisis demográfico.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_registros": 6147091,
                "distribucion_por_sexo": {"Hombre": 3050000, "Mujer": 3097091},
                "distribucion_por_departamento": {"Antioquia": 6147091},
                "distribucion_por_grupo_etnico": {
                    "Ninguno de los anteriores": 5500000,
                    "Negro(a), Mulato(a), Afrocolombiano(a)": 500000,
                    "Indígena": 147091
                },
                "distribucion_por_grupos_edad": {
                    "Primera infancia (0-9 años)": 1020000,
                    "Niñez (10-14 años)": 510000,
                    "Adolescencia (15-19 años)": 480000,
                    "Juventud (20-29 años)": 950000,
                    "Adultez temprana (30-44 años)": 1400000,
                    "Adultez media (45-59 años)": 1100000,
                    "Adultez mayor (60-74 años)": 500000,
                    "Vejez (75+ años)": 187091,
                },
                "indice_masculinidad": 98.5,
                "indice_dependencia": 52.3,
            }
        }
    )

    total_registros: int = Field(description="Total de registros en el censo")

    distribucion_por_sexo: Dict[str, int] = Field(description="Distribución por sexo")
    distribucion_por_departamento: Dict[str, int] = Field(description="Distribución por departamento")
    distribucion_por_municipio: Optional[Dict[str, int]] = Field(
        default=None,
        description="Top 15 municipios por población, cruzados con catálogo DIVIPOLA"
    )
    distribucion_por_grupo_etnico: Dict[str, int] = Field(description="Distribución por grupo étnico")
    distribucion_por_nivel_educativo: Dict[str, int] = Field(description="Distribución por nivel educativo")
    distribucion_por_estado_civil: Dict[str, int] = Field(description="Distribución por estado civil")
    distribucion_por_trabajo: Dict[str, int] = Field(description="Distribución por situación laboral")
    
    # Distribución por grupos de edad amplios
    distribucion_por_grupos_edad: Optional[Dict[str, int]] = Field(
        default=None,
        description="Distribución por grupos de edad amplios (ej: 'Primera infancia (0-9 años)': 1020000)"
    )

    # Distribución por rangos etarios detallados (19-21 rangos del DANE)
    distribucion_por_rangos_edad: Optional[Dict[str, int]] = Field(
        default=None,
        description="Distribución por rangos etarios detallados del DANE (ej: '00-04 años': 500000)"
    )

    indice_masculinidad: Optional[float] = Field(default=None, description="Índice de masculinidad (H/M × 100)")
    indice_dependencia: Optional[float] = Field(default=None, description="Índice de dependencia demográfica")


class IndiceDemografico(BaseModel):
    """Modelo para índices demográficos específicos."""
    nombre: str
    valor: float
    descripcion: str
    formula: str
    desglose: Optional[Dict[str, float]] = Field(default=None, description="Desglose por categorías")
