from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.cuenta_social import CuentaSocial
from app.schemas.cuenta_social import CuentaSocialCreate, CuentaSocialUpdate
from sqlalchemy.future import select


class CRUDCuentaSocial(CRUDBase[CuentaSocial, CuentaSocialCreate, CuentaSocialUpdate]):
    
    async def get_by_proveedor_and_id(
        self, 
        db: AsyncSession, 
        *, 
        proveedor: str, 
        id_usuario_proveedor: str
    ) -> Optional[CuentaSocial]:
        """Obtener cuenta social por proveedor e ID del proveedor"""
        result = await db.execute(
            select(CuentaSocial).where(
                CuentaSocial.proveedor == proveedor,
                CuentaSocial.id_usuario_proveedor == id_usuario_proveedor
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_usuario_and_proveedor(
        self, 
        db: AsyncSession, 
        *, 
        usuario_id: int, 
        proveedor: str
    ) -> Optional[CuentaSocial]:
        """Obtener cuenta social por usuario y proveedor"""
        result = await db.execute(
            select(CuentaSocial).where(
                CuentaSocial.id_persona == usuario_id,
                CuentaSocial.proveedor == proveedor
            )
        )
        return result.scalar_one_or_none()
    
    async def create_or_update_social_account(
        self,
        db: AsyncSession,
        *,
        usuario_id: int,
        proveedor: str,
        id_usuario_proveedor: str,
        correo: str,
        nombre: str
    ) -> CuentaSocial:
        """Crear o actualizar cuenta social"""
        
        # Buscar cuenta existente
        existing_account = await self.get_by_usuario_and_proveedor(
            db, usuario_id=usuario_id, proveedor=proveedor
        )
        
        if existing_account:
            # Actualizar cuenta existente
            update_data = {
                "id_usuario_proveedor": id_usuario_proveedor,
                "correo": correo,
                "nombre": nombre
            }
            return await self.update(db, db_obj=existing_account, obj_in=update_data)
        else:
            # Crear nueva cuenta
            cuenta_data = CuentaSocialCreate(
                id_persona=usuario_id,
                proveedor=proveedor,
                id_usuario_proveedor=id_usuario_proveedor,
                correo=correo,
                nombre=nombre
            )
            return await self.create(db, obj_in=cuenta_data)


# Instancia del CRUD de cuenta social
cuenta_social = CRUDCuentaSocial(CuentaSocial)

