from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime


class ApiBase(BaseModel):
    grupo: Optional[str] = None
    url_api: str
    id_aplicacion: int
    class_front: Optional[str] = None
    tipo_accion: Optional[int] = None
    nombre: str
    descripcion: Optional[str] = None
    id_persona: Optional[int] = None
    activo: Optional[bool] = None

    model_config = {
        "extra": "forbid",
    }


class ApiCreate(ApiBase):
    @field_validator("url_api", "class_front", "nombre", "descripcion")
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


class ApiUpdate(ApiCreate):
    url_api: Optional[str] = None
    id_aplicacion: Optional[int] = None
    nombre: Optional[str] = None
    

class ApiInDBBase(ApiBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Api(ApiInDBBase):
    pass


class ApiResponse(ApiInDBBase):
    pass