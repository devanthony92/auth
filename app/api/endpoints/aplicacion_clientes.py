from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import aplicacion_cliente as crud_aplicacion_cliente
from app.schemas.aplicacion_cliente import (
    AplicacionClienteCreate,
    AplicacionClienteUpdate,
    AplicacionClienteResponse
)
from app.schemas import PaginatedResponse
from app.auth.dependencies import get_current_active_user, require_roles
from app.models.usuario import Usuario

router = APIRouter(prefix="/aplicacion_clientes", tags=["aplicacion_clientes"])

@router.get("/", response_model=PaginatedResponse)
async def get_aplicacion_clientes(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    skip = (page - 1) * per_page
    limit = per_page
    aplicacion_clientes = await crud_aplicacion_cliente.get_multi(db, skip=skip, limit=limit)
    total = await crud_aplicacion_cliente.count(db)
    return PaginatedResponse(
        items=[AplicacionClienteResponse.model_validate(ac) for ac in aplicacion_clientes],
        total=total,
        page=page,
        per_page=per_page,
        last_page=(total + per_page - 1) // per_page,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.get("/all", response_model=List[AplicacionClienteResponse])
async def get_all_aplicacion_clientes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    aplicacion_clientes = await crud_aplicacion_cliente.get_all(db)
    return [AplicacionClienteResponse.model_validate(ac) for ac in aplicacion_clientes]

@router.get("/{aplicacion_cliente_id}", response_model=AplicacionClienteResponse)
async def get_aplicacion_cliente(
    aplicacion_cliente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    aplicacion_cliente = await crud_aplicacion_cliente.get(db, id=aplicacion_cliente_id)
    if not aplicacion_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AplicacionCliente no encontrado"
        )
    return AplicacionClienteResponse.model_validate(aplicacion_cliente)

@router.post("/", response_model=AplicacionClienteResponse)
async def create_aplicacion_cliente(
    aplicacion_cliente_in: AplicacionClienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    aplicacion_cliente = await crud_aplicacion_cliente.create(db, obj_in=aplicacion_cliente_in)
    return AplicacionClienteResponse.model_validate(aplicacion_cliente)

@router.put("/{aplicacion_cliente_id}", response_model=AplicacionClienteResponse)
async def update_aplicacion_cliente(
    aplicacion_cliente_id: int,
    aplicacion_cliente_in: AplicacionClienteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    aplicacion_cliente = await crud_aplicacion_cliente.get(db, id=aplicacion_cliente_id)
    if not aplicacion_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AplicacionCliente no encontrado"
        )
    aplicacion_cliente = await crud_aplicacion_cliente.update(db, db_obj=aplicacion_cliente, obj_in=aplicacion_cliente_in)
    return AplicacionClienteResponse.model_validate(aplicacion_cliente)

@router.delete("/{aplicacion_cliente_id}")
async def delete_aplicacion_cliente(
    aplicacion_cliente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    aplicacion_cliente = await crud_aplicacion_cliente.get(db, id=aplicacion_cliente_id)
    if not aplicacion_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AplicacionCliente no encontrado"
        )
    await crud_aplicacion_cliente.soft_delete(db, id=aplicacion_cliente_id)
    return {"message": "AplicacionCliente eliminado correctamente"}

@router.post("/{aplicacion_cliente_id}/reactivate")
async def reactivate_aplicacion_cliente(
    aplicacion_cliente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    aplicacion_cliente = await crud_aplicacion_cliente.get(db, id=aplicacion_cliente_id)
    if not aplicacion_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AplicacionCliente no encontrado"
        )
    await crud_aplicacion_cliente.reactivate(db, id=aplicacion_cliente_id)
    return {"message": "AplicacionCliente reactivado correctamente"}
