from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import api as crud_api
from app.schemas.api import Api, ApiCreate, ApiUpdate, ApiResponse
from app.schemas import PaginatedResponse
from app.auth.dependencies import get_current_active_user, require_roles
from app.models.usuario import Usuario

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_apis(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    search: Optional[str] = Query(None),
    id_aplicacion: Optional[int] = Query(None),
    grupo: Optional[str] = Query(None),
    tipo_accion: Optional[int] = Query(None),
    activo: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener lista de APIs con paginación y filtros
    """
    skip = (page - 1) * per_page
    limit = per_page

    filters = {}
    if id_aplicacion is not None:
        filters["id_aplicacion"] = id_aplicacion
    if grupo is not None:
        filters["grupo"] = grupo
    if tipo_accion is not None:
        filters["tipo_accion"] = tipo_accion
    if activo is not None:
        filters["activo"] = activo
    
    if search:
        apis = await crud_api.search_apis(
            db, search_term=search, skip=skip, limit=limit
        )
        total = await crud_api.count_search(db, search_term=search)
    else:
        apis = await crud_api.get_multi(
            db, skip=skip, limit=limit, filters=filters
        )
        total = await crud_api.count(db, filters=filters)
    
    
    
    return PaginatedResponse(
        items=[ApiResponse.model_validate(api) for api in apis],
        total=total,
        page=page,
        per_page=per_page,
        last_page=(total + per_page - 1) // per_page,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/by-aplicacion/{aplicacion_id}", response_model=List[ApiResponse])
async def get_apis_by_aplicacion(
    aplicacion_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener APIs por aplicación
    """
    skip = (page - 1) * per_page
    limit = per_page
    apis = await crud_api.get_apis_by_aplicacion(
        db, aplicacion_id=aplicacion_id, skip=skip, limit=limit
    )
    return [ApiResponse.model_validate(api) for api in apis]


@router.get("/by-grupo/{grupo}", response_model=List[ApiResponse])
async def get_apis_by_grupo(
    grupo: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener APIs por grupo
    """
    skip = (page - 1) * per_page
    limit = per_page
    apis = await crud_api.get_apis_by_grupo(
        db, grupo=grupo, skip=skip, limit=limit
    )
    return [ApiResponse.model_validate(api) for api in apis]


@router.get("/by-tipo-accion/{tipo_accion}", response_model=List[ApiResponse])
async def get_apis_by_tipo_accion(
    tipo_accion: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener APIs por tipo de acción
    """
    skip = (page - 1) * per_page
    limit = per_page
    apis = await crud_api.get_apis_by_tipo_accion(
        db, tipo_accion=tipo_accion, skip=skip, limit=limit
    )
    return [ApiResponse.model_validate(api) for api in apis]


@router.get("/{api_id}", response_model=ApiResponse)
async def get_api(
    api_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener API por ID
    """
    
    api = await crud_api.get(db, id=api_id)
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API no encontrada"
        )
    return ApiResponse.model_validate(api)


@router.post("/", response_model=ApiResponse)
async def create_api(
    api_in: ApiCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Crear nueva API
    """
    # Verificar que la URL no exista
    existing_api = await crud_api.get_by_url(db, url_api=api_in.url_api)
    if existing_api:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una API con esta URL"
        )
    api_in.id_persona = current_user.id
    api = await crud_api.create(db, obj_in=api_in)
    return ApiResponse.model_validate(api)


@router.put("/{api_id}", response_model=ApiResponse)
async def update_api(
    api_id: int,
    api_in: ApiUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Actualizar API
    """
    api = await crud_api.get(db, id=api_id)
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API no encontrada"
        )
    api_in.id_persona = current_user.id
    api = await crud_api.update(db, db_obj=api, obj_in=api_in)
    return ApiResponse.model_validate(api)


@router.delete("/{api_id}")
async def delete_api(
    api_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Eliminar API (soft delete)
    """
    api = await crud_api.get(db, id=api_id)
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API no encontrada"
        )
    
    await crud_api.soft_delete(db, id=api_id, id_persona=current_user.id)
    return {"message": "API eliminada correctamente"}


@router.post("/{api_id}/reactivate")
async def reactivate_api(
    api_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Reactivar API
    """
    api = await crud_api.get(db, id=api_id)
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API no encontrada"
        )
    
    await crud_api.reactivate(db, id=api_id, id_persona=current_user.id)
    return {"message": "API reactivada correctamente"}

