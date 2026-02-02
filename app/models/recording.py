from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings


class Recording(Base):
    __tablename__ = "recordings"
    __table_args__ = {"schema": settings.db_schema}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_path = Column(String(500), nullable=False, comment="Ruta del archivo en S3")
    container_name = Column(String(255), nullable=False, comment="Nombre del contenedor/bucket")
    file_name = Column(String(255), nullable=False, comment="Nombre original del archivo")
    file_size = Column(Integer, nullable=True, comment="Tamaño del archivo en bytes")
    content_type = Column(String(100), nullable=True, comment="Tipo de contenido del archivo")
    etiqueta = Column(String(255), nullable=True, comment="Campo etiqueta opcional")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Fecha de inserción del registro")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Fecha de última actualización")

