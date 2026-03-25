"""Script para debuggear el endpoint de estadísticas."""
import asyncio
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import AsyncSessionLocal
from models_censo import RegistroCenso2018ORM
from sqlalchemy import select, func

async def test():
    async with AsyncSessionLocal() as session:
        # 1. Contar registros
        result = await session.execute(select(func.count()).select_from(RegistroCenso2018ORM))
        total = result.scalar()
        print(f"1. Total registros: {total}")
        
        # 2. Estadísticas de edad
        result = await session.execute(
            select(func.avg(RegistroCenso2018ORM.p_edadr), func.min(RegistroCenso2018ORM.p_edadr), func.max(RegistroCenso2018ORM.p_edadr))
            .where(RegistroCenso2018ORM.p_edadr.isnot(None))
        )
        print(f"2. Edad stats: {result.one()}")
        
        # 3. Distribución por sexo
        result = await session.execute(
            select(RegistroCenso2018ORM.p_sexo, func.count()).group_by(RegistroCenso2018ORM.p_sexo)
        )
        print(f"3. Sexo: {result.all()}")
        
        # 4. Distribución por departamento
        result = await session.execute(
            select(RegistroCenso2018ORM.u_dpto, func.count()).group_by(RegistroCenso2018ORM.u_dpto)
        )
        print(f"4. Departamento: {result.all()}")
        
        print("\n✓ Todas las consultas funcionaron correctamente")

if __name__ == "__main__":
    asyncio.run(test())
