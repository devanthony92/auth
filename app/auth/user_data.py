from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usuario import Usuario
from app.crud import usuario_rol as crud_usuario_rol
from app.crud import permiso_menu as crud_permiso_menu
from app.crud import permiso_api as crud_permiso_api
from app.crud import rol as crud_rol


async def get_user_roles(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
    """Obtener roles del usuario"""
    user_roles = await crud_usuario_rol.get_roles_by_usuario(db, usuario_id=user_id)
    
    roles = []
    for user_role in user_roles:
        if user_role.rol_obj:
            roles.append({
                "id_rol": user_role.rol_obj.id,
                "nombre": user_role.rol_obj.nombre,
                "descripcion": user_role.rol_obj.descripcion,
                "key_publico": user_role.rol_obj.key_publico,
                "id_aplicacion": user_role.rol_obj.id_aplicacion
            })
    
    return roles


async def get_user_complete_data(db: AsyncSession, user: Usuario) -> Dict[str, Any]:
    """Obtener datos completos del usuario para el token"""
    
    # Obtener todos los datos del usuario
    roles = await get_user_roles(db, user.id)
    roles_ids = [r["id_rol"] for r in roles]
    
    menus = await get_roles_menus_map(db, roles_ids)
    apis  = await get_roles_apis_map(db, roles_ids)
    aplis = await get_roles_aplicaciones_map(db, roles_ids)
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nombres": user.nombres,
            "apellidos": user.apellidos,
            "nombre_completo": user.nombre_completo,
            "foto": user.foto,
            "activo": user.activo
        },
        "roles": roles,
        "menus": menus,
        "apis": apis,
        "aplicaciones": aplis
    }


async def get_users_roles_map(db: AsyncSession, user_ids: list[int]):
    result = await crud_usuario_rol.get_roles_by_usuarios_map(db, user_ids)

    roles_map = {}
    for id_usuario, rol in result:
        roles_map.setdefault(id_usuario, []).append({
            "id_rol": rol.id,
            "nombre": rol.nombre,
            "descripcion": rol.descripcion,
            "key_publico": rol.key_publico,
            "id_aplicacion": rol.id_aplicacion
        })
    return roles_map


async def get_roles_aplicaciones_map(db: AsyncSession, roles_ids: list[int]):
    result = await crud_rol.get_aplicaciones_by_roles_map(db, roles_ids)

    applications_map = {}
    for _, application in result:
        applications_map.setdefault(application.id, {
            "id_aplicacion": application.id,
            "key": application.key,
            "nombre": application.nombre,
            "descripcion": application.descripcion
        })

    return list(applications_map.values())


async def get_roles_menus_map(db: AsyncSession, roles_ids: list[int]):
    result = await crud_permiso_menu.get_menus_by_roles_map(db, roles_ids)
    
    menus_map = []
    for menu in result:
        menus_map.append({
            "id_menu": menu.id,
            "nombre": menu.nombre,
            "url_menu": menu.url_menu,
            "ruta_front": menu.ruta_front,
            "padre": menu.padre
        })


    return menus_map


async def get_roles_apis_map(db: AsyncSession, roles_ids: list[int]):
    result = await crud_permiso_api.get_apis_by_roles_map(db, roles_ids)
    
    apis_map = []
    for api in result:
        apis_map.append({
            "id_api": api.id,
            "nombre": api.nombre,
            "grupo": api.grupo,
            "url_api": api.url_api,
            "class_front": api.class_front
        })

    return apis_map