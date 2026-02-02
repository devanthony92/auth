from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class CuentaSocialBase(BaseModel):
    id_persona: int
    proveedor: str
    id_usuario_proveedor: str
    token_proveedor: Optional[str] = None
    correo: Optional[EmailStr] = None
    nombre: Optional[str] = None


class CuentaSocialCreate(CuentaSocialBase):
    pass


class CuentaSocialUpdate(BaseModel):
    id_persona: Optional[int] = None
    proveedor: Optional[str] = None
    id_usuario_proveedor: Optional[str] = None
    token_proveedor: Optional[str] = None
    correo: Optional[EmailStr] = None
    nombre: Optional[str] = None


class CuentaSocialInDBBase(CuentaSocialBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CuentaSocial(CuentaSocialInDBBase):
    pass


class CuentaSocialResponse(CuentaSocialInDBBase):
    pass

class GoogleUser(BaseModel):
    id: str
    email: EmailStr
    verified_email: bool
    name: str
    given_name: str
    family_name: str
    picture: Optional[str] = None
    locale: Optional[str] = None
