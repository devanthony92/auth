from app.core.database import AsyncSessionLocal
from datetime import datetime, timezone
from app.models.Logs_login import LoginLog
from app.utils.GeoIp2 import SessionContext

class LogLoginService:
    async def create_log(
            user_id: int,
            session_data: SessionContext
    ):
        """Registra un log de login de usuario."""
        try:
            async with AsyncSessionLocal() as bg_db:
                login_payload = LoginLog(
                    user_id=user_id,
                    ip=session_data.ip,
                    user_agent=session_data.user_agent,
                    location=session_data.location,
                    timestamp=datetime.now(timezone.utc)
                )
                bg_db.add(login_payload)
                await bg_db.commit()
        except Exception as e:
            print(f"Error al crear log de login: {e}")