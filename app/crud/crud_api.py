from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.crud.base import CRUDBase
from app.models.api import Api
from app.schemas.api import ApiCreate, ApiUpdate


class CRUDApi(CRUDBase[Api, ApiCreate, ApiUpdate]):
    
    async def get_by_url(self, db: AsyncSession, *, url_api: str) -> Optional[Api]:
        """Obtener API por URL"""
        result = await db.execute(
            select(Api).where(Api.url_api == url_api)
        )
        return result.scalar_one_or_none()

    async def get_apis_by_aplicacion(
        self, db: AsyncSession, *, aplicacion_id: int, skip: int = 0, limit: int = 100
    ) -> List[Api]:
        """Obtener APIs por aplicación"""
        result = await db.execute(
            select(Api)
            .where(Api.id_aplicacion == aplicacion_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_apis_by_grupo(
        self, db: AsyncSession, *, grupo: str, skip: int = 0, limit: int = 100
    ) -> List[Api]:
        """Obtener APIs por grupo"""
        result = await db.execute(
            select(Api)
            .where(Api.grupo == grupo)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_apis_by_tipo_accion(
        self, db: AsyncSession, *, tipo_accion: int, skip: int = 0, limit: int = 100
    ) -> List[Api]:
        """Obtener APIs por tipo de acción"""
        result = await db.execute(
            select(Api)
            .where(Api.tipo_accion == tipo_accion)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search_apis(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Api]:
        """Buscar APIs por nombre, descripción o URL"""
        search_fields = ["nombre", "descripcion", "url_api", "grupo"]
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
        """Contar APIs que coinciden con el término de búsqueda"""
        search_fields = ["nombre", "descripcion", "url_api", "grupo"]
        return await self.count_with_search(
            db=db, 
            search_term=search_term, 
            search_fields=search_fields
        )


# Instancia del CRUD de API
api = CRUDApi(Api)

