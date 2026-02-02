from fastapi import APIRouter
from app.api.endpoints import auth, profile, usuarios, microsoft_auth, gmail_auth, roles, menus, apis, permisos, aplicaciones, usuario_roles, registro

# Crear el router principal
api_router = APIRouter()

# Incluir todos los routers
api_router.include_router(registro.router, prefix="/public", tags=["Registro Público"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
#api_router.include_router(microsoft_auth.router, prefix="/auth", tags=["Autenticación Microsoft"])
api_router.include_router(gmail_auth.router, prefix="/auth", tags=["Autenticación Gmail"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(menus.router, prefix="/menus", tags=["Menús"])
api_router.include_router(apis.router, prefix="/apis", tags=["APIs"])
api_router.include_router(permisos.router, prefix="/permisos", tags=["Permisos"])
api_router.include_router(aplicaciones.router, prefix="/aplicaciones", tags=["Aplicaciones"])
#api_router.include_router(aplicacion_clientes.router, prefix="/aplicacion_clientes", tags=["AplicacionClientes"])
api_router.include_router(usuario_roles.router, prefix="/usuario_roles", tags=["UsuarioRoles"])
api_router.include_router(profile.router, prefix="/profile", tags=["Perfil"])
api_router.include_router(registro.router, prefix="/public", tags=["Registro Público"])

# Ruta de verificación
@api_router.get("/")
async def api_root():
    return {"message": "API v1 funcionando correctamente"}
