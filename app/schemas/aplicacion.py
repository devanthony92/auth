from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime


class AplicacionBase(BaseModel):
    key: str
    nombre: str
    activo: int = 1
    descripcion: Optional[str] = None

    model_config = {
        "extra": "forbid"
    }


class AplicacionCreate(AplicacionBase):
    @field_validator("key", "nombre", "descripcion")
    def validate_nombre(cls, v):
        if v:
            v = v.strip() 
        if v is not None and len(v) <= 3:
            raise ValueError('El campo debe tener al menos 4 caracteres')
        return v.strip()


class AplicacionUpdate(AplicacionCreate):
    key: Optional[str] = None
    nombre: Optional[str] = None


class AplicacionInDBBase(AplicacionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Aplicacion(AplicacionInDBBase):
    pass


class AplicacionResponse(AplicacionInDBBase):
    pass

