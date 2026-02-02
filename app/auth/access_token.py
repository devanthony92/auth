from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime, timezone
from app.models.access_token import AccessToken


class AccessTokenService():
    async def save_access_token(db: AsyncSession, *,
                                user_id: int,
                                jti: str,
                                expires_at: datetime
                                ) -> None:
        """
        Guarda un nuevo access token en la base de datos.
        """
        entity = AccessToken(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at
        )

        db.add(entity)
        #await db.commit()

    async def get_access_token_id(db: AsyncSession, jti: str) -> AccessToken | None:
        result = await db.execute(select(AccessToken)
                                  .where(AccessToken.jti == jti)
                                  )
        return result.scalar_one_or_none()

    async def revoke_access_token(db: AsyncSession, token_id: int) -> AccessToken | None:
        """
        Marca un access token específico como revocado.
        """
        result = await db.execute(select(AccessToken).where(AccessToken.id == token_id))
        token = result.scalars().first()
        if not token:
            return None
        
        # Marcar como revocado
        token.is_revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        
        return token

    async def revoke_access_tokens_by_user(db: AsyncSession, user_id: int):
        """
        Marca todos los access tokens de un usuario como revocados.
        """
        await db.execute(update(AccessToken)
                        .where(AccessToken.user_id == user_id, AccessToken.is_revoked == False)
                        .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
                        )
        
