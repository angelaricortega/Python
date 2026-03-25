"""
models_orm.py — Modelos ORM para Encuestas y Censo 2018.

Contiene:
- EncuestaORM: Versión ORM de EncuestaCompleta (para persistencia)
- RegistroCenso2018ORM: Ya definido en models_censo.py (se reimporta aquí)

Justificación:
─────────────────────────────────────────────────────────────────────────────
Los modelos Pydantic son excelentes para validación de API, pero no para
persistencia en base de datos. SQLAlchemy ORM permite:
- Consultas eficientes con JOINs, filtros y agregaciones
- Transacciones ACID para integridad de datos
- Migraciones y evolución del esquema
─────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


# ══════════════════════════════════════════════════════════════════════════════
# MODELO ORM: EncuestaORM (para encuestas manuales/Google Forms)
# ══════════════════════════════════════════════════════════════════════════════

class EncuestaORM(Base):
    """
    Modelo ORM para encuestas poblacionales (origen: manual, Google Forms, CSV).
    
    Equivalente a EncuestaCompleta de models.py pero para persistencia en DB.
    """
    __tablename__ = "encuestas"
    
    # Clave primaria (UUID como string)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_encuesta_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True, comment="UUID de la encuesta")
    
    # Fecha de registro
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now())
    
    # Datos del encuestado (serializados como JSON en texto)
    encuestado_nombre: Mapped[str] = mapped_column(String(100), index=True)
    encuestado_edad: Mapped[int] = mapped_column(Integer, index=True)
    encuestado_genero: Mapped[str] = mapped_column(String(20), index=True)
    encuestado_estrato: Mapped[int] = mapped_column(Integer, index=True)
    encuestado_departamento: Mapped[str] = mapped_column(String(50), index=True)
    encuestado_municipio: Mapped[str] = mapped_column(String(100))
    encuestado_nivel_educativo: Mapped[str] = mapped_column(String(20))
    encuestado_ocupacion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Respuestas (serializadas como JSON)
    respuestas_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Respuestas en formato JSON")
    
    # Metadatos
    observaciones_generales: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    fuente: Mapped[Optional[str]] = mapped_column(String(50), default="manual", comment="manual, csv_upload, google_forms")
    
    # Timestamps de auditoría
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now())
    actualizado_en: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.now)
    
    def to_dict(self) -> dict:
        """Convierte a diccionario compatible con EncuestaCompleta."""
        import json
        return {
            "id_encuesta": self.id_encuesta_uuid,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "encuestado": {
                "nombre": self.encuestado_nombre,
                "edad": self.encuestado_edad,
                "genero": self.encuestado_genero,
                "estrato": self.encuestado_estrato,
                "departamento": self.encuestado_departamento,
                "municipio": self.encuestado_municipio,
                "nivel_educativo": self.encuestado_nivel_educativo,
                "ocupacion": self.encuestado_ocupacion,
            },
            "respuestas": json.loads(self.respuestas_json) if self.respuestas_json else [],
            "observaciones_generales": self.observaciones_generales,
            "fuente": self.fuente,
        }


# ══════════════════════════════════════════════════════════════════════════════
# Reimportar modelo del Censo 2018
# ══════════════════════════════════════════════════════════════════════════════

from models_censo import RegistroCenso2018ORM

__all__ = ["EncuestaORM", "RegistroCenso2018ORM"]
