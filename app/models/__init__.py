# Importar todos los modelos para que SQLAlchemy los reconozca
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.aplicacion import Aplicacion
from app.models.menu import Menu
from app.models.api import Api
from app.models.permiso import PermisoMenu, PermisoApi
from app.models.usuario_rol import UsuarioRol
from app.models.cuenta_social import CuentaSocial
from app.models.bitacora import Bitacora, TipoBitacora
from app.models.aplicacion_cliente import AplicacionCliente
from app.models.recording import Recording
from app.models.Logs_login import LoginLog

# Exportar todos los modelos
__all__ = [
    "Usuario",
    "Rol", 
    "Aplicacion",
    "Menu",
    "Api",
    "PermisoMenu",
    "PermisoApi",
    "UsuarioRol",
    "CuentaSocial",
    "Bitacora",
    "TipoBitacora",
    "AplicacionCliente",
    "Recording",
    "LoginLog"
]

