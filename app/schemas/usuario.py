import re
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

def normalize_str(v: Optional[str]) -> Optional[str]:
    return v.strip() if isinstance(v, str) else v

class UsuarioBase(BaseModel):
    username: str
    email: EmailStr
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    firma: Optional[str] = None
    foto: Optional[str] = None
    activo: int = 1

    model_config = {
        "extra": "forbid"
    }


class UsuarioCreate(UsuarioBase):
    password: str
    
    @field_validator("nombres", "apellidos" , "username", mode="before")
    @classmethod
    def validar_nombres(cls, v):
            v = normalize_str(v)
            if v is not None and len(v) < 3:
                raise ValueError("Debe tener al menos 3 caracteres")
            return v
    
    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, v):
        return normalize_str(v)
    @field_validator("password", mode="before")
    @classmethod
    def validar_password(cls, v):
        if not isinstance(v, str):
            raise ValueError("Contraseña inválida")

        v = v.strip()

        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una mayúscula")

        if not re.search(r"[a-z]", v):
            raise ValueError("Debe contener al menos una minúscula")

        if not re.search(r"\d", v):
            raise ValueError("Debe contener al menos un número")

        return v


class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    firma: Optional[str] = None
    foto: Optional[str] = None
    activo: Optional[int] = None

    model_config = {
        "extra": "forbid"
    }

    @field_validator("nombres", "apellidos", "username", mode="before")
    @classmethod
    def validar_nombres(cls, v):
        v = normalize_str(v)
        if v is not None and len(v) < 3:
            raise ValueError("Debe tener al menos 3 caracteres")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, v):
        return normalize_str(v)


class UsuarioInDBBase(UsuarioBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


class Usuario(UsuarioInDBBase):
    pass


class UsuarioInDB(UsuarioInDBBase):
    hash_clave: Optional[str] = None


class UsuarioResponse(UsuarioInDBBase):
    nombre_completo: Optional[str] = None


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "extra": "forbid"
    }

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, v):
        return normalize_str(v)


class ChangePassword(BaseModel):
    new_password: str

    model_config = {
        "extra": "forbid"
    }




class UsuarioChangePassword(ChangePassword):
    current_password: str
    

class UsuarioChangePasswordAdmin(ChangePassword):
    usuario_id: int
    
    
class PasswordResetConfirmRequest(ChangePassword):
    reset_token: str 