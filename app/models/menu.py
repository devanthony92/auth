from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class Menu(Base):
    __tablename__ = "menu"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    url_menu = Column(String(250), unique=True, nullable=False)
    id_aplicacion = Column(Integer, ForeignKey(f"{settings.db_schema}.aplicaciones.id"), default=0, nullable=False, index=True)
    padre = Column(BigInteger, nullable=True)
    nombre = Column(String(250), nullable=False)
    ruta_front = Column(String(250), nullable=True)
    orden = Column(Integer, default=0, nullable=True, index=True)
    visible = Column(Integer, default=1, nullable=True, index=True)
    acceso = Column(Integer, default=1)
    icono = Column(String(300), nullable=True)
    target = Column(String(49), nullable=True)
    activo = Column(Integer, default=1, index=True)
    descripcion = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    id_persona = Column(Integer, ForeignKey(f"{settings.db_schema}.usuarios.id"), nullable=True, index=True)

    # Relaciones - corregidas
    aplicacion_obj = relationship("Aplicacion", back_populates="menus")
    permiso_menus = relationship("PermisoMenu", back_populates="menu_obj")

