from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class CuentaSocial(Base):
    __tablename__ = "cuentas_sociales"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    proveedor = Column(String(20), nullable=False)    
    id_usuario_proveedor = Column(String(255), nullable=False)
    token_proveedor = Column(Text, nullable=True)
    correo = Column(String(100), nullable=True)
    nombre = Column(String(100), nullable=True)
    id_persona = Column(Integer, ForeignKey(f"{settings.db_schema}.usuarios.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones - corregidas
    usuario_obj = relationship("Usuario", back_populates="cuentas_sociales")

    

