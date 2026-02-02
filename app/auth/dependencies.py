from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.access_token import AccessTokenService
from app.core.database import get_db
from app.crud import usuario as crud_usuario
from app.auth.jwt_handler import verify_token
from app.models.usuario import Usuario
from app.core.config import settings

# Configurar el esquema de autenticación Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    """Obtener el usuario actual desde el token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verificar el token
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Verificar que el access token no este revocado
        jti: str = payload.get("jti")
        stored_token = await AccessTokenService.get_access_token_id(db, jti)
        if stored_token is None or stored_token.is_revoked:
            raise credentials_exception
        
    except Exception:
        raise credentials_exception
    
    # Obtener el usuario de la base de datos
    user = await crud_usuario.get(db, id=int(user_id))
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Obtener el usuario actual y verificar que esté activo"""
    if not await crud_usuario.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Usuario inactivo"
        )
    return current_user


def verify_refresh_token(
    request: Request,
    ):
    """Verificar el refresh token desde las cookies"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no enviado"
        )
    try:
        payload = jwt.decode(refresh_token,
                            settings.secret_key,
                            algorithms=[settings.algorithm],
                            options={"verify_signature": True,
                                    "verify_exp": True})
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado, por favor incie sesion nuevamente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )    
    return {"refresh_token": refresh_token, "payload": payload}


def require_roles(required_roles: list):
    """Decorator para requerir roles específicos"""
    async def role_checker(
        current_user: Usuario = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        # Obtener roles del usuario
        user_with_roles = await crud_usuario.get_with_roles(db, user_id=current_user.id)
        if not user_with_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No se pudieron obtener los roles del usuario"
            )

        user_roles = [ur.rol_obj.nombre for ur in user_with_roles.usuario_roles if ur.rol_obj]

        # Verificar si el usuario tiene alguno de los roles requeridos
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los siguientes roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


def require_permissions(required_apis: list):
    """Decorator para requerir permisos específicos de API"""
    async def permission_checker(
        current_user: Usuario = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        from app.crud import permiso_api as crud_permiso_api
        from app.crud import usuario_rol as crud_usuario_rol
        
        # Obtener roles del usuario
        user_roles = await crud_usuario_rol.get_roles_by_usuario(db, usuario_id=current_user.id)
        
        # Verificar permisos para cada rol
        user_apis = []
        for user_role in user_roles:
            role_apis = await crud_permiso_api.get_apis_by_rol(db, rol_id=user_role.id_rol)
            user_apis.extend([api.api_obj.url_api for api in role_apis if api.api_obj])
        
        # Verificar si el usuario tiene acceso a alguna de las APIs requeridas
        if not any(api in user_apis for api in required_apis):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tiene permisos para acceder a esta funcionalidad"
            )
        
        return current_user
    
    return permission_checker

