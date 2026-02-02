"""
Configuración de la base de datos con soporte SSL
Actualizado: 2025-11-27 - Fabio Garcia
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings
import ssl

# Configurar argumentos de conexión para SSL
connect_args = {}

if settings.db_ssl:
    # Habilitar SSL completamente
    # SSL sin verificación estricta (para desarrollo)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connect_args = {
        "ssl": ssl_context,
        "server_settings": {
            "search_path": settings.db_schema  # Establecer el schema por defecto
        }
    }
else:
     # Deshabilitar SSL completamente
    connect_args = {
        "ssl": False,
        "server_settings": {
            "search_path": settings.db_schema  # Establecer el schema por defecto
        }
    }

# Crear el motor de base de datos asíncrono con configuración SSL
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    pool_recycle=3600,   # Reciclar conexiones cada hora
    pool_size=10,        # Tamaño del pool de conexiones
    max_overflow=20      # Conexiones adicionales permitidas
)

# Crear el sessionmaker asíncrono
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base para los modelos
Base = declarative_base()


# Dependency para obtener la sesión de base de datos
async def get_db() -> AsyncSession:
    """
    Dependency que proporciona una sesión de base de datos
    
    Yields:
        AsyncSession: Sesión de base de datos asíncrona
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
