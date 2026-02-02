from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from app.core.config import settings


class LoginLog(Base):
    __tablename__ = "login_logs"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ip = Column(String(255), nullable=False)  
    location = Column(String(255), nullable=True)
    user_agent = Column(JSONB, nullable=True)
    