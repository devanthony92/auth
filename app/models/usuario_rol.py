from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class UsuarioRol(Base):
    __tablename__ = "usuario_roles"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey(f"{settings.db_schema}.usuarios.id"), nullable=False, index=True)
    id_rol = Column(Integer, ForeignKey(f"{settings.db_schema}.roles.id"), nullable=False, index=True)
    id_persona = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones - corregidas
    usuario_obj = relationship("Usuario", back_populates="usuario_roles")
    rol_obj = relationship("Rol", back_populates="usuario_roles")

