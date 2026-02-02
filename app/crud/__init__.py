# Importar todos los CRUDs
from app.crud.crud_usuario import usuario
from app.crud.crud_rol import rol
from app.crud.crud_aplicacion import aplicacion
from app.crud.crud_menu import menu
from app.crud.crud_api import api
from app.crud.crud_permiso import permiso_menu, permiso_api
from app.crud.crud_usuario_rol import usuario_rol

# Exportar todos los CRUDs
__all__ = [
    "usuario",
    "rol",
    "aplicacion", 
    "menu",
    "api",
    "permiso_menu",
    "permiso_api",
    "usuario_rol"
]

