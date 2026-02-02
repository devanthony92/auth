from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class TipoBitacora(Base):
    __tablename__ = "tipo_bitacora"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(145), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones - corregidas
    bitacoras = relationship("Bitacora", back_populates="tipo_bitacora_obj")


class Bitacora(Base):
    __tablename__ = "bitacoras"
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

    id = Column(BigInteger, primary_key=True, index=True)
    id_tipo_bitacora = Column(Integer, ForeignKey(f"{settings.db_schema}.tipo_bitacora.id"), nullable=False, index=True)
    datos_anteriores = Column(String(255), nullable=True)
    datos_insertados = Column(String(255), nullable=True)
    observacion = Column(String(245), nullable=True)
    menu = Column(String(245), nullable=True, index=True)
    url_api = Column(String(445), nullable=True, index=True)
    id_persona = Column(Integer, ForeignKey(f"{settings.db_schema}.usuarios.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relaciones - corregidas
    tipo_bitacora_obj = relationship("TipoBitacora", back_populates="bitacoras")
    usuario_obj = relationship("Usuario", back_populates="bitacoras")

