from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from app.core.database import get_db
from app.crud import permiso_menu as crud_permiso_menu
from app.crud import permiso_api as crud_permiso_api
from app.crud import rol as crud_rol
from app.crud import menu as crud_menu
from app.crud import api as crud_api
from app.schemas.permiso import (
    PermisoApiUpdate, PermisoMenuCreate, PermisoMenuResponse, PermisoMenuDelete, PermisoMenuBulkSave,
    PermisoMenuUpdate, PermisoApiCreate, PermisoApiResponse, PermisoApiDelete, PermisoApiBulkSave
)
from app.auth.dependencies import get_current_active_user, require_roles
from app.models.permiso import PermisoMenu, PermisoApi
from app.models.usuario import Usuario
from app.models.menu import Menu
from app.models.api import Api

router = APIRouter()


# ==================== PERMISOS DE MENÚ ====================

@router.get("/menu/", response_model=List[PermisoMenuResponse], summary="Obtener todos los permisos de menú")
async def get_permisos_menu(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todos los permisos de menú
    """
    permisos = await crud_permiso_menu.get_all(db)
    return [PermisoMenuResponse.model_validate(permiso) for permiso in permisos]

@router.post("/menu/", response_model=PermisoMenuResponse, summary="Crear permiso de menú")
async def create_permiso_menu(
    permiso_in: PermisoMenuCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Crear permiso de menú para un rol
    """
    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=permiso_in.rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Verificar que el menú existe
    menu = await crud_menu.get(db, id=permiso_in.menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menú no encontrado"
        )
    
    # Verificar que no existe ya el permiso
    existing_permiso = await crud_permiso_menu.get_by_rol_menu(
        db, rol_id=permiso_in.rol_id, menu_id=permiso_in.menu_id
    )
    if existing_permiso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe este permiso de menú"
        )
    permiso_in.id_persona = current_user.id
    permiso = await crud_permiso_menu.create(db, obj_in=permiso_in)
    return PermisoMenuResponse.model_validate(permiso)

@router.put("/menus/{rol_menu_id}", response_model=PermisoMenuResponse, summary="Actualizar permiso de menú")
async def update_permiso_menu(
    rol_menu_id: int,
    permiso_in: PermisoMenuUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    # Verificar que no existe ya el permiso
    existing_permiso = await crud_permiso_menu.get_by_rol_menu(
        db, rol_id=permiso_in.rol_id, menu_id=permiso_in.menu_id
    )
    if existing_permiso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe este permiso de menú"
        )
    
    permiso_menu = await crud_permiso_menu.get(db, id=rol_menu_id)
    if not permiso_menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso de menú no encontrado"
        )
    permiso_in.id_persona = current_user.id
    permiso_menu = await crud_permiso_menu.update(db, db_obj=permiso_menu, obj_in=permiso_in)
    return PermisoMenuResponse.model_validate(permiso_menu)

@router.delete("/menu", summary="Eliminar permiso de menú")
async def delete_permiso_menu(
    permiso_in: PermisoMenuDelete,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Eliminar permiso de menú específico
    """
    success = await crud_permiso_menu.remove_by_rol_menu(
        db, rol_id=permiso_in.rol_id, menu_id=permiso_in.menu_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso de menú no encontrado"
        )
    
    return {"message": "Permiso de menú eliminado correctamente"}

@router.get("/menu/rol/{rol_id}", response_model=List[Dict[str, Any]], summary="Obtener menús por rol")
async def get_menus_by_rol(
    rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todos los menús permitidos para un rol
    """
    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    permisos_menu = await crud_permiso_menu.get_menus_by_rol(db, rol_id=rol_id)
    
    menus = []
    for permiso in permisos_menu:
        if permiso.menu_obj:
            menu = permiso.menu_obj
            menus.append({
                "id": menu.id,
                "nombre": menu.nombre,
                "url_menu": menu.url_menu,
                "padre": menu.padre,
                "ruta_front": menu.ruta_front,
                "orden": menu.orden,
                "visible": menu.visible,
                "icono": menu.icono,
                "target": menu.target,
                "id_aplicacion": menu.id_aplicacion,
                "activo": menu.activo,
                "descripcion": menu.descripcion
            })
    
    # Ordenar por orden
    menus.sort(key=lambda x: x["orden"])
    return menus

@router.post("/menu/rol/{rol_id}/bulk", summary="Guardar permisos de menú masivos para un rol")
async def guardar_permisos_menu_bulk(
    rol_id: int,
    data: PermisoMenuBulkSave,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Guarda todos los permisos de menú para un rol (reemplaza los existentes)
    Autor: @Fabio Garcia
    Actualizado: 2025-12-28
    
    Recibe:
    - rol_id: ID del rol (en la URL)
    - data: { menu_ids: [1, 2, 3, ...] }
    """

    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con ID {rol_id} no encontrado"
        )
    
    # Obtener lista de IDs de menú
    result = await db.execute(select(Menu.id).where(Menu.id.in_(data.menu_ids)))
    menus_find = [row[0] for row in result.all()]
    menus_not_find = list(set(data.menu_ids) - set(menus_find))
    if menus_not_find:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Los siguientes IDs de menú no fueron encontrados: {menus_not_find}"
        )
    
    # Eliminar todos los permisos existentes para este rol
    await crud_permiso_menu.remove_by_rol(db, rol_id=rol_id)
    
    # Crear nuevos permisos    
    data_to_insert = [{"rol_id": rol_id, "menu_id": m_id, "id_persona": current_user.id} for m_id in menus_find]
    await db.execute(insert(PermisoMenu), data_to_insert)    
    await db.commit()
    
    return {
        "message": "Permisos guardados exitosamente",
        "rol_id": rol_id,
        "rol_nombre": rol.nombre,
        "total_permisos": len(data_to_insert)
    }

# ==================== PERMISOS DE API ====================

@router.get("/api/", response_model=List[PermisoApiResponse], summary="Obtener todos los permisos de API")
async def get_permisos_api(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todos los permisos de API
    """
    permisos = await crud_permiso_api.get_all(db)
    return [PermisoApiResponse.model_validate(permiso) for permiso in permisos]

@router.post("/api/", response_model=PermisoApiResponse, summary="Crear permiso de API")
async def create_permiso_api(
    permiso_in: PermisoApiCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Crear permiso de API para un rol
    """
    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=permiso_in.rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Verificar que el menú existe
    api = await crud_api.get(db, id=permiso_in.api_id)
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API no encontrada"
        )
    
    # Verificar que no existe ya el permiso
    existing_permiso = await crud_permiso_api.get_by_rol_api(
        db, rol_id=permiso_in.rol_id, api_id=permiso_in.api_id
    )
    if existing_permiso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe este permiso de API"
        )
    permiso_in.id_persona = current_user.id
    permiso = await crud_permiso_api.create(db, obj_in=permiso_in)
    return PermisoApiResponse.model_validate(permiso)

@router.put("/api/{rol_api_id}", response_model=PermisoApiResponse, summary="Actualizar permiso de API")
async def update_permiso_api(
    rol_api_id: int,
    permiso_in: PermisoApiUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    # Verificar que no existe ya el permiso
    existing_permiso = await crud_permiso_api.get_by_rol_api(
        db, rol_id=permiso_in.rol_id, api_id=permiso_in.api_id
    )
    if existing_permiso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe este permiso de API"
        )
    
    permiso_api = await crud_permiso_api.get(db, id=rol_api_id)
    if not permiso_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso de API no encontrado"
        )
    permiso_in.id_persona = current_user.id
    try:
        permiso_api = await crud_permiso_api.update(db, db_obj=permiso_api, obj_in=permiso_in)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el permiso de API: {str(e)}"
        )
    return PermisoApiResponse.model_validate(permiso_api)

@router.delete("/api", summary="Eliminar permiso de API")
async def delete_permiso_api(
    permiso_in: PermisoApiDelete,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Eliminar permiso de menú específico
    """
    success = await crud_permiso_api.remove_by_rol_api(
        db, rol_id=permiso_in.rol_id, api_id=permiso_in.api_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso de API no encontrado"
        )
    
    return {"message": "Permiso de API eliminado correctamente"}

@router.get("/api/rol/{rol_id}", response_model=List[Dict[str, Any]], summary="Obtener APIs por rol")
async def get_apis_by_rol(
    rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todos los menús permitidos para un rol
    """
    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    permisos_api = await crud_permiso_api.get_apis_by_rol(db, rol_id=rol_id)
    
    apis = []
    for permiso in permisos_api:
        if permiso.api_obj:
            api = permiso.api_obj
            apis.append({
                "id": api.id,
                "grupo": api.grupo,
                "url_api": api.url_api,
                "id_aplicacion": api.id_aplicacion,
                "class_front": api.class_front,
                "tipo_accion": api.tipo_accion,
                "nombre": api.nombre,
                "descripcion": api.descripcion
            })
    
    # Ordenar por orden
    apis.sort(key=lambda x: x["id"])
    return apis

@router.post("/api/rol/{rol_id}/bulk", summary="Guardar permisos de API masivos para un rol")
async def guardar_permisos_api_bulk(
    rol_id: int,
    data: PermisoApiBulkSave,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Guarda todos los permisos de API para un rol (reemplaza los existentes)
    Autor: @Fabio Garcia
    Actualizado: 2025-12-28
    
    Recibe:
    - rol_id: ID del rol (en la URL)
    - data: { api_ids: [1, 2, 3, ...] }
    """
    
    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con ID {rol_id} no encontrado"
        )
    
    # Obtener lista de IDs de apis
    result = await db.execute(select(Api.id).where(Api.id.in_(data.api_ids)))
    apis_find = [row[0] for row in result.all()]
    apis_not_find = list(set(data.api_ids) - set(apis_find))
    if apis_not_find:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Los siguientes IDs de API no fueron encontrados: {apis_not_find}"
        )
    
    # Eliminar todos los permisos existentes para este rol
    await crud_permiso_api.remove_by_rol(db, rol_id=rol_id)
    
    # Crear nuevos permisos    
    data_to_insert = [{"rol_id": rol_id, "api_id": a_id, "id_persona": current_user.id} for a_id in apis_find]
    await db.execute(insert(PermisoApi), data_to_insert)    
    await db.commit()
    
    return {
        "message": "Permisos guardados exitosamente",
        "rol_id": rol_id,
        "rol_nombre": rol.nombre,
        "total_permisos": len(data_to_insert)
    }

