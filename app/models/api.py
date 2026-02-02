from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class Api(Base):
    __tablename__ = "api"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    grupo = Column(String(50), nullable=True, index=True)
    url_api = Column(String(460), nullable=False)
    id_aplicacion = Column(Integer, ForeignKey(f"{settings.db_schema}.aplicaciones.id"), default=0, nullable=False, index=True)
    class_front = Column(String(460), nullable=True)
    tipo_accion = Column(Integer, nullable=True, index=True)
    nombre = Column(String(145), nullable=False)
    descripcion = Column(String(255), nullable=True)
    id_persona = Column(Integer, nullable=True, index=True)
    activo = Column(Integer, default=1, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones - corregidas
    aplicacion_obj = relationship("Aplicacion", back_populates="apis")
    permiso_apis = relationship("PermisoApi", back_populates="api_obj")

