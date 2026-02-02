from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import rol as crud_rol
from app.crud import permiso_menu as crud_permiso_menu
from app.crud import permiso_api as crud_permiso_api
from app.schemas.rol import Rol, RolCreate, RolUpdate, RolResponse
from app.schemas import PaginatedResponse
from app.auth.dependencies import get_current_active_user, require_roles
from app.models.usuario import Usuario

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_roles(
    page: int = Query(0, ge=0),
    per_page: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    id_aplicacion: Optional[int] = Query(None),
    activo: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener lista de roles con paginación y filtros
    """
    # Convertir page y per_page a skip y limit si se reciben como query params
    skip = (page - 1) * per_page
    limit = per_page
    filters = {}
    if id_aplicacion is not None:
        filters["id_aplicacion"] = id_aplicacion
    if activo is not None:
        filters["activo"] = activo
    else:
        filters["activo"] = 1
    
    if search:
        roles = await crud_rol.search_roles(
            db, search_term=search, skip=skip, limit=limit
        )
        total = await crud_rol.count_search(db, search_term=search)
    else:
        roles = await crud_rol.get_multi(
            db, skip=skip, limit=limit, filters=filters
        )
        total = await crud_rol.count(db, filters=filters)
    
    
    return PaginatedResponse(
        items=[RolResponse.model_validate(rol) for rol in roles],
        total=total,
        page=page,
        per_page=per_page,
        last_page=(total + per_page - 1) // per_page,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/all", response_model=List[RolResponse])
async def get_all_roles(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todos los roles sin paginación
    """
    roles = await crud_rol.get_all(db)
    return [RolResponse.model_validate(rol) for rol in roles]


@router.get("/by-aplicacion/{aplicacion_id}", response_model=List[RolResponse])
async def get_roles_by_aplicacion(
    aplicacion_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener roles por aplicación
    """
    skip = (page - 1) * per_page
    limit = per_page
    roles = await crud_rol.get_roles_by_aplicacion(
        db, aplicacion_id=aplicacion_id, skip=skip, limit=limit
    )
    return [RolResponse.model_validate(rol) for rol in roles]


@router.get("/{rol_id}", response_model=RolResponse)
async def get_rol(
    rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener rol por ID
    """
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return RolResponse.model_validate(rol)


@router.get("/{rol_id}/menus", response_model=List[Dict[str, Any]])
async def get_menus_by_rol(
    rol_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener menús permitidos para un rol específico
    """
    skip = (page - 1) * per_page
    limit = per_page
    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Obtener menús del rol
    permisos_menu = await crud_permiso_menu.get_menus_by_rol(
        db, rol_id=rol_id, skip=skip, limit=limit
    )
    
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


@router.get("/{rol_id}/apis", response_model=List[Dict[str, Any]])
async def get_apis_by_rol(
    rol_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener APIs permitidas para un rol específico
    """
    skip = (page - 1) * per_page
    limit = per_page
    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Obtener APIs del rol
    permisos_api = await crud_permiso_api.get_apis_by_rol(
        db, rol_id=rol_id, skip=skip, limit=limit
    )
    
    apis = []
    for permiso in permisos_api:
        if permiso.api_obj:
            api = permiso.api_obj
            apis.append({
                "id": api.id,
                "nombre": api.nombre,
                "url_api": api.url_api,
                "grupo": api.grupo,
                "class_front": api.class_front,
                "tipo_accion": api.tipo_accion,
                "descripcion": api.descripcion,
                "id_aplicacion": api.id_aplicacion,
                "activo": api.activo
            })
    
    return apis


@router.get("/{rol_id}/aplicaciones", response_model=List[Dict[str, Any]])
async def get_aplicaciones_by_rol(
    rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener aplicaciones permitidas para un rol específico
    """
    # Verificar que el rol existe
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    from app.crud import aplicacion as crud_aplicacion
    
    # Obtener aplicación del rol
    aplicacion = await crud_aplicacion.get(db, id=rol.id_aplicacion)
    
    aplicaciones = []
    if aplicacion:
        aplicaciones.append({
            "id": aplicacion.id,
            "key": aplicacion.key,
            "nombre": aplicacion.nombre,
            "descripcion": aplicacion.descripcion
        })
    
    return aplicaciones


@router.post("/", response_model=RolResponse)
async def create_rol(
    rol_in: RolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Crear nuevo rol
    """
    # Verificar que el nombre no exista
    existing_rol = await crud_rol.get_by_nombre(db, nombre=rol_in.nombre)
    if existing_rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un rol con este nombre"
        )
    
    # Verificar key_publico si se proporciona
    if rol_in.key_publico:
        existing_key = await crud_rol.get_by_key_publico(db, key_publico=rol_in.key_publico)
        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un rol con esta clave pública"
            )
    rol_in.id_persona = current_user.id  # Asignar id_persona desde el JWT
    rol = await crud_rol.create(db, obj_in=rol_in)
    return RolResponse.model_validate(rol)


@router.put("/{rol_id}", response_model=RolResponse)
async def update_rol(
    rol_id: int,
    rol_in: RolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Actualizar rol
    """
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    rol_in.id_persona = current_user.id  # Asignar id_persona desde el JWT
    rol = await crud_rol.update(db, db_obj=rol, obj_in=rol_in)
    return RolResponse.model_validate(rol)


@router.delete("/{rol_id}")
async def delete_rol(
    rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Eliminar rol (soft delete)
    """
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    await crud_rol.soft_delete(db, id=rol_id, id_persona=current_user.id)
    return {"message": "Rol eliminado correctamente"}


@router.post("/{rol_id}/reactivate")
async def reactivate_rol(
    rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Reactivar rol
    """
    rol = await crud_rol.get(db, id=rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    await crud_rol.reactivate(db, id=rol_id, id_persona=current_user.id)
    return {"message": "Rol reactivado correctamente"}

