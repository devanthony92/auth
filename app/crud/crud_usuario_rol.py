from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.rol import Rol
from app.models.usuario_rol import UsuarioRol
from app.schemas.usuario_rol import UsuarioRolCreate, UsuarioRolUpdate


class CRUDUsuarioRol(CRUDBase[UsuarioRol, UsuarioRolCreate, UsuarioRolUpdate]):
    
    async def get_by_usuario_rol(
        self, db: AsyncSession, *, usuario_id: int, rol_id: int
    ) -> Optional[UsuarioRol]:
        """Obtener relación específica usuario-rol"""
        result = await db.execute(
            select(UsuarioRol)
            .where(UsuarioRol.id_usuario == usuario_id, UsuarioRol.id_rol == rol_id)
        )
        return result.scalar_one_or_none()

    async def get_roles_by_usuario(
        self, db: AsyncSession, *, usuario_id: int, skip: int = 0, limit: int = 100
    ) -> List[UsuarioRol]:
        """Obtener todos los roles de un usuario"""
        result = await db.execute(
            select(UsuarioRol)
            .options(selectinload(UsuarioRol.rol_obj))
            .where(UsuarioRol.id_usuario == usuario_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_usuarios_by_rol(
        self, db: AsyncSession, *, rol_id: int, skip: int = 0, limit: int = 100
    ) -> List[UsuarioRol]:
        """Obtener todos los usuarios con un rol específico"""
        result = await db.execute(
            select(UsuarioRol)
            .options(selectinload(UsuarioRol.usuario))
            .where(UsuarioRol.id_rol == rol_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def remove_by_usuario_rol(
        self, db: AsyncSession, *, usuario_id: int, rol_id: int
    ) -> bool:
        """Eliminar relación específica usuario-rol"""
        usuario_rol = await self.get_by_usuario_rol(
            db=db, usuario_id=usuario_id, rol_id=rol_id
        )
        if usuario_rol:
            await db.delete(usuario_rol)
            await db.commit()
            return True
        return False

    async def remove_all_roles_from_usuario(
        self, db: AsyncSession, *, usuario_id: int
    ) -> bool:
        """Eliminar todas las relaciones de roles de un usuario"""
        usuario_roles = await self.get_roles_by_usuario(db, usuario_id=usuario_id)
        if usuario_roles:
            for usuario_rol in usuario_roles:
                await db.delete(usuario_rol)
            #await db.commit()
            return True
        return False

    async def remove_role_from_usuario(
        self, db: AsyncSession, *, usuario_id: int, rol_id: int
    ) -> bool:
        """Eliminar relación específica usuario-rol"""
        usuario_rol = await self.get_by_usuario_rol(
            db=db, usuario_id=usuario_id, rol_id=rol_id
        )
        if usuario_rol:
            await db.delete(usuario_rol)
            await db.commit()
            return True
        return False

    async def assign_role_to_user(
        self, db: AsyncSession, *, usuario_id: int, rol_id: int, persona_id: int
    ) -> UsuarioRol:
        """Asignar rol a usuario"""
        # Verificar si ya existe la relación
        existing = await self.get_by_usuario_rol(
            db=db, usuario_id=usuario_id, rol_id=rol_id
        )
        if existing:
            return existing
        
        # Crear nueva relación
        usuario_rol_data = UsuarioRolCreate(
            id_usuario=usuario_id,
            id_rol=rol_id,
            id_persona=persona_id
        )
        return await self.create(db=db, obj_in=usuario_rol_data)

    async def get_roles_by_usuarios_map(self, db: AsyncSession, user_ids: list[int]) -> list[tuple[int, Rol]]:
        result = await db.execute(
            select(UsuarioRol.id_usuario, Rol)
            .join(Rol)
            .where(UsuarioRol.id_usuario.in_(user_ids))
        )
        return result.all()
    

# Instancia del CRUD de usuario-rol
usuario_rol = CRUDUsuarioRol(UsuarioRol)

