from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime


class MenuBase(BaseModel):
    url_menu: str
    id_aplicacion: int = 0
    padre: Optional[int] = None
    nombre: str
    ruta_front: Optional[str] = None
    orden: Optional[int] = 0
    visible: Optional[int] = 1
    acceso: Optional[int] = 1
    icono: Optional[str] = None
    target: Optional[str] = None
    activo: Optional[int] = 1
    descripcion: Optional[str] = None
    id_persona: Optional[int] = None

    model_config = {
        "extra": "forbid",
    }


class MenuCreate(MenuBase):
    @field_validator("nombre", "descripcion", "url_menu", "ruta_front", "icono", "target")
    def validate_str_input(cls, v):
        if v:
            v = v.strip() 
        if v is not None and len(v) <= 3:
            raise ValueError('El campo debe tener al menos 4 caracteres')
        return v.strip()
    @field_validator('id_aplicacion',"id_persona","padre")
    def validate_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El ID debe ser mayor que cero')
        return v


class MenuUpdate(MenuCreate):
    url_menu: Optional[str] = None
    id_aplicacion: Optional[int] = None
    nombre: Optional[str] = None



class MenuInDBBase(MenuBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Menu(MenuInDBBase):
    pass


class MenuResponse(MenuInDBBase):
    
    @field_validator('padre', mode='before')
    @classmethod
    def convert_padre_to_int(cls, v):
        """Convertir padre a int si viene como string"""
        if v is not None and isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return v


class MenuHierarchy(MenuInDBBase):
    children: Optional[list["MenuHierarchy"]] = []

class UpdatePermisos(BaseModel):
    menu_list: str
    rol: int