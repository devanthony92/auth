from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


# Esquemas para PermisoMenu
class PermisoMenuBase(BaseModel):
    rol_id: int
    menu_id: int
    id_persona: Optional[int] = None

    model_config = {
        "extra": "forbid"
    }

class PermisoMenuCreate(PermisoMenuBase):
    pass

class PermisoMenuUpdate(PermisoMenuCreate):
    pass

class PermisoMenuDelete(PermisoMenuCreate):
    pass

class PermisoMenuCreateMasive(BaseModel):
    rol_id: int
    menu_list: str

class PermisoMenuBulkSave(BaseModel):
    """Schema para guardar permisos masivos de menú"""
    menu_ids: List[int]

class PermisoMenuInDBBase(PermisoMenuBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PermisoMenuResponse(PermisoMenuInDBBase):
    pass


# Esquemas para PermisoApi
class PermisoApiBase(BaseModel):
    api_id: int
    rol_id: int
    id_persona: Optional[int] = None

    model_config = {
        "extra": "forbid"
    }

class PermisoApiCreate(PermisoApiBase):
    pass

class PermisoApiUpdate(PermisoApiCreate):
    pass

class PermisoApiDelete(PermisoApiCreate):
    pass

class PermisoApiBulkSave(BaseModel):
    """Schema para guardar permisos masivos de API"""
    api_ids: List[int]

class PermisoApiInDBBase(PermisoApiBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PermisoApi(PermisoApiInDBBase):
    pass


class PermisoApiResponse(PermisoApiInDBBase):
    pass

