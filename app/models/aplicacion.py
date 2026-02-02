from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class Aplicacion(Base):
    __tablename__ = "aplicaciones"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String(250), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    activo = Column(Integer, default=1, index=True)

    # Relaciones - corregidas
    menus = relationship("Menu", back_populates="aplicacion_obj")
    apis = relationship("Api", back_populates="aplicacion_obj")

