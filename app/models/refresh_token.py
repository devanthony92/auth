from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(f"{settings.db_schema}.usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    token_jti = Column(UUID(as_uuid=True), nullable=False, unique=True)
    token_hash = Column(String(64), nullable=False, unique=True)

    # Seguridad / auditoría
    ip = Column(String(45), nullable=True) 
    user_agent = Column(JSONB, nullable=True)
    device_id = Column(String(64), nullable=False)

    # Estado
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relación ORM
    user = relationship("Usuario", back_populates="refresh_tokens")

    Index("ix_refresh_tokens_user_active", "user_id", "is_revoked")
    Index("ix_refresh_tokens_exp", "expires_at")

