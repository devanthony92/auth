from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from uuid import uuid4
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, Response, status
from app.core.config import settings


def create_access_token(
    user_id: int,
    roles: List[Dict[str, Any]]
) -> str:
    """
    Crear token de acceso JWT utilizado para autenticar peticiones
    Retorna:
    - access_token (string) → se envía al cliente
    - jti (string) → se guarda en BD
    """
    try:
        # Crear el identificador unico del token
        jti = uuid4()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

        to_encode = {
            "jti": str(jti),
            "sub": str(user_id),
            "roles": roles,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "iss": settings.app_name,
            "token_type": "access",
        }

        token = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al generar access token: {e}"
        )
    
    

    return {
        "token": token,
        "jti": jti, 
        "expires_at": expire
        }

def create_refresh_token(user_id: str) -> dict[str, Any]:
    """
    Crear Refresh Token utilizado para refrescar el access token cuando expira
    Retorna:
    - refresh_token (string) → se guarda en cookie segura httpOnly
    - refresh_token_jti (string) → se guarda en BD
    """
    try:
        # Asignar el tiempo de expiracion del regresh token
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.refresh_token_expire_days)

        # Crear el identificador unico del token
        jti = uuid4()

        payload = {
            "sub": str(user_id),    # Id del usuario
            "jti": str(jti),
            "iat": int(now.timestamp()),    # cuando fue generado el token
            "exp": int(expire.timestamp()), # cuando expira el token
            "iss": settings.app_name,       # emisor del token
            "token_type": "refresh",        # tipo de token
        }
        token = jwt.encode(payload,
                           settings.secret_key,
                           algorithm=settings.algorithm
                           )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al generar refresh token: {e}"
        )
    
    return {
        "token": token,
        "jti": jti, 
        "expires_at": expire
        }

def create_reset_token(user_id: str) -> dict[str, Any]: 
    """
    Crear token de reseteo de contraseña JWT
    Retorna:
    - reset_token (string) → se envía al cliente

    """
    try:
        # Asignar el tiempo de expiracion del regresh token
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.pass_reset_token_expire_minutes)
        

        # Crear el identificador unico del token
        jti = uuid4()

        payload = {
            "sub": str(user_id),    # Id del usuario
            "jti": str(jti),
            "iat": int(now.timestamp()),    # cuando fue generado el token
            "exp": int(expire.timestamp()), # cuando expira el token
            "iss": settings.app_name,       # emisor del token
            "token_type": "reset_password", # tipo de token
        }
        token = jwt.encode(payload,
                           settings.secret_key,
                           algorithm=settings.algorithm
                           )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al generar reset token: {e}"
        )
    
    return {
        "token": token,
        "jti": jti,
        "expires_at": settings.pass_reset_token_expire_minutes
            }

def verify_token(token: str) -> Dict[str, Any]:
    """Verificar y decodificar token JWT"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm], issuer=settings.app_name, options={"require": ["sub", "exp", "iat", "iss"],
                                                                                                   "verify_signature": True,
                                                                                                   "verify_exp": True,
                                                                                                   "verify_iss": True})
        
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def set_refresh_token(response: Response, refresh_token):
    response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/api/v1/auth/refresh",
            max_age=settings.REFRESH_TOKEN_EXPIRE_SECONDS
        )
    
def hash_token(token: str) -> str:
    return bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()

def verify_token_hash(token: str, hashed: str) -> bool:
    return bcrypt.checkpw(token.encode(), hashed.encode())