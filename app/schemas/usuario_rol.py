from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from typing import List


class UsuarioRolBase(BaseModel):
    id_usuario: int
    id_rol: int
    id_persona: Optional[int] = None

    model_config = {
        "extra": "forbid"
    }

class UsuarioRolCreate(UsuarioRolBase):
    pass


class UsuarioRolUpdate(UsuarioRolCreate):
    pass


class UsuarioRolInDBBase(UsuarioRolBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsuarioRol(UsuarioRolInDBBase):
    pass


class UsuarioRolResponse(UsuarioRolInDBBase):
    pass


class UsuarioRolListResponse(BaseModel):
    items: List[UsuarioRolResponse]
    total: int
 
    class Config:
        from_attributes = True

class UsuarioRolBulkCreate(BaseModel):
    usuario_roles: str

class UsuarioRolBulkAssignResponse(BaseModel):
    id_usuario: int
    usuario_roles: List[UsuarioRolResponse]

class UsuarioRolBulkAssignRequest(BaseModel):
    id_usuario: int
    usuario_roles: List[int]  # List of role IDs