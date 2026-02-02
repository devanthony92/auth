import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

def normalize_str(v: Optional[str]) -> Optional[str]:
    return v.strip() if isinstance(v, str) else v

class UpdateProfileRequest(BaseModel):
    """Schema para actualizar datos del perfil"""
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None

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
    
    model_config = {
        "extra": "forbid"
    }


class ChangePasswordRequest(BaseModel):
    """Schema para cambiar contraseña"""
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password", "confirm_password", mode="before")
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


class ProfileResponse(BaseModel):
    """Schema de respuesta del perfil"""
    success: bool
    message: str
    data: Dict[str, Any]
