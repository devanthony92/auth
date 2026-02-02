from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.auth.access_token import AccessTokenService
from app.auth.refresh_tokens import RefreshTokenService
from app.core.database import get_db
from app.crud import usuario as crud_usuario
from app.schemas.usuario import UsuarioLogin, UsuarioResponse
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    set_refresh_token,
    hash_token,
    verify_token_hash
)
from app.auth.user_data import get_user_complete_data, get_user_roles
from app.auth.dependencies import get_current_active_user, verify_refresh_token
from app.models.usuario import Usuario

from app.utils.GeoIp2 import get_session_context
from app.utils.Logs_login_service import LogLoginService

router = APIRouter()



@router.post("/login", response_model=Dict[str, Any], summary ="Iniciar sesión de usuario")
async def login(
    request: Request,
    response: Response,
    user_credentials: UsuarioLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Autenticar usuario y retornar JWT con datos completos
    """
    # Autenticar usuario
    user = await crud_usuario.authenticate(
        db, email=user_credentials.email, password=user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not await crud_usuario.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales incorrectas"
        )
    
    # Obtener datos de la sesion 
    session = get_session_context(request)

    # Obtener roles
    roles_data = await get_user_roles(db, user.id)
    roles = [r["nombre"] for r in roles_data]
    
    # Crear token JWT con todos los datos
    access_token = create_access_token(
        user_id=user.id,
        roles=roles
    )
    refresh_token = create_refresh_token(
        user_id=user.id
    )
    
    try:
        # Guardar access token en BD
        await AccessTokenService.save_access_token(
            db=db,
            user_id=user.id,
            jti=access_token["jti"],
            expires_at=access_token["expires_at"]
        )

        # Revocar cualquier token activo en el mismo dispositivo
        await RefreshTokenService.revoke_refresh_token_by_device(db=db,
                                                            device_id=session.device_id
                                                            )
        # Guardar refresh token en base de datos
        await RefreshTokenService.save_refresh_token(db=db,
                            user_id=user.id,
                            token_jti=refresh_token["jti"],
                            token_hash=hash_token(refresh_token["token"]),
                            expires_at=refresh_token["expires_at"],
                            ip=session.ip,
                            user_agent=session.user_agent,
                            device_id=session.device_id
                            )
            
        # Log de login 
        await LogLoginService.create_log(
            user_id=user.id,
            session_data=session
        )
        
        await db.commit()
    except Exception as e:
        # revierte la transaccion si hay error al guardar el token
        await db.rollback()
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar el refresh token en BD: {e}"
        )

    # Guardar el refresh token en cookies del usuario
    set_refresh_token(response=response, refresh_token=refresh_token["token"])

    return {
        "access_token": access_token["token"],
        "token_type": "Bearer",
    }


@router.post("/refresh", response_model=Dict[str, Any], summary ="Refrescar token de acceso usando el refresh token almacenado en cookies")
async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_token: Dict[str, str] = Depends(verify_refresh_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Refrescar token JWT usando el refresh token 
    Verifica que el token sea válido y genera uno nuevo
    Endpoint consolidado para refresh token
    """
    
    # Extraer datos del token
    user_id = int(refresh_token["payload"].get("sub"))
    token_id = refresh_token["payload"].get("jti")

    # Buscar token en BD
    stored_token = await RefreshTokenService.get_refresh_token_id(db, token_jti=token_id)

    # Validar propietario del token
    if not stored_token or stored_token.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalido")
        
    # Validar hash del refresh token
    if  not verify_token_hash(refresh_token["refresh_token"], stored_token.token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalido")
    
    # Validar si se intenta usar un token revocado
    try:
        if stored_token.is_revoked:
            await RefreshTokenService.revoke_refresh_tokens_by_user(db, user_id=user_id)
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revocado")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al procesar el refresh token")
            

    # Obtener datos de la sesion 
    session = get_session_context(request)

    # Obtener roles
    roles_data = await get_user_roles(db, user_id=user_id)
    roles = [r["nombre"] for r in roles_data]
    
    # Crear token JWT con todos los datos
    access_token = create_access_token(
        user_id=user_id,
        roles=roles
    )

    # Rotar tokens: crea un nuevo refresh token
    new_refresh_token = create_refresh_token(user_id=user_id)

    # Guardar el nuevo refresh token en cookies del usuario
    set_refresh_token(response=response, refresh_token=new_refresh_token["token"])
    
    try:
        # Guardar access token en BD
        await AccessTokenService.save_access_token(
            db=db,
            user_id=user_id,
            jti=access_token["jti"],
            expires_at=access_token["expires_at"]
        )

        # Marca el anterior token como usado
        await RefreshTokenService.revoke_refresh_token(db, stored_token.id)
        
        # Guardar nuevo refresh token en base de datos 
        await RefreshTokenService.save_refresh_token(db=db,
                                user_id= user_id,
                                token_jti=new_refresh_token["jti"],
                                token_hash=hash_token(new_refresh_token["token"]),
                                expires_at=new_refresh_token["expires_at"],
                                ip=session.ip,
                                user_agent=session.user_agent,
                                device_id=session.device_id
                                )
        await db.commit()
    except Exception as e:
        # revierte la transaccion si hay error al guardar el token
        await db.rollback()
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar el refresh token en BD: {e}"
        )
    
    return {
        "access_token": access_token["token"],
        "token_type": "Bearer",
    }


@router.post("/login-form", response_model=Dict[str, Any], summary ="Iniciar sesión de usuario mediante formulario")
async def login_form(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Autenticar usuario usando formulario OAuth2 (para compatibilidad con Swagger)
    """
    # Autenticar usuario (username puede ser email)
    user = await crud_usuario.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        # Intentar con username si no funciona con email
        user_by_username = await crud_usuario.get_by_username(db, username=form_data.username)
        if user_by_username and user_by_username.email:
            user = await crud_usuario.authenticate(
                db, email=user_by_username.email, password=form_data.password
            )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not await crud_usuario.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    # Obtener datos de la sesion 
    session = get_session_context(request)

    # Obtener roles
    roles_data = await get_user_roles(db, user.id)
    roles = [r["nombre"] for r in roles_data]
    
    # Crear token JWT con todos los datos
    access_token = create_access_token(
        user_id=user.id,
        roles=roles
    )
    refresh_token = create_refresh_token(
        user_id=user.id
    )

    # Guardar el refresh token en cookies del usuario
    set_refresh_token(response=response, refresh_token=refresh_token["token"])
    
    try:
        # Guardar access token en BD
        await AccessTokenService.save_access_token(
            db=db,
            user_id=user.id,
            jti=access_token["jti"],
            expires_at=access_token["expires_at"]
        )
        
        # Revocar cualquier token activo en el mismo dispositivo
        await RefreshTokenService.revoke_refresh_token_by_device(db=db,
                                                            device_id=session.device_id
                                                            )
        # Guardar refresh token en base de datos
        await RefreshTokenService.save_refresh_token(db=db,
                            user_id=user.id,
                            token_jti=refresh_token["jti"],
                            token_hash=hash_token(refresh_token["token"]),
                            expires_at=refresh_token["expires_at"],
                            ip=session.ip,
                            user_agent=session.user_agent,
                            device_id=session.device_id
                            )
            
        # Log de login 
        await LogLoginService.create_log(
            user_id=user.id,
            session_data=session
        )
        
        await db.commit()
    except Exception as e:
        # revierte la transaccion si hay error al guardar el token
        await db.rollback()
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar el refresh token en BD: {e}"
        )

    return {
        "access_token": access_token["token"],
        "token_type": "Bearer",
    }


@router.get("/me", response_model=UsuarioResponse, summary ="Obtener información basica del usuario actual")
async def get_current_user_info(
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener datos básicos del usuario actual usando JWT
    """
    return UsuarioResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nombres=current_user.nombres,
        apellidos=current_user.apellidos,
        firma=current_user.firma,
        foto=current_user.foto,
        activo=current_user.activo,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        nombre_completo=current_user.nombre_completo
    )


@router.get("/me/complete", response_model=Dict[str, Any], summary ="Obtener información completa del usuario actual")
async def get_current_user_complete(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener usuario con roles, menús y permisos completos
    """
    user_data = await get_user_complete_data(db, current_user)
    return user_data


@router.get("/logout", summary ="Cerrar sesión del usuario actual")
async def logout(
    response: Response,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para cerrar sesión (logout).
    - Elimina la cookie local.
    - Revoca el refresh token en BD.
    """
    # Eliminar refresh token de las cookies
    response.delete_cookie(
                key="refresh_token",
                path="/api/v1/auth/refresh",
                httponly=True,
                secure=True
            )

    try:
        # Revocar cualquier refresh token activo
        await AccessTokenService.revoke_access_tokens_by_user(db=db, user_id=current_user.id)
        await RefreshTokenService.revoke_refresh_tokens_by_user(db=db, user_id=current_user.id)
        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al cerrar sesión: {e}"
        )

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo completar el cierre de sesión"
        )
    return {"message": "Sesión cerrada correctamente"}
