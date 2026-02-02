"""
Endpoints de autenticación con Gmail OAuth2
Autor: Manus AI (@Fabio Garcia)
Fecha: 2025-01-18
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, status, Depends, Response, Query
from fastapi.responses import RedirectResponse
import httpx
import urllib.parse
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.access_token import AccessTokenService
from app.core.database import get_db
from app.crud import usuario as crud_usuario
from app.crud.crud_cuenta_social import cuenta_social as crud_cuenta_social
from app.schemas.usuario import UsuarioCreate
from app.schemas.cuenta_social import GoogleUser
from app.auth.gmail_oauth import gmail_oauth
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    set_refresh_token,
    hash_token
)
from app.auth.user_data import get_user_complete_data, get_user_roles
from app.auth.dependencies import get_current_active_user
from app.auth.refresh_tokens import RefreshTokenService
import secrets
import uuid
from app.core.config import settings
from app.utils.Logs_login_service import LogLoginService
from app.utils.GeoIp2 import get_session_context
from datetime import datetime, timezone

router = APIRouter()


@router.get("/google")
def google_login(response: Response):
    """
    Iniciar proceso de autenticación con Gmail
    
    Retorna:
        - authorization_url: URL para redirigir al usuario a Gmail
        - state: Token de estado para validar el callback
    """

    # Generar estado único para prevenir CSRF
    state = secrets.token_urlsafe(32)
    
    params = {
        "client_id": settings.gmail_client_id,
        "redirect_uri": settings.gmail_redirect_uri,
        "response_type": "code",
        "scope": "email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state
    }

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    response = RedirectResponse(url)

    # Guardar state en cookie segura (anti-CSRF)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
    ):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    stored_state = request.cookies.get("oauth_state")

    # Verificar errores y estado
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    if not state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Intercambiar código por token
    token_payload = {
        "client_id": settings.gmail_client_id,
        "client_secret": settings.gmail_client_secret,
        "code": code,
        "redirect_uri": settings.gmail_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(settings.token_url, data=token_payload)

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google token exchange failed"
        )

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Invalid token response")

    # Obtener información del usuario
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    google_user = GoogleUser(**userinfo_response.json())

    # Validar email verificado
    if not google_user.verified_email:
        raise HTTPException(status_code=400, detail="Google email not verified")
    

    # Autenticar usuario en el sistema
    return await google_authenticate(
        db=db,
        google_user=google_user,
        request=request,
        response=response
    )


async def google_authenticate(
    db: AsyncSession,
    *,
    google_user: GoogleUser,
    request: Request,
    response: Response,
    provider: str = "google"
) -> Optional[Dict[str, Any]]:
    """
    Autenticar usuario usando datos de Google OAuth2
    google_user: Datos del usuario obtenidos de Google
    """
    
    # Buscar cuenta social existente
    existing_social = await crud_cuenta_social.get_by_proveedor_and_id(
        db, proveedor=provider, id_usuario_proveedor=google_user.id
    )

    if existing_social:
        # Usuario existente con cuenta social
        user = await crud_usuario.get(db, id=existing_social.id_persona)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se encontró el usuario asociado a la cuenta social, favor de contactar al soporte."
            )
        
        if google_user.email != existing_social.correo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El correo de la cuenta social no coincide con el correo registrado, favor de contactar al soporte."
            )

    else:
        # Buscar usuario por email
        user = await crud_usuario.get_by_email(db, email=google_user.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se encontró el usuario asociado a la cuenta social, favor de contactar al soporte."
            )
        
        else:
            # Crear cuenta social
            await crud_cuenta_social.create_or_update_social_account(
                db,
                usuario_id=user.id,
                proveedor=provider,
                id_usuario_proveedor=google_user.id,
                correo=google_user.email,
                nombre=google_user.name
            )
    
    if not await crud_usuario.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se encontró el usuario asociado a la cuenta social, favor de contactar al soporte."
        )
    
    # Obtener datos de la sesion 
    session = get_session_context(request)

    # Obtener roles
    roles_data = await get_user_roles(db, user.id)
    roles = [r["nombre"] for r in roles_data]
    
    # Generar tokens
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
    set_refresh_token(
        response=response,
        refresh_token=refresh_token["token"]
    )

    return {
        "access_token": access_token["token"],
        "token_type": "Bearer",
    }

# # # Almacén temporal para estados OAuth (en producción usar Redis)
# # oauth_states = {}

# # @router.get("/gmail/login")
# # async def gmail_login(
# #     redirect_url: Optional[str] = Query(None, description="URL de redirección después del login")
# # ):
# #     """
# #     Iniciar proceso de autenticación con Gmail
    
# #     Retorna:
# #         - authorization_url: URL para redirigir al usuario a Gmail
# #         - state: Token de estado para validar el callback
# #     """
# #     # Generar estado único para prevenir CSRF
# #     state = secrets.token_urlsafe(32)
    
# #     # Guardar estado y URL de redirección
# #     oauth_states[state] = {
# #         "redirect_url": redirect_url,
# #         "timestamp": secrets.token_hex(16)
# #     }
    
# #     # Obtener URL de autorización
# #     auth_url = gmail_oauth.get_authorization_url(state=state)
    
# #     return {
# #         "authorization_url": auth_url,
# #         "state": state
# #     }


# # @router.get("/gmail/callback")
# # async def gmail_callback(
# #     code: str,
# #     state: str,
# #     error: Optional[str] = None,
# #     error_description: Optional[str] = None,
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     """
# #     Callback de Gmail OAuth2
# #     Procesa el código de autorización y autentica al usuario
# #     """
# #     # Verificar si hay error
# #     if error:
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST,
# #             detail=f"Error de autenticación: {error_description or error}"
# #         )
    
# #     # Verificar estado
# #     if state not in oauth_states:
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST,
# #             detail="Estado OAuth inválido"
# #         )
    
# #     state_data = oauth_states.pop(state)
# #     redirect_url = state_data.get("redirect_url")
    
# #     try:
# #         # Intercambiar código por token
# #         token_data = await gmail_oauth.exchange_code_for_token(code)
# #         access_token = token_data.get("access_token")
# #         refresh_token = token_data.get("refresh_token")
        
# #         if not access_token:
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail="No se pudo obtener token de acceso"
# #             )
        
# #         # Obtener información del usuario
# #         user_info = await gmail_oauth.get_user_info(access_token)
        
# #         # Extraer datos del usuario
# #         gmail_id = user_info.get("id")
# #         email = user_info.get("email")
# #         name = user_info.get("name", "")
# #         picture = user_info.get("picture", "")
        
# #         if not gmail_id or not email:
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail="No se pudo obtener información completa del usuario"
# #             )
        
# #         # Buscar cuenta social existente
# #         existing_social = await crud_cuenta_social.get_by_proveedor_and_id(
# #             db, proveedor="gmail", id_usuario_proveedor=gmail_id
# #         )
        
# #         user = None
        
# #         if existing_social:
# #             # Usuario existente con cuenta social
# #             user = await crud_usuario.get(db, id=existing_social.id_usuario)
            
# #             # Actualizar token
# #             await crud_cuenta_social.create_or_update_social_account(
# #                 db,
# #                 usuario_id=user.id,
# #                 proveedor="gmail",
# #                 id_usuario_proveedor=gmail_id,
# #                 token_proveedor=access_token,
# #                 correo=email,
# #                 nombre=name
# #             )
# #         else:
# #             # Buscar usuario por email
# #             user = await crud_usuario.get_by_email(db, email=email)
            
# #             if not user:
# #                 # Crear nuevo usuario
# #                 username = email.split("@")[0] + "_" + str(uuid.uuid4())[:8]
                
# #                 # Separar nombre y apellido
# #                 name_parts = name.split(" ", 1) if name else ["Usuario", "Gmail"]
# #                 nombres = name_parts[0]
# #                 apellidos = name_parts[1] if len(name_parts) > 1 else ""
                
# #                 user_data = UsuarioCreate(
# #                     username=username,
# #                     email=email,
# #                     nombres=nombres,
# #                     apellidos=apellidos,
# #                     password=secrets.token_urlsafe(32),  # Contraseña aleatoria
# #                     foto=picture
# #                 )
                
# #                 user = await crud_usuario.create(db, obj_in=user_data)
            
# #             # Crear cuenta social
# #             await crud_cuenta_social.create_or_update_social_account(
# #                 db,
# #                 usuario_id=user.id,
# #                 proveedor="gmail",
# #                 id_usuario_proveedor=gmail_id,
# #                 token_proveedor=access_token,
# #                 correo=email,
# #                 nombre=name
# #             )
        
# #         # Verificar que el usuario esté activo
# #         if not await crud_usuario.is_active(user):
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail="Usuario inactivo"
# #             )
        
# #         # Obtener datos completos del usuario
# #         user_data = await get_user_complete_data(db, user)
        
# #         # Crear token JWT
# #         jwt_token = create_user_token(
# #             user_id=user.id,
# #             email=user.email,
# #             username=user.username,
# #             roles=user_data["roles"],
# #             menus=user_data["menus"],
# #             apis=user_data["apis"],
# #             aplicaciones=user_data["aplicaciones"]
# #         )
        
# #         # Si hay URL de redirección, redirigir con el token
# #         if redirect_url:
# #             return RedirectResponse(
# #                 url=f"{redirect_url}?token={jwt_token}&type=gmail"
# #             )
        
# #         # Retornar datos del usuario y token
# #         return {
# #             "access_token": jwt_token,
# #             "token_type": "bearer",
# #             "user": user_data["user"],
# #             "roles": user_data["roles"],
# #             "menus": user_data["menus"],
# #             "apis": user_data["apis"],
# #             "aplicaciones": user_data["aplicaciones"],
# #             "provider": "gmail"
# #         }
        
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail=f"Error en autenticación con Gmail: {str(e)}"
# #         )


# # @router.post("/gmail/link")
# # async def link_gmail_account(
# #     code: str,
# #     state: str,
# #     db: AsyncSession = Depends(get_db),
# #     current_user = Depends(get_current_active_user)
# # ):
# #     """
# #     Vincular cuenta de Gmail a usuario existente
# #     """
# #     # Verificar estado
# #     if state not in oauth_states:
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST,
# #             detail="Estado OAuth inválido"
# #         )
    
# #     oauth_states.pop(state)
    
# #     try:
# #         # Intercambiar código por token
# #         token_data = await gmail_oauth.exchange_code_for_token(code)
# #         access_token = token_data.get("access_token")
        
# #         # Obtener información del usuario
# #         user_info = await gmail_oauth.get_user_info(access_token)
        
# #         gmail_id = user_info.get("id")
# #         email = user_info.get("email")
# #         name = user_info.get("name", "")
        
# #         # Verificar que la cuenta no esté ya vinculada
# #         existing_social = await crud_cuenta_social.get_by_proveedor_and_id(
# #             db, proveedor="gmail", id_usuario_proveedor=gmail_id
# #         )
        
# #         if existing_social and existing_social.id_usuario != current_user.id:
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail="Esta cuenta de Gmail ya está vinculada a otro usuario"
# #             )
        
# #         # Crear o actualizar cuenta social
# #         await crud_cuenta_social.create_or_update_social_account(
# #             db,
# #             usuario_id=current_user.id,
# #             proveedor="gmail",
# #             id_usuario_proveedor=gmail_id,
# #             token_proveedor=access_token,
# #             correo=email,
# #             nombre=name
# #         )
        
# #         return {"message": "Cuenta de Gmail vinculada correctamente"}
        
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail=f"Error al vincular cuenta de Gmail: {str(e)}"
# #         )



