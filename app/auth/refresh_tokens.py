
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime, timezone
from app.models.refresh_token import RefreshToken


class RefreshTokenService():
    async def save_refresh_token(db, *,
                                user_id: int,
                                token_jti: str,
                                token_hash: str,
                                expires_at: datetime,
                                ip: str | None = None,
                                user_agent: Dict[str, Any] | None = None,
                                device_id: str
                                ) -> None:
        entity = RefreshToken(
            user_id=user_id,
            token_jti=token_jti,
            token_hash=token_hash,
            expires_at=expires_at,
            ip=ip,
            user_agent=user_agent,
            device_id = device_id
        )

        db.add(entity)
        #await db.commit()

    async def get_refresh_token_id(db: AsyncSession, token_jti: str) -> RefreshToken | None:
        result = await db.execute(select(RefreshToken)
                                  .where(RefreshToken.token_jti == token_jti)
                                  )
        return result.scalar_one_or_none()

    async def get_refresh_token_active_by_device(db: AsyncSession, device_id: str) -> RefreshToken | None:
        result = await db.execute(select(RefreshToken)
                                  .where(RefreshToken.device_id == device_id,
                                         RefreshToken.is_revoked == False
                                         )
                                  )
        return result.scalar_one_or_none()
    
    async def revoke_refresh_token_by_device(db: AsyncSession, device_id: str):
        await db.execute(
                    update(RefreshToken)
                    .where(
                        RefreshToken.device_id == device_id,
                        RefreshToken.is_revoked == False,
                        )
                        .values(
                            is_revoked=True,
                            revoked_at=datetime.now(timezone.utc)
                            )
        )
        #await db.commit()

    async def revoke_refresh_token(db: AsyncSession, token_id):
        result = await db.execute(select(RefreshToken).where(RefreshToken.id == token_id))
        token = result.scalars().first()
        if not token:
            return None
        
        # Marcar como revocado
        token.is_revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        
        return token

    async def revoke_refresh_tokens_by_user(db: AsyncSession, user_id: int):
        """
        Marca todos los refresh tokens de un usuario como revocados.
        """
        await db.execute(update(RefreshToken)
                        .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
                        .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
                        )
        
    