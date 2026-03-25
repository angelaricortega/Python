"""
database.py — Configuración de base de datos para el Censo 2018.

Justificación técnica:
─────────────────────────────────────────────────────────────────────────────
El almacenamiento en memoria (dict) no escala para millones de registros.
SQLite (desarrollo) y PostgreSQL (producción) permiten:
- Persistencia de datos después de reiniciar el servidor
- Consultas eficientes con índices en columnas clave
- Procesamiento de grandes volúmenes sin saturar RAM
- Transacciones ACID para integridad de datos

SQLAlchemy 2.0+ con soporte async permite:
- Consultas asíncronas que no bloquean el event loop
- Integración nativa con FastAPI/ASGI
- ORM para mapeo objeto-relacional limpio
─────────────────────────────────────────────────────────────────────────────
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Configuración de la base de datos
# ─────────────────────────────────────────────────────────────────────────────

# SQLite para desarrollo (archivo local)
# En producción cambiar a: postgresql+asyncpg://user:password@localhost/dbname
DATABASE_URL = "sqlite+aiosqlite:///./encuestas_censo.db"


# ─────────────────────────────────────────────────────────────────────────────
# Engine asíncrono
# ─────────────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # True para log de SQL en debug
    future=True,
)

# Session factory asíncrono
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# Base declarativa para modelos ORM
# ─────────────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Funciones de gestión de base de datos
# ─────────────────────────────────────────────────────────────────────────────

async def crear_tablas():
    """
    Crea todas las tablas definidas en los modelos ORM.
    Ejecutar al iniciar la aplicación.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def eliminar_tablas():
    """
    Elimina todas las tablas.
    Útil para testing o reinicio completo.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_db() -> AsyncSession:
    """
    Dependency de FastAPI para obtener sesión de base de datos.
    Uso en endpoints:
    
        @app.get("/ruta/")
        async def mi_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ─────────────────────────────────────────────────────────────────────────────
# Inicialización para pruebas
# ─────────────────────────────────────────────────────────────────────────────

async def inicializar_db_pruebas():
    """
    Inicializa la base de datos para testing.
    Elimina tablas existentes y crea nuevas.
    """
    await eliminar_tablas()
    await crear_tablas()
