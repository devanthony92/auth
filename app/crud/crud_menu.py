from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate


class CRUDMenu(CRUDBase[Menu, MenuCreate, MenuUpdate]):
    
    async def get_by_url(self, db: AsyncSession, *, url_menu: str) -> Optional[Menu]:
        """Obtener menú por URL"""
        result = await db.execute(
            select(Menu).where(Menu.url_menu == url_menu)
        )
        return result.scalar_one_or_none()

    async def get_menus_by_aplicacion(
        self, db: AsyncSession, *, aplicacion_id: int, skip: int = 0, limit: int = 100
    ) -> List[Menu]:
        """Obtener menús por aplicación"""
        result = await db.execute(
            select(Menu)
            .where(Menu.id_aplicacion == aplicacion_id)
            .order_by(Menu.orden)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_menus_by_padre(
        self, db: AsyncSession, *, padre: str, skip: int = 0, limit: int = 100
    ) -> List[Menu]:
        """Obtener menús hijos por padre"""
        result = await db.execute(
            select(Menu)
            .where(Menu.padre == padre)
            .order_by(Menu.orden)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_visible_menus(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Menu]:
        """Obtener menús visibles"""
        result = await db.execute(
            select(Menu)
            .where(Menu.visible == 1)
            .order_by(Menu.orden)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_activo_menus_all(
        self, db: AsyncSession, *, activo: int = 1
    ) -> List[Menu]:
        """Obtener menús activos"""
        result = await db.execute(
            select(Menu)
            .where(Menu.activo == activo)
            .order_by(Menu.orden)
        )
        return result.scalars().all()

    async def get_activo_menus(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Menu]:
        """Obtener menús activos"""
        result = await db.execute(
            select(Menu)
            .where(Menu.activo == 1)
            .order_by(Menu.orden)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_menu_hierarchy(
        self, db: AsyncSession, *, aplicacion_id: Optional[int] = None
    ) -> List[Menu]:
        """Obtener jerarquía completa de menús"""
        query = select(Menu).order_by(Menu.orden, Menu.id)
        
        if aplicacion_id:
            query = query.where(Menu.id_aplicacion == aplicacion_id)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def search_menus(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Menu]:
        """Buscar menús por nombre o descripción"""
        search_fields = ["nombre", "descripcion", "url_menu"]
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
    ) -> List[Menu]:
        """Contar menús que coinciden con la búsqueda por nombre o descripción"""
        search_fields = ["nombre", "descripcion", "url_menu"]
        return await self.count_with_search(
            db=db, 
            search_term=search_term, 
            search_fields=search_fields
        )


# Instancia del CRUD de menú
menu = CRUDMenu(Menu)