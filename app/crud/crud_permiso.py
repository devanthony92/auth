from typing import Optional, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.api import Api
from app.models.permiso import PermisoMenu, PermisoApi
from app.models.menu import Menu
from app.models.rol import Rol
from app.schemas.permiso import PermisoMenuCreate, PermisoMenuUpdate, PermisoApiCreate, PermisoApiUpdate


class CRUDPermisoMenu(CRUDBase[PermisoMenu, PermisoMenuCreate, PermisoMenuUpdate]):
    
    async def get_by_rol_menu(
        self, db: AsyncSession, *, rol_id: int, menu_id: int
    ) -> Optional[PermisoMenu]:
        """Obtener permiso específico de rol-menú"""
        result = await db.execute(
            select(PermisoMenu)
            .where(PermisoMenu.rol_id == rol_id, PermisoMenu.menu_id == menu_id)
        )
        return result.scalar_one_or_none()

    async def get_menus_by_rol(
        self, db: AsyncSession, *, rol_id: int, skip: int = 0, limit: int = 100
    ) -> List[PermisoMenu]:
        """Obtener todos los menús permitidos para un rol"""
        result = await db.execute(
            select(PermisoMenu)
            .options(selectinload(PermisoMenu.menu_obj))
            .where(PermisoMenu.rol_id == rol_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_menus_by_rol_full(
        self, db: AsyncSession, *, rol_id: Sequence[int]
    ) -> List[Menu]:
        """Obtener todos los menús permitidos para un rol"""
        if not rol_id:
            return []
        result = await db.execute(
            select(Menu)
            .join(PermisoMenu, PermisoMenu.menu_id == Menu.id)
            .where(PermisoMenu.rol_id.in_(rol_id), Menu.visible == 1, Menu.activo == 1)
            .order_by(Menu.orden)
        )
        return result.scalars().all()

    async def get_menus(
        self, db: AsyncSession, *, activo: int
    ) -> List[PermisoMenu]:
        """Obtener todos los menús permitidos para un rol"""
        result = await db.execute(
            select(PermisoMenu)
            .options(selectinload(PermisoMenu.menu_obj))
            .where(PermisoMenu.activo == activo)

        )
        return result.scalars().all()

    async def get_roles_by_menu(
        self, db: AsyncSession, *, menu_id: int, skip: int = 0, limit: int = 100
    ) -> List[PermisoMenu]:
        """Obtener todos los roles que tienen acceso a un menú"""
        result = await db.execute(
            select(PermisoMenu)
            .options(selectinload(PermisoMenu.rol_obj))
            .where(PermisoMenu.menu_id == menu_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def remove_by_rol_menu(
        self, db: AsyncSession, *, rol_id: int, menu_id: int
    ) -> bool:
        """Eliminar permiso específico de rol-menú"""
        permiso = await self.get_by_rol_menu(db=db, rol_id=rol_id, menu_id=menu_id)
        if permiso:
            await db.delete(permiso)
            await db.commit()
            return True
        return False

    async def remove_by_rol(
        self, db: AsyncSession, *, rol_id: int
    ) -> bool:
        """Eliminar permiso específico de rol"""
        permisos = await self.get_menus_by_rol(db=db, rol_id=rol_id)
        if permisos:
            for permiso in permisos:
                await db.delete(permiso)
            await db.commit()
            return True
        return False
    
    async def get_menus_by_roles_map(self, db: AsyncSession, roles_ids: list[int]) -> list[Menu]:
        result = await db.execute(
            select(Menu)
            .join(PermisoMenu, PermisoMenu.menu_id == Menu.id)
            .where(PermisoMenu.rol_id.in_(roles_ids))
            .distinct()
            .order_by(Menu.orden)
            )
        
        return result.scalars().all()



class CRUDPermisoApi(CRUDBase[PermisoApi, PermisoApiCreate, PermisoApiUpdate]):
    
    async def get_by_rol_api(
        self, db: AsyncSession, *, rol_id: int, api_id: int
    ) -> Optional[PermisoApi]:
        """Obtener permiso específico de rol-API"""
        result = await db.execute(
            select(PermisoApi)
            .where(PermisoApi.rol_id == rol_id, PermisoApi.api_id == api_id)
        )
        return result.scalar_one_or_none()

    async def get_apis_by_rol(
        self, db: AsyncSession, *, rol_id: int, skip: int = 0, limit: int = 100
    ) -> List[PermisoApi]:
        """Obtener todas las APIs permitidas para un rol"""
        result = await db.execute(
            select(PermisoApi)
            .options(selectinload(PermisoApi.api_obj))
            .where(PermisoApi.rol_id == rol_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_roles_by_api(
        self, db: AsyncSession, *, api_id: int, skip: int = 0, limit: int = 100
    ) -> List[PermisoApi]:
        """Obtener todos los roles que tienen acceso a una API"""
        result = await db.execute(
            select(PermisoApi)
            .options(selectinload(PermisoApi.rol_obj))
            .where(PermisoApi.api_id == api_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def remove_by_rol_api(
        self, db: AsyncSession, *, rol_id: int, api_id: int
    ) -> bool:
        """Eliminar permiso específico de rol-API"""
        permiso = await self.get_by_rol_api(db=db, rol_id=rol_id, api_id=api_id)
        if permiso:
            await db.delete(permiso)
            await db.commit()
            return True
        return False
    
    async def remove_by_rol(
        self, db: AsyncSession, *, rol_id: int
    ) -> bool:
        """Eliminar permiso específico de rol"""
        permisos = await self.get_apis_by_rol(db=db, rol_id=rol_id)
        if permisos:
            for permiso in permisos:
                await db.delete(permiso)
            await db.commit()
            return True
        return False

    async def get_apis_by_roles_map(self, db: AsyncSession, roles_ids: list[int]) -> list[Api]:
        result = await db.execute(
            select(Api)
            .join(PermisoApi, PermisoApi.api_id == Api.id)
            .where(PermisoApi.rol_id.in_(roles_ids))
            .distinct()
            )
        
        return result.scalars().all()


# Instancias de los CRUDs de permisos
permiso_menu = CRUDPermisoMenu(PermisoMenu)
permiso_api = CRUDPermisoApi(PermisoApi)

