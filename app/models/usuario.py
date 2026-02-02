from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hash_clave = Column(String(255), nullable=False)
    nombres = Column(String(250), nullable=True)
    apellidos = Column(String(250), nullable=True)
    firma = Column(String(250), nullable=True)
    foto = Column(String(250), nullable=True)
    activo = Column(Integer, default=1, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones - corregidas
    usuario_roles = relationship("UsuarioRol", back_populates="usuario_obj")
    cuentas_sociales = relationship("CuentaSocial", back_populates="usuario_obj")
    bitacoras = relationship("Bitacora", back_populates="usuario_obj")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    forget_password = relationship("PasswordResetToken", back_populates="persona_obj")
    access_tokens = relationship("AccessToken", back_populates="user")
    roles = relationship("Rol", back_populates="persona_obj")

    @property
    def nombre_completo(self):
        if self.nombres and self.apellidos:
            return f"{self.nombres} {self.apellidos}"
        return self.nombres or self.apellidos or self.username

