from sqlalchemy import UUID, Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(f"{settings.db_schema}.usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    jti = Column(UUID(as_uuid=True), nullable=False, unique=True)
    token_hash = Column(String(64), nullable=False)
    ip_address = Column(String(45), nullable=True) 
    user_agent = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    persona_obj = relationship("Usuario", back_populates="forget_password")

    
    