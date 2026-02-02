"""
Router para registro público de usuarios y recuperación de contraseña
Autor: Fabio Garcia
Fecha: 2025-11-27
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_password_hash
from app.crud import usuario as crud_usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import json
import httpx
from app.auth.password_reset import PasswordResetService
from app.services.notificaciones import NotificationService
from app.utils.GeoIp2 import get_session_context

router = APIRouter()


class RegisterRequest(BaseModel):
    """Schema para registro de usuario"""
    username: str
    email: EmailStr
    password: str
    nombres: str
    apellidos: str


class ForgotPasswordRequest(BaseModel):
    """Schema para solicitud de recuperación de contraseña"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema para resetear contraseña"""
    email: EmailStr
    token: str
    new_password: str


class RegisterResponse(BaseModel):
    """Schema de respuesta de registro"""
    success: bool
    message: str
    data: Dict[str, Any]

class PasswordResetConfirmRequest(BaseModel):
    new_password: str
    reset_token: str

    model_config = {
        "extra": "forbid"
    }

@router.post("/registro", response_model=RegisterResponse, summary ="Registrar nuevo usuario")
async def register_user(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema
    """
    try:
        # Verificar si el email ya existe
        existing_user = await crud_usuario.get_by_email(db, email=user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Verificar si el username ya existe
        existing_username = await crud_usuario.get_by_username(db, username=user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso"
            )
        
        # Validar longitud de contraseña
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 8 caracteres"
            )
        
        # Crear usuario
        user_create = UsuarioCreate(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            nombres=user_data.nombres,
            apellidos=user_data.apellidos,
            activo=True
        )
        
        new_user = await crud_usuario.create(db, obj_in=user_create)
        
        return RegisterResponse(
            success=True,
            message="Usuario registrado correctamente",
            data={
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "nombres": new_user.nombres,
                "apellidos": new_user.apellidos
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )


@router.post("/recuperar-contrasena", response_model=RegisterResponse, summary="Iniciar recuperación de contraseña")
async def forget_password(
    email: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
    ):
    """
    Iniciar proceso de recuperación de contraseña
    """
    user = await crud_usuario.get_by_email(db=db, email=email)
    # Obtener datos de la sesion 
    session = get_session_context(request)

    if user:
        token = await PasswordResetService.request_reset_token(
            db=db,
            user_id=user.id,
            ip=session.ip,
            user_agent=session.user_agent
        )
    
        payload = {
            "account_id": 2,
            "template_id": 1,
            "subject": "Restablecimiento de contraseña",
            "to": [f"{user.email}"],
            "cc": [],
            "bcc": [],
            "variables": {
                            "user_name": f"{user.nombres} {user.apellidos}",
                            "reset_link": f"https://example.com/reset-password?token={token['token']}",
                            "expiration_time": f"{token['expires_at']} minutos",
                            "recovery_code": "123456",
                            "support_link": "https://example.com/support"
                        }
        }

        try:
            await NotificationService.send_email(payload)
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except json.JSONDecodeError:
                detail = e.response.text or "Error en servicio externo"

            raise HTTPException(
                status_code=e.response.status_code,
                detail=detail,
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="Servicio de correo no disponible",
            )
    return RegisterResponse(
            success=True,
            message="Siga las instrucciones en su correo electrónico para restablecer la contraseña",
            data={
                "email": email
            }
        )


@router.post("/resetear-contrasena", response_model=RegisterResponse)
async def reset_password(
    payload: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await PasswordResetService.confirm_reset(db=db, token=payload.reset_token, new_password=payload.new_password)

    return RegisterResponse(
            success=True,
            message=f"Contraseña asociada al usuario {result.username} actualizada correctamente",
            data={
                "email": result.email
            }
        )


