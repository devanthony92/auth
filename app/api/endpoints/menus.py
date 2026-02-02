from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.crud import menu as crud_menu
from app.schemas.menu import MenuCreate, MenuUpdate, MenuResponse
from app.schemas import PaginatedResponse
from app.auth.dependencies import require_roles, get_current_active_user
from app.models.usuario import Usuario

router = APIRouter()
def _build_tree(menu_list):
        menu_map = {m["id"]: m for m in menu_list}

        tree = []
        for m in menu_list:
            if m["padre"]:
                parent = menu_map.get(m["padre"])
                if parent:
                    parent["children"].append(menu_map[m["id"]])
            else:
                tree.append(menu_map[m["id"]])

        return tree


@router.get("/", response_model=PaginatedResponse, summary="Obtener menús con paginación y filtros")
async def get_menus(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    search: Optional[str] = Query(None),
    id_aplicacion: Optional[int] = Query(None),
    padre: Optional[int] = Query(None),
    visible: Optional[int] = Query(None),
    activo: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener lista de menús con paginación y filtros
    """
    skip = (page - 1) * per_page
    limit = per_page
    filters = {}
    if id_aplicacion is not None:
        filters["id_aplicacion"] = id_aplicacion
    if padre is not None:
        filters["padre"] = padre
    if visible is not None:
        filters["visible"] = visible
    if activo is not None:
        filters["activo"] = activo
    
    if search:
        menus = await crud_menu.search_menus(
            db, search_term=search, skip=skip, limit=limit
        )
        total = await crud_menu.count_search(db, search_term=search)
    else:
        menus = await crud_menu.get_multi(
            db, skip=skip, limit=limit, filters=filters, order_by="orden"
        )
        total = await crud_menu.count(db, filters=filters)
    
    
    
    return PaginatedResponse(
        items=[MenuResponse.model_validate(menu) for menu in menus],
        total=total,
        page=page,
        per_page=per_page,
        last_page=(total + per_page - 1) // per_page,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/by-user", response_model=List[Dict[str, Any]], summary="Obtener menús accesibles para el usuario logueado basado en sus roles")
async def get_menus_by_user(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener menús accesibles para el usuario basado en sus roles
    y construir el árbol de menús.
    """
    from app.models.menu import Menu
    from app.models.permiso import PermisoMenu
    from app.auth.user_data import get_user_roles

    
    user_data = await get_user_roles(db, current_user.id)
    user_roles = [rol["id_rol"] for rol in user_data]
    

    if not user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sin roles asociados"
        )
    # Consulta de menús asociados a los roles del usuario y a la aplicación                
    stmt = (
            select(Menu)
            .distinct()
            .join(PermisoMenu, PermisoMenu.menu_id == Menu.id)
            .where(
                PermisoMenu.rol_id.in_(user_roles),
                PermisoMenu.activo == 1,
                Menu.activo == 1
            )
            .order_by(Menu.padre.nullsfirst(), Menu.orden)
        )

    try:
        result = await db.execute(stmt)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando menús: {e}")

    menus = result.scalars().all()

    # Construir el árbol de menús
    menu_map = {
        m.id: {
            "id": m.id,
            "nombre": m.nombre,
            "url_menu": m.url_menu,
            "icono": m.icono or "solar:layers-line-duotone",
            "padre": m.padre,
            "children": []
        }
        for m in menus
    }
    return _build_tree(list(menu_map.values()))


@router.get("/all", response_model=List[MenuResponse], summary="Obtener todos los menús sin paginación")
async def get_menus_all(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todos los menús sin paginación
    """
    menus = await crud_menu.get_activo_menus_all(db, activo=1)
    return [MenuResponse.model_validate(menu) for menu in menus]


@router.get("/hierarchy", response_model=List[Dict[str, Any]], summary="Obtener jerarquía completa de menús en estructura de árbol")
async def get_menu_hierarchy(
    aplicacion_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener jerarquía completa de menús en estructura de árbol
    """
    try:
        menus = await crud_menu.get_menu_hierarchy(db, aplicacion_id=aplicacion_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los menús: {e}"
        )

    menu_dict = {}

    # Crear mapa por ID
    for menu in menus:
        menu_data = {
            "id": menu.id,
            "nombre": menu.nombre,
            "icono": menu.icono,
            "ruta_front": menu.ruta_front,
            "padre": menu.padre,
            "children": []
        }

        menu_dict[menu.id] = menu_data

    return _build_tree(list(menu_dict.values()))


@router.get("/by-rol", response_model=List[Dict[str, Any]], summary="Obtener menús accesibles para un rol específico")
async def get_menus_by_rol(
    db: AsyncSession = Depends(get_db),
    rol: int = Query(..., description="ID del rol"),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener menús accesibles para el usuario basado en sus roles
    y construir el árbol de menús.
    """
    from app.models.menu import Menu
    from app.models.permiso import PermisoMenu
    

    # Consulta de menús asociados a los roles del usuario y a la aplicación                
    stmt = (
            select(Menu)
            .distinct()
            .join(PermisoMenu, PermisoMenu.menu_id == Menu.id)
            .where(
                PermisoMenu.rol_id == rol,
                PermisoMenu.activo == 1,
                Menu.activo == 1
            )
            .order_by(Menu.padre.nullsfirst(), Menu.orden)
        )

    try:
        result = await db.execute(stmt)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando menús: {e}")

    menus = result.scalars().all()

    # Construir el árbol de menús
    menu_map = {
        m.id: {
            "id": m.id,
            "nombre": m.nombre,
            "url_menu": m.url_menu,
            "icono": m.icono or "solar:layers-line-duotone",
            "padre": m.padre,
            "children": []
        }
        for m in menus
    }
    return _build_tree(list(menu_map.values()))


@router.get("/by-aplicacion/{aplicacion_id}", response_model=List[MenuResponse], summary="Obtener menús por aplicación")
async def get_menus_by_aplicacion(
    aplicacion_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener menús por aplicación
    """
    skip = (page - 1) * per_page
    limit = per_page
    menus = await crud_menu.get_menus_by_aplicacion(
        db, aplicacion_id=aplicacion_id, skip=skip, limit=limit
    )
    return [MenuResponse.model_validate(menu) for menu in menus]


@router.get("/visible", response_model=List[MenuResponse], summary="Obtener solo menús visibles")
async def get_visible_menus(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener solo menús visibles
    """
    skip = (page - 1) * per_page
    limit = per_page
    menus = await crud_menu.get_visible_menus(db, skip=skip, limit=limit)
    return [MenuResponse.model_validate(menu) for menu in menus]


@router.get("/{menu_id}", response_model=MenuResponse, summary="Obtener menú por ID")
async def get_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener menú por ID
    """
    menu = await crud_menu.get(db, id=menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menú no encontrado"
        )
    return MenuResponse.model_validate(menu)


@router.post("/", response_model=MenuResponse, summary="Crear nuevo menú")
async def create_menu(
    menu_in: MenuCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crear nuevo menú
    """
    # Verificar que la URL no exista
    existing_menu = await crud_menu.get_by_url(db, url_menu=menu_in.url_menu)
    if existing_menu:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un menú con esta URL"
        )
    menu_in.id_persona = current_user.id
    
    menu = await crud_menu.create(db, obj_in=menu_in)
    return MenuResponse.model_validate(menu)


@router.put("/{menu_id}", response_model=MenuResponse, summary="Actualizar menú")
async def update_menu(
    menu_id: int,
    menu_in: MenuUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Actualizar menú
    """
    menu = await crud_menu.get(db, id=menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menú no encontrado"
        )
    menu_in.id_persona = current_user.id
    menu = await crud_menu.update(db, db_obj=menu, obj_in=menu_in)
    return MenuResponse.model_validate(menu)


@router.delete("/{menu_id}", summary="Eliminar menú (soft delete)")
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Eliminar menú (soft delete)
    """
    menu = await crud_menu.get(db, id=menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menú no encontrado"
        )
    
    await crud_menu.soft_delete(db, id=menu_id, id_persona=current_user.id)
    return {"message": "Menú eliminado correctamente"}


@router.post("/{menu_id}/reactivate", summary="Reactivar menú")
async def reactivate_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Reactivar menú
    """
    menu = await crud_menu.get(db, id=menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menú no encontrado"
        )
    
    await crud_menu.reactivate(db, id=menu_id, id_persona=current_user.id)
    return {"message": "Menú reactivado correctamente"}
