from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from app.core.database import get_db
from app.crud import usuario_rol as crud_usuario_rol
from app.crud import usuario as crud_usuario
from app.schemas.usuario_rol import UsuarioRolCreate, UsuarioRolUpdate, UsuarioRolResponse
from app.schemas import PaginatedResponse
from app.auth.dependencies import get_current_active_user, require_roles
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.usuario_rol import UsuarioRol
from app.schemas.usuario_rol import UsuarioRolBulkAssignRequest, UsuarioRolResponse

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
async def get_usuario_roles(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    skip = (page - 1) * per_page
    limit = per_page
    usuario_roles = await crud_usuario_rol.get_multi(db, skip=skip, limit=limit)
    total = await crud_usuario_rol.count(db)
    return PaginatedResponse(
        items=[UsuarioRolResponse.model_validate(ur) for ur in usuario_roles],
        total=total,
        page=page,
        per_page=per_page,
        last_page=(total + per_page - 1) // per_page,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.get("/all", response_model=List[UsuarioRolResponse])
async def get_all_usuario_roles(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    usuario_roles = await crud_usuario_rol.get_all(db)
    return [UsuarioRolResponse.model_validate(ur) for ur in usuario_roles]

@router.get("/{usuario_rol_id}", response_model=UsuarioRolResponse)
async def get_usuario_rol(
    usuario_rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    usuario_rol = await crud_usuario_rol.get(db, id=usuario_rol_id)
    if not usuario_rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UsuarioRol no encontrado"
        )
    return UsuarioRolResponse.model_validate(usuario_rol)

@router.post("/", response_model=UsuarioRolResponse)
async def create_usuario_rol(
    usuario_rol_in: UsuarioRolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    usuario_rol_in.id_persona = current_user.id
    usuario_rol = await crud_usuario_rol.create(db, obj_in=usuario_rol_in)
    return UsuarioRolResponse.model_validate(usuario_rol)

@router.put("/{usuario_rol_id}", response_model=UsuarioRolResponse)
async def update_usuario_rol(
    usuario_rol_id: int,
    usuario_rol_in: UsuarioRolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    usuario_rol = await crud_usuario_rol.get(db, id=usuario_rol_id)
    if not usuario_rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UsuarioRol no encontrado"
        )
    usuario_rol_in.id_persona = current_user.id
    usuario_rol = await crud_usuario_rol.update(db, db_obj=usuario_rol, obj_in=usuario_rol_in)
    return UsuarioRolResponse.model_validate(usuario_rol)

@router.delete("/{usuario_rol_id}")
async def delete_usuario_rol(
    usuario_rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    usuario_rol = await crud_usuario_rol.get(db, id=usuario_rol_id)
    if not usuario_rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UsuarioRol no encontrado"
        )
    await crud_usuario_rol.soft_delete(db, id=usuario_rol_id, id_persona=current_user.id)
    return {"message": "UsuarioRol eliminado correctamente"}

@router.post("/{usuario_rol_id}/reactivate")
async def reactivate_usuario_rol(
    usuario_rol_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    usuario_rol = await crud_usuario_rol.get(db, id=usuario_rol_id)
    if not usuario_rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UsuarioRol no encontrado"
        )
    await crud_usuario_rol.reactivate(db, id=usuario_rol_id, id_persona=current_user.id)
    return {"message": "UsuarioRol reactivado correctamente"}

@router.post("/bulk-assign")
async def bulk_assign_roles_to_usuario(
    bulk_assign: UsuarioRolBulkAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
):
    try:
        user = await crud_usuario.get(db, id=bulk_assign.id_usuario)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario especificado no existe"
            )

        # Elimina roles previos del usuario (opcional, según tu lógica de negocio)
        deleted_roles = await crud_usuario_rol.remove_all_roles_from_usuario(db, usuario_id=user.id)
        
        # Validar qué IDs existen realmente en una sola consulta
        result = await db.execute(
                select(Rol.id).where(Rol.id.in_(bulk_assign.usuario_roles))
        )
        roles_find = [row[0] for row in result.all()]
        roles_not_find = list(set(bulk_assign.usuario_roles) - set(roles_find))
        
        # Inserción masiva (bulk insert)
        if roles_find:
                data_to_insert = [{
                    "id_usuario": bulk_assign.id_usuario,
                    "id_rol": r_id,
                    "id_persona": current_user.id
                    } for r_id in roles_find]
                await db.execute(insert(UsuarioRol), data_to_insert)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al asignar roles: {str(e)}"
        )


    return JSONResponse(
            status_code=status.HTTP_207_MULTI_STATUS if roles_not_find else status.HTTP_200_OK,
            content={
                "status": "Partial success" if roles_not_find else "Success",
                "data": {
                    "roles_asignados": roles_find,
                    "roles_no_asignados": roles_not_find
                }
            }
        )