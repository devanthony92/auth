from pydantic_core import ValidationError
from sqlalchemy import select, update
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from app.auth.access_token import AccessTokenService
from app.models.password_reset_token import PasswordResetToken
from app.auth.refresh_tokens import RefreshTokenService
from app.crud import usuario as crud_usuario
from app.core.config import settings

from app.auth.jwt_handler import hash_token, create_reset_token, verify_token
from app.schemas.usuario import UsuarioChangePasswordAdmin

class PasswordResetService:

    async def save_reset_token(db, user_id: int, jti: str, token_hash: str, expires_at: datetime, ip_address: str, user_agent: str):
        # Guardar el token de restablecimiento en la base de datos
        try:
            smt = PasswordResetToken(
                user_id=user_id,
                jti=jti,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                )

            db.add(smt)
            await db.commit()

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al guardar el token de restablecimiento: {str(e)}"
            )
        return smt
    
    async def get_reset_token_by_jti(db, jti: str):
        result = await db.execute(
            select(PasswordResetToken).where(PasswordResetToken.jti == jti)
        )
        return result.scalar_one_or_none()
    
    async def revoke_all_reset_tokens(db, user_id: int):
        # Marcar todos los tokens como usados
        await db.execute(update(PasswordResetToken)
                        .where(
                            PasswordResetToken.user_id == user_id,
                            PasswordResetToken.used_at.is_(None),
                            )
                            .values(
                                used_at=datetime.now(timezone.utc)
                                )
            )
    
    async def request_reset_token(db, user_id, ip: str, user_agent: str):
        # Crear el token de restablecimiento
        token = create_reset_token(user_id)
        token_hash = hash_token(token["token"])

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.pass_reset_token_expire_minutes)

        # Guardar el token en la base de datos
        await PasswordResetService.save_reset_token(db=db,
                                                    user_id=user_id,
                                                    jti=token['jti'],
                                                    token_hash=token_hash,
                                                    expires_at=expires_at,
                                                    ip_address=ip,
                                                    user_agent=user_agent,
                                                    )

        return token  # solo se usa para enviarlo por email
    
    async def confirm_reset(db, token: str, new_password: str):
        # Verificar el token
        reset_token = verify_token(token)
        jti = reset_token.get("jti")

        result  = await PasswordResetService.get_reset_token_by_jti(db, jti)
        
        if not result or result.used_at is not None:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o usado previamente"
        )

        # Obtener el usuario asociado al token        
        usuario = await crud_usuario.get(db=db, id=result.user_id)
        if not usuario:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario asociado al token no fue encontrado"
        )
        
        # Cambiar la contraseña
        try:
            data = UsuarioChangePasswordAdmin(usuario_id=usuario.id,
                                       new_password=new_password
                                       )
            await crud_usuario.update_password(
                db, db_obj=usuario, new_password=new_password
            )

        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= f"Error de validación: {str(e)}"
            )

        # revocar refresh tokens
        try:
            await RefreshTokenService.revoke_refresh_tokens_by_user(db=db, user_id=usuario.id)
            await AccessTokenService.revoke_access_tokens_by_user(db=db, user_id=usuario.id)
            await PasswordResetService.revoke_all_reset_tokens(db=db, user_id=usuario.id)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al revocar tokens: {str(e)}"
            )

        return usuario
        