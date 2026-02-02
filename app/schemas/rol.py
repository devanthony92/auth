from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime


class RolBase(BaseModel):
    nombre: str
    id_aplicacion: int = 0
    descripcion: Optional[str] = None
    key_publico: Optional[str] = None
    id_persona: Optional[int] = None
    activo: int = 1

    model_config = {
        "extra": "forbid",
    }


class RolCreate(RolBase):
    @field_validator("nombre", "descripcion")
    def validate_nombre(cls, v):
        if v:
            v = v.strip() 
        if v is not None and len(v) <= 3:
            raise ValueError('El nombre debe tener al menos 4 caracteres')
        return v.strip()
    @field_validator('id_aplicacion',"id_persona")
    def validate_id_aplicacion(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El ID debe ser mayor que cero')
        return v


class RolUpdate(RolCreate):
    nombre: Optional[str] = None
    id_aplicacion: Optional[int] = None


class RolInDBBase(RolBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Rol(RolInDBBase):
    pass


class RolResponse(RolInDBBase):
    pass

