from datetime import datetime
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, desc, asc
from pydantic import BaseModel
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Obtener un registro por ID"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc"
    ) -> List[ModelType]:
        """Obtener múltiples registros con paginación y filtros"""
        query = select(self.model)
        
        # Aplicar filtros
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Aplicar ordenamiento
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        
        # Aplicar paginación
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def get_all(self, db: AsyncSession) -> List[ModelType]:
        """Obtener todos los registros sin paginación"""
        result = await db.execute(select(self.model))
        return result.scalars().all()

    async def count(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Contar registros con filtros opcionales"""
        query = select(func.count(self.model.id))
        
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        result = await db.execute(query)
        return result.scalar()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Crear un nuevo registro"""
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """Actualizar un registro existente"""
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType:
        """Eliminar un registro (hard delete)"""
        obj = await self.get(db=db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
 
    async def soft_delete(self, db: AsyncSession, *, id: int, id_persona: int = None) -> Optional[ModelType]:
        """Eliminación suave (actualizar campo activo a 0)"""
        obj = await self.get(db=db, id=id)
        if obj and hasattr(obj, 'activo'):
            setattr(obj, 'activo', 0)
            if id_persona and hasattr(obj, 'id_persona'):
                setattr(obj, 'id_persona', id_persona)
                if hasattr(obj, 'deleted_at'):
                    setattr(obj, 'deleted_at', datetime.now())
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
        return obj

    async def reactivate(self, db: AsyncSession, *, id: int, id_persona: int = None) -> Optional[ModelType]:
        """Reactivar un registro (actualizar campo activo a 1)"""
        obj = await self.get(db=db, id=id)
        if obj and hasattr(obj, 'activo'):
            setattr(obj, 'activo', 1)
            if id_persona and hasattr(obj, 'id_persona'):
                setattr(obj, 'id_persona', id_persona)
                if hasattr(obj, 'updated_at'):
                    setattr(obj, 'updated_at', datetime.now())
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
        return obj

    async def get_active(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Obtener solo registros activos"""
        if hasattr(self.model, 'activo'):
            filters = {"activo": 1}
            return await self.get_multi(db=db, skip=skip, limit=limit, filters=filters)
        else:
            return await self.get_multi(db=db, skip=skip, limit=limit)

    async def search(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str, 
        search_fields: List[str],
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """Buscar registros por término en campos específicos"""
        query = select(self.model)
        
        if search_term and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(
                        getattr(self.model, field).ilike(f"%{search_term}%")
                    )
            
            if search_conditions:
                query = query.where(or_(*search_conditions))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    

    async def count_with_search(
        self,
        db: AsyncSession,
        *,
        search_term: str | None = None,
        search_fields: List[str]
    ) -> int:
        """Contar registros aplicando búsqueda en múltiples campos"""

        query = select(func.count(self.model.id))

        if search_term:
            if isinstance(search_fields, list):
                conditions = [
                    getattr(self.model, field).ilike(f"%{search_term}%")
                    for field in search_fields
                    if hasattr(self.model, field)
                ]

            if conditions:
                query = query.where(or_(*conditions))

        result = await db.execute(query)
        return result.scalar_one()

