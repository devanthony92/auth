from sqlalchemy import Column, Integer, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class PermisoMenu(Base):
    __tablename__ = "permiso_menu"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rol_id = Column(Integer, ForeignKey(f"{settings.db_schema}.roles.id"), nullable=False)
    menu_id = Column(BigInteger, ForeignKey(f"{settings.db_schema}.menu.id"), nullable=False)
    id_persona = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Integer, default=1)

    # Relaciones - corregidas
    rol_obj = relationship("Rol", back_populates="permiso_menus")
    menu_obj = relationship("Menu", back_populates="permiso_menus")


class PermisoApi(Base):
    __tablename__ = "permiso_api"
    __table_args__ = {"schema": settings.db_schema}
    id = Column(BigInteger, primary_key=True,index=True, autoincrement=True)
    api_id = Column(BigInteger, ForeignKey(f"{settings.db_schema}.api.id"), nullable=False)
    rol_id = Column(Integer, ForeignKey(f"{settings.db_schema}.roles.id"), nullable=False)
    id_persona = Column(BigInteger, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Integer, default=1)

    # Relaciones - corregidas
    api_obj = relationship("Api", back_populates="permiso_apis")
    rol_obj = relationship("Rol", back_populates="permiso_apis")

