from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth.jwt_handler import create_access_token
from app.crud import usuario as crud_usuario
from app.crud.crud_cuenta_social import cuenta_social as crud_cuenta_social
from app.schemas.usuario import UsuarioCreate
from app.auth.microsoft_oauth import microsoft_oauth
from app.auth.user_data import get_user_complete_data
from app.auth.dependencies import get_current_active_user
import secrets
import uuid

router = APIRouter()

# Almacén temporal para estados OAuth (en producción usar Redis)
oauth_states = {}


@router.get("/microsoft/login")
async def microsoft_login(
    redirect_url: Optional[str] = Query(None, description="URL de redirección después del login")
):
    """
    Iniciar proceso de autenticación con Microsoft
    """
    # Generar estado único para prevenir CSRF
    state = secrets.token_urlsafe(32)
    
    # Guardar estado y URL de redirección
    oauth_states[state] = {
        "redirect_url": redirect_url,
        "timestamp": secrets.token_hex(16)
    }
    
    # Obtener URL de autorización
    auth_url = microsoft_oauth.get_authorization_url(state=state)
    
    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/microsoft/callback")
async def microsoft_callback(
    code: str,
    state: str,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Callback de Microsoft OAuth2
    """
    # Verificar si hay error
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de autenticación: {error_description or error}"
        )
    
    # Verificar estado
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado OAuth inválido"
        )
    
    state_data = oauth_states.pop(state)
    redirect_url = state_data.get("redirect_url")
    
    try:
        # Intercambiar código por token
        token_data = await microsoft_oauth.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo obtener token de acceso"
            )
        
        # Obtener información del usuario
        user_info = await microsoft_oauth.get_user_info(access_token)
        
        # Extraer datos del usuario
        microsoft_id = user_info.get("id")
        email = user_info.get("mail") or user_info.get("userPrincipalName")
        display_name = user_info.get("displayName", "")
        given_name = user_info.get("givenName", "")
        surname = user_info.get("surname", "")
        
        if not microsoft_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo obtener información completa del usuario"
            )
        
        # Buscar cuenta social existente
        existing_social = await crud_cuenta_social.get_by_proveedor_and_id(
            db, proveedor="microsoft", id_usuario_proveedor=microsoft_id
        )
        
        user = None
        
        if existing_social:
            # Usuario existente con cuenta social
            user = await crud_usuario.get(db, id=existing_social.id_usuario)
            
            # Actualizar token
            await crud_cuenta_social.create_or_update_social_account(
                db,
                usuario_id=user.id,
                proveedor="microsoft",
                id_usuario_proveedor=microsoft_id,
                token_proveedor=access_token,
                correo=email,
                nombre=display_name
            )
        else:
            # Buscar usuario por email
            user = await crud_usuario.get_by_email(db, email=email)
            
            if not user:
                # Crear nuevo usuario
                username = email.split("@")[0] + "_" + str(uuid.uuid4())[:8]
                
                user_data = UsuarioCreate(
                    username=username,
                    email=email,
                    nombres=given_name,
                    apellidos=surname,
                    password=secrets.token_urlsafe(32)  # Contraseña aleatoria
                )
                
                user = await crud_usuario.create(db, obj_in=user_data)
            
            # Crear cuenta social
            await crud_cuenta_social.create_or_update_social_account(
                db,
                usuario_id=user.id,
                proveedor="microsoft",
                id_usuario_proveedor=microsoft_id,
                token_proveedor=access_token,
                correo=email,
                nombre=display_name
            )
        
        # Verificar que el usuario esté activo
        if not await crud_usuario.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo"
            )
        
        # Obtener datos completos del usuario
        user_data = await get_user_complete_data(db, user)
        
        # Crear token JWT
        jwt_token = create_access_token(
            user_id=user.id,
            email=user.email,
            username=user.username,
            roles=user_data["roles"],
            menus=user_data["menus"],
            apis=user_data["apis"],
            aplicaciones=user_data["aplicaciones"]
        )
        
        # Si hay URL de redirección, redirigir con el token
        if redirect_url:
            return RedirectResponse(
                url=f"{redirect_url}?token={jwt_token}&type=microsoft"
            )
        
        # Retornar datos del usuario y token
        return {
            "access_token": jwt_token["token"],
            "token_type": "bearer",
            "user": user_data["user"],
            "roles": user_data["roles"],
            "menus": user_data["menus"],
            "apis": user_data["apis"],
            "aplicaciones": user_data["aplicaciones"],
            "provider": "microsoft"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en autenticación con Microsoft: {str(e)}"
        )


@router.post("/microsoft/link")
async def link_microsoft_account(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Vincular cuenta de Microsoft a usuario existente
    """
    # Verificar estado
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado OAuth inválido"
        )
    
    oauth_states.pop(state)
    
    try:
        # Intercambiar código por token
        token_data = await microsoft_oauth.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        
        # Obtener información del usuario
        user_info = await microsoft_oauth.get_user_info(access_token)
        
        microsoft_id = user_info.get("id")
        email = user_info.get("mail") or user_info.get("userPrincipalName")
        display_name = user_info.get("displayName", "")
        
        # Verificar que la cuenta no esté ya vinculada
        existing_social = await crud_cuenta_social.get_by_proveedor_and_id(
            db, proveedor="microsoft", id_usuario_proveedor=microsoft_id
        )
        
        if existing_social and existing_social.id_usuario != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta cuenta de Microsoft ya está vinculada a otro usuario"
            )
        
        # Crear o actualizar cuenta social
        await crud_cuenta_social.create_or_update_social_account(
            db,
            usuario_id=current_user.id,
            proveedor="microsoft",
            id_usuario_proveedor=microsoft_id,
            token_proveedor=access_token,
            correo=email,
            nombre=display_name
        )
        
        return {"message": "Cuenta de Microsoft vinculada correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al vincular cuenta de Microsoft: {str(e)}"
        )

