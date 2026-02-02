"""
Configuración del sistema
Actualizado: 2025-01-18 - Manus AI (@Fabio Garcia)
Soporta MySQL, PostgreSQL y SQL Server
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Base de datos - Configuración multi-base de datos
    db_type: str = "postgresql"  # mysql, postgresql, mssql
    db_host: str = ""
    db_port: int  
    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    db_schema: str = ""  # Schema para PostgreSQL
    
    # Configuración SSL para la conexión
    db_ssl: str = ""  # disable, prefer, require, verify_ca, verify_identity
    db_schema: str = ""  # Schema para PostgreSQL
    
    database_url: str = ""

    # JWT
    secret_key: str = "tu_clave_secreta_super_segura_aqui_cambiar_en_produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    pass_reset_token_expire_minutes: int = 15
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * refresh_token_expire_days
    
    # Microsoft OAuth2
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    microsoft_tenant_id: str = ""
    microsoft_redirect_uri: str = "http://localhost:8000/api/v1/auth/microsoft/callback"
    
    # Gmail OAuth2
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_redirect_uri: str = ""
    token_url: str = ""
    
    # Configuración de la aplicación
    app_name: str = "Sistema de Autenticación"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"]

    # Servicios externos
    base_url_storage: str = ""
    key_storage: str = ""
    base_url_notificaciones: str = ""
    
    # Configuración de logs
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


def build_database_url():
    """Construye la URL de conexión según el tipo de base de datos"""
    
    if settings.db_type.lower() == "mysql":
        # MySQL con aiomysql
        ssl_param = "?ssl=false" if settings.db_ssl == "disable" else "?ssl=true"
        return (
            f"mysql+aiomysql://{settings.db_user}:{settings.db_password}"
            f"@{settings.db_host}:{settings.db_port}/{settings.db_name}{ssl_param}"
        )
    
    elif settings.db_type.lower() == "postgresql":
        # PostgreSQL con asyncpg
        #ssl_mode = settings.db_ssl if settings.db_ssl != "disable" else "disable"
        return (
            f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
            f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            #f"?sslmode={ssl_mode}"
        )
    
    elif settings.db_type.lower() == "mssql":
        # SQL Server con pyodbc
        return (
            f"mssql+pyodbc://{settings.db_user}:{settings.db_password}"
            f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            f"?driver=ODBC+Driver+17+for+SQL+Server"
        )
    
    else:
        raise ValueError(f"Tipo de base de datos no soportado: {settings.db_type}")


# Construir URL de base de datos
settings.database_url = build_database_url()
