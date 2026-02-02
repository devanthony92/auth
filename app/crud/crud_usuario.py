from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext
from app.crud.base import CRUDBase
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate

# Configuración para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CRUDUsuario(CRUDBase[Usuario, UsuarioCreate, UsuarioUpdate]):

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        # Truncar la contraseña a 72 bytes para cumplir con la limitación de bcrypt
        password_bytes = plain_password.encode('utf-8')[:72]
        password_truncated = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.verify(password_truncated, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generar hash de contraseña"""
        # Truncar la contraseña a 72 bytes para cumplir con la limitación de bcrypt
        password_bytes = password.encode('utf-8')[:72]
        password_truncated = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.hash(password_truncated)

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[Usuario]:
        """Obtener usuario por email"""
        result = await db.execute(
            select(Usuario).where(Usuario.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[Usuario]:
        """Obtener usuario por username"""
        result = await db.execute(
            select(Usuario).where(Usuario.username == username)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UsuarioCreate) -> Usuario:
        """Crear usuario con hash de contraseña"""
        obj_in_data = obj_in.model_dump()
        if obj_in_data.get("password"):
            hashed_password = self.get_password_hash(obj_in_data.pop("password"))
            obj_in_data["hash_clave"] = hashed_password
        
        db_obj = Usuario(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_password(
        self, db: AsyncSession, *, db_obj: Usuario, new_password: str
    ) -> Usuario:
        """Actualizar contraseña de usuario"""
        hashed_password = self.get_password_hash(new_password)
        db_obj.hash_clave = hashed_password
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[Usuario]:
        """Autenticar usuario"""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not user.hash_clave:
            return None
        if not self.verify_password(password, user.hash_clave):
            return None
        return user

    async def is_active(self, user: Usuario) -> bool:
        """Verificar si el usuario está activo"""
        return user.activo

    async def get_with_roles(self, db: AsyncSession, *, user_id: int) -> Optional[Usuario]:
        """Obtener usuario con sus roles"""
        result = await db.execute(
            select(Usuario)
            .options(
                selectinload(Usuario.usuario_roles).selectinload(UsuarioRol.rol_obj)
            )
            .where(Usuario.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_users_by_role(
        self, db: AsyncSession, *, role_id: int, skip: int = 0, limit: int = 100
    ) -> List[Usuario]:
        """Obtener usuarios por rol"""
        from app.models.usuario_rol import UsuarioRol
        
        result = await db.execute(
            select(Usuario)
            .join(UsuarioRol)
            .where(UsuarioRol.id_rol == role_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search_users(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Usuario]:
        """Buscar usuarios por nombre, apellido, username o email"""
        search_fields = ["nombres", "apellidos", "username", "email"]
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
    ) -> List[Usuario]:
        """Buscar usuarios por nombre, apellido, username o email"""
        search_fields = ["nombres", "apellidos", "username", "email"]
        return await self.count_with_search(
            db=db, 
            search_term=search_term, 
            search_fields=search_fields
        )


# Instancia del CRUD de usuario
usuario = CRUDUsuario(Usuario)

