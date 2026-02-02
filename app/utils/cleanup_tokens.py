from sqlalchemy import text
from app.core.scheduler import scheduler
from app.core.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

@scheduler.scheduled_job("cron", hour=15, minute=52)
async def cleanup_expired_refresh_tokens():
    """
    Borra refresh tokens expirados todos los días a las 03:00 AM
    """
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("DELETE FROM refresh_tokens WHERE expires_at <= NOW()")
            )
            await db.commit()
            print(f"Expired refresh tokens cleaned. Rows affected: {result.rowcount or 0}")
            logger.info(f"Expired refresh tokens cleaned. Rows affected: {result.rowcount or 0}")

    except Exception as e:
        logger.error(f"Error cleaning refresh tokens: {e}")

# Codigo de prueba
@scheduler.scheduled_job("interval", hours=1)
async def test_job():
    """
    Borra refresh tokens con mas de 2 horas de antiguedad que esten expirados
    """
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    DELETE FROM refresh_tokens
                    WHERE created_at <= NOW() - INTERVAL '4 hours'
                      AND is_revoked = TRUE
                """)
            )
            await db.commit()
            print(f"Expired refresh tokens cleaned. Rows affected: {result.rowcount or 0}")
            logger.info(f"Expired refresh tokens cleaned. Rows affected: {result.rowcount or 0}")

    except Exception as e:
        logger.error(f"Error cleaning refresh tokens: {e}")