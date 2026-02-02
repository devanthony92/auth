from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.aplicacion import Aplicacion
from app.models.rol import Rol
from app.schemas.rol import RolCreate, RolUpdate


class CRUDRol(CRUDBase[Rol, RolCreate, RolUpdate]):
    
    async def get_by_nombre(self, db: AsyncSession, *, nombre: str) -> Optional[Rol]:
        """Obtener rol por nombre"""
        result = await db.execute(
            select(Rol).where(Rol.nombre == nombre)
        )
        return result.scalar_one_or_none()

    async def get_by_key_publico(self, db: AsyncSession, *, key_publico: str) -> Optional[Rol]:
        """Obtener rol por key_publico"""
        result = await db.execute(
            select(Rol).where(Rol.key_publico == key_publico)
        )
        return result.scalar_one_or_none()

    async def get_roles_by_aplicacion(
        self, db: AsyncSession, *, aplicacion_id: int, skip: int = 0, limit: int = 100
    ) -> List[Rol]:
        """Obtener roles por aplicación"""
        result = await db.execute(
            select(Rol)
            .where(Rol.id_aplicacion == aplicacion_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_permissions(self, db: AsyncSession, *, rol_id: int) -> Optional[Rol]:
        """Obtener rol con sus permisos de menú y API"""
        result = await db.execute(
            select(Rol)
            .options(
                selectinload(Rol.permiso_menus),
                selectinload(Rol.permiso_apis)
            )
            .where(Rol.id == rol_id)
        )
        return result.scalar_one_or_none()

    async def search_roles(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Rol]:
        """Buscar roles por nombre o descripción"""
        search_fields = ["nombre", "descripcion"]
        return await self.search(
            db=db, 
            search_term=search_term, 
            search_fields=search_fields,
            skip=skip, 
            limit=limit
        )

    async def get_aplicaciones_by_roles_map(self, db: AsyncSession, roles_ids: list[int]) -> list[tuple[int, Aplicacion]]:
        result = await db.execute(
            select(Rol.id, Aplicacion)
            .join(Aplicacion, Rol.id_aplicacion == Aplicacion.id)
            .where(Rol.id.in_(roles_ids))
        )
        return result.all()
    
    async def count_search(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str
    ) -> int:
        """Contar roles que coinciden con el término de búsqueda"""
        search_fields = ["nombre", "descripcion"]
        return await self.count_with_search(
            db=db, 
            search_term=search_term, 
            search_fields=search_fields
        )

# Instancia del CRUD de rol
rol = CRUDRol(Rol)

