from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import aplicacion as crud_aplicacion
from app.schemas.aplicacion import Aplicacion, AplicacionCreate, AplicacionUpdate, AplicacionResponse
from app.schemas import PaginatedResponse
from app.auth.dependencies import get_current_active_user, require_roles
from app.models.usuario import Usuario

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
async def get_aplicaciones(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    search: Optional[str] = Query(None),
    activo: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    skip = (page - 1) * per_page
    limit = per_page
    filters = {}
    if activo is not None:
        filters["activo"] = activo

    if search:
        aplicaciones = await crud_aplicacion.search_aplicaciones(
            db, search_term=search, skip=skip, limit=limit
        )
        total = await crud_aplicacion.count_search(db, search_term=search)
    else:
        aplicaciones = await crud_aplicacion.get_multi(
            db, skip=skip, limit=limit, filters=filters
        )
        total = await crud_aplicacion.count(db, filters=filters)

    

    return PaginatedResponse(
        items=[AplicacionResponse.model_validate(app) for app in aplicaciones],
        total=total,
        page=page,
        per_page=per_page,
        last_page=(total + per_page - 1) // per_page,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/all", response_model=List[AplicacionResponse])
async def get_all_aplicaciones(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    aplicaciones = await crud_aplicacion.get_all(db)
    return [AplicacionResponse.model_validate(app) for app in aplicaciones]


@router.get("/{aplicacion_id}", response_model=AplicacionResponse)
async def get_aplicacion(
    aplicacion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    aplicacion = await crud_aplicacion.get(db, id=aplicacion_id)
    if not aplicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aplicación no encontrada"
        )
    return AplicacionResponse.model_validate(aplicacion)


@router.post("/", response_model=AplicacionResponse)
async def create_aplicacion(
    aplicacion_in: AplicacionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPERADMIN"]))
):
    existing_app = await crud_aplicacion.get_by_key(db, key=aplicacion_in.key)
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una aplicación con este key"
        )
    
    aplicacion = await crud_aplicacion.create(db, obj_in=aplicacion_in)
    return AplicacionResponse.model_validate(aplicacion)


@router.put("/{aplicacion_id}", response_model=AplicacionResponse)
async def update_aplicacion(
    aplicacion_id: int,
    aplicacion_in: AplicacionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPERADMIN"]))
):
    aplicacion = await crud_aplicacion.get(db, id=aplicacion_id)
    if not aplicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aplicación no encontrada"
        )
    aplicacion = await crud_aplicacion.update(db, db_obj=aplicacion, obj_in=aplicacion_in)
    return AplicacionResponse.model_validate(aplicacion)


@router.delete("/{aplicacion_id}")
async def delete_aplicacion(
    aplicacion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPERADMIN"]))
):
    aplicacion = await crud_aplicacion.get(db, id=aplicacion_id)
    if not aplicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aplicación no encontrada"
        )
    await crud_aplicacion.soft_delete(db, id=aplicacion_id)
    return {"message": "Aplicación eliminada correctamente"}


@router.post("/{aplicacion_id}/reactivate")
async def reactivate_aplicacion(
    aplicacion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPERADMIN"]))
):
    aplicacion = await crud_aplicacion.get(db, id=aplicacion_id)
    if not aplicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aplicación no encontrada"
        )
    await crud_aplicacion.reactivate(db, id=aplicacion_id)
    return {"message": "Aplicación reactivada correctamente"}
