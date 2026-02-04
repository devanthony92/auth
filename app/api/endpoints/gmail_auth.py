"""
Endpoints de autenticación con Gmail OAuth2
Autor: Manus AI (@Fabio Garcia)
Fecha: 2025-01-18
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, status, Depends, Response
from fastapi.responses import RedirectResponse
import httpx
import urllib.parse
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.access_token import AccessTokenService
from app.core.database import get_db
from app.crud import usuario as crud_usuario
from app.crud.crud_cuenta_social import cuenta_social as crud_cuenta_social
from app.schemas.cuenta_social import GoogleUser
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    set_refresh_token,
    hash_token
)
from app.auth.user_data import get_user_roles
from app.auth.refresh_tokens import RefreshTokenService
import secrets
from app.core.config import settings
from app.utils.Logs_login_service import LogLoginService
from app.utils.GeoIp2 import get_session_context

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
    """
    Callback de Gmail OAuth2
    Procesa el código de autorización y extraer parámetros de la solicitud
    Inicializa la autenticación del usuario usando los datos obtenidos de Google
    """

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    stored_state = request.cookies.get("oauth_state")

    # Eliminar cookie de estado después de leerla
    response.delete_cookie("oauth_state")

    # Verificar errores y estado
    if not code:
        raise HTTPException(status_code=400, detail="Codigo de autorización faltante.")

    if not state or state != stored_state:
        raise HTTPException(status_code=400, detail="OAuth state no válido. Posible ataque CSRF.")

    try:
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
                detail="Error al obtener token de Google"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Access token no recibido de Google.")

        # Obtener información del usuario
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        google_user = GoogleUser(**userinfo_response.json())

        # Validar email verificado
        if not google_user.verified_email:
            raise HTTPException(status_code=400, detail="El correo de Google no está verificado, por favor verifica tu correo antes de continuar.")
        

        # Autenticar usuario en el sistema
        return await google_authenticate(
            db=db,
            google_user=google_user,
            request=request,
            response=response
        )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout al conectar con Google"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error de red al conectar con Google: {str(e)}"
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
    Args:
        db (AsyncSession): Sesión de base de datos
        google_user (GoogleUser): Datos del usuario obtenidos de Google
        request (Request): Objeto de solicitud FastAPI
        response (Response): Objeto de respuesta FastAPI
    Returns:
        - Diccionario con tokens de acceso si la autenticación es exitosa
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
        
        if user: 
            # Usuario existe pero no tiene cuenta social vinculada
            # Crear cuenta social para el usuario existente
            await crud_cuenta_social.create_or_update_social_account(
                db,
                usuario_id=user.id,
                proveedor=provider,
                id_usuario_proveedor=google_user.id,
                correo=google_user.email,
                nombre=google_user.name
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se encontró el usuario asociado a la cuenta social, favor de contactar al soporte."
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
    
    redirect = RedirectResponse("http://localhost:4200/callback?access_token=" + access_token["token"] + "&token_type=Bearer")

    
    # Guardar el refresh token en cookies del usuario
    set_refresh_token(
        response=redirect,
        refresh_token=refresh_token["token"]
    )
    return redirect
    return {
        "access_token": access_token["token"],
        "token_type": "Bearer",
    }
