from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class Rol(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False, index=True)
    id_aplicacion = Column(Integer, default=0, nullable=False, index=True)
    descripcion = Column(String(255), nullable=True)
    key_publico = Column(String(50), unique=True, nullable=True)
    id_persona = Column(Integer, ForeignKey(f"{settings.db_schema}.usuarios.id"), nullable=True)
    activo = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones - corregidas para coincidir con los nombres en los otros modelos
    usuario_roles = relationship("UsuarioRol", back_populates="rol_obj")
    permiso_menus = relationship("PermisoMenu", back_populates="rol_obj")
    permiso_apis = relationship("PermisoApi", back_populates="rol_obj")
    persona_obj = relationship("Usuario", back_populates="roles")

