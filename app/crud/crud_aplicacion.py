from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.crud.base import CRUDBase
from app.models.aplicacion import Aplicacion
from app.schemas.aplicacion import AplicacionCreate, AplicacionUpdate


class CRUDAplicacion(CRUDBase[Aplicacion, AplicacionCreate, AplicacionUpdate]):
    
    async def get_by_key(self, db: AsyncSession, *, key: str) -> Optional[Aplicacion]:
        """Obtener aplicación por key"""
        result = await db.execute(
            select(Aplicacion).where(Aplicacion.key == key)
        )
        return result.scalar_one_or_none()

    async def search_aplicaciones(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Aplicacion]:
        """Buscar aplicaciones por nombre o descripción"""
        search_fields = ["nombre", "descripcion"]
        return await self.search(
            db=db, 
            search_term=search_term, 
            search_fields=search_fields,
            skip=skip, 
            limit=limit
        )
    
    async def count_search(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str
    ) -> int:
        """Contar aplicaciones que coinciden con el término de búsqueda"""
        search_fields = ["nombre", "descripcion"]
        return await self.count_with_search(
            db=db, 
            search_term=search_term, 
            search_fields=search_fields
        )


# Instancia del CRUD de aplicación
aplicacion = CRUDAplicacion(Aplicacion)

