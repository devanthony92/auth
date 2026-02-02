from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import usuario as crud_usuario
from app.auth.user_data import (
    get_users_roles_map,
    get_roles_aplicaciones_map
)
from app.schemas.usuario import (
    Usuario, UsuarioChangePasswordAdmin, UsuarioCreate, UsuarioUpdate, UsuarioResponse, 
    UsuarioChangePassword
)
from app.schemas import PaginatedResponse
from app.auth.dependencies import get_current_active_user, require_roles
from app.models.usuario import Usuario as UsuarioModel
from fastapi import File, UploadFile, Form
from app.services.storages import storage_service
from fastapi.responses import StreamingResponse
import io
from sqlalchemy import select
router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_usuarios(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    activo: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener lista de usuarios con paginación y filtros
    """
    skip = (page - 1) * per_page
    limit = per_page
    filters = {}
    if activo is not None:
        filters["activo"] = activo
    else:
        filters["activo"] = 1
    # Si hay término de búsqueda, usar búsqueda avanzada
    if search:
        usuarios = await crud_usuario.search_users(
            db, search_term=search, skip=skip, limit=limit
        )
        total = await crud_usuario.count_search(db, search_term=search)
    else:
        usuarios = await crud_usuario.get_multi(
            db, skip=skip, limit=limit, filters=filters
        )
        total = await crud_usuario.count(db, filters=filters)

    items = []
    # Si no hay usuarios, retornar paginación vacía
    if not usuarios:
            return PaginatedResponse(
                items=items,
                total=total,
                page=page,
                per_page=per_page,
                last_page=(total + per_page - 1) // per_page,
                size=limit,
                pages=(total + limit - 1) // limit
            )
        
    # Construir lista de usuarios con roles y aplicaciones
    usuarios_out = [UsuarioResponse.model_validate(u) for u in usuarios]

    user_ids = [u.id for u in usuarios_out]

    roles_map = await get_users_roles_map(db, user_ids)

    role_ids = {
        rol["id_rol"]
        for roles in roles_map.values()
        for rol in roles
    }

    applications = []
    if role_ids:
        applications = await get_roles_aplicaciones_map(db, list(role_ids))

    items = []
    for user in usuarios_out:
        data = user.model_dump()
        data["roles"] = roles_map.get(user.id, [])
        data["aplicaciones"] = applications
        items.append(data)


    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        last_page=(total + per_page - 1) // per_page,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/all", response_model=List[UsuarioResponse])
async def get_all_usuarios(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todos los usuarios sin paginación
    """
    usuarios = await crud_usuario.get_all(db)
    return [UsuarioResponse.model_validate(usuario) for usuario in usuarios]


@router.get("/active", response_model=List[UsuarioResponse])
async def get_active_usuarios(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener solo usuarios activos
    """
    skip = (page - 1) * per_page
    limit = per_page
    usuarios = await crud_usuario.get_active(db, skip=skip, limit=limit)
    return [UsuarioResponse.model_validate(usuario) for usuario in usuarios]


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener usuario por ID
    """
    usuario = await crud_usuario.get(db, id=usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return UsuarioResponse.model_validate(usuario)


@router.post("/", response_model=UsuarioResponse)
async def create_usuario(
    usuario_in: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crear nuevo usuario
    """
    # Verificar que el email no exista
    existing_user = await crud_usuario.get_by_email(db, email=usuario_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con este email"
        )
    
    # Verificar que el username no exista
    existing_username = await crud_usuario.get_by_username(db, username=usuario_in.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con este username"
        )
    
    usuario = await crud_usuario.create(db, obj_in=usuario_in)
    return UsuarioResponse.model_validate(usuario)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: int,
    usuario_in: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Actualizar usuario
    """
    usuario = await crud_usuario.get(db, id=usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario = await crud_usuario.update(db, db_obj=usuario, obj_in=usuario_in)
    return UsuarioResponse.model_validate(usuario)


@router.delete("/{usuario_id}")
async def delete_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Eliminar usuario (soft delete)
    """
    usuario = await crud_usuario.get(db, id=usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    await crud_usuario.soft_delete(db, id=usuario_id, id_persona=current_user.id)
    return {"message": "Usuario eliminado correctamente"}


@router.post("/{usuario_id}/reactivate")
async def reactivate_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Reactivar usuario
    """
    usuario = await crud_usuario.get(db, id=usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    await crud_usuario.reactivate(db, id=usuario_id, id_persona=current_user.id)
    return {"message": "Usuario reactivado correctamente"}


@router.post("/change-password")
async def change_password(
    password_data: UsuarioChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_active_user)
):
    """
    Cambiar contraseña del usuario actual
    """
    # Verificar contraseña actual
    if not crud_usuario.verify_password(password_data.current_password, current_user.hash_clave):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    await crud_usuario.update_password(
        db, db_obj=current_user, new_password=password_data.new_password
    )
    
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/change-password-admin")
async def change_password_admin(
    password_data: UsuarioChangePasswordAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["ADMIN","SUPERADMIN"]))
):
    """
    Cambiar contraseña del usuario admin
    """
    usuario = await crud_usuario.get(db, id=password_data.usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar contraseña
    await crud_usuario.update_password(
        db, db_obj=usuario, new_password=password_data.new_password
    )
    
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    subfolder: str = Form(...),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Subir foto de perfil del usuario y actualizar la información
    """
    usuario_id = current_user.id
    usuario = await crud_usuario.get(db, id=usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    # Subir archivo al servicio externo
    file_content = await file.read()
    url = await storage_service.upload_file(file_content=file_content, subfolder=subfolder, filename=file.filename)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo subir el archivo"
        )
    if url['status']=='error':
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=url['message']
        ) 
    # Actualizar usuario con la url
    if subfolder == "firma":
        await crud_usuario.update(db, db_obj=usuario, obj_in={"firma": url['relative_path']})
    else:
        await crud_usuario.update(db, db_obj=usuario, obj_in={"foto": url['relative_path']})
    return {"message": "Archivo actualizado correctamente", "url": url['relative_path']}


@router.post("/get-file")
async def get_file(
    file: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Descargar archivo del servicio externo
    """
    url = await storage_service.download_file(file)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo descargar el archivo"
        )
    filename = file.split("/")[-1]
    return StreamingResponse(
            io.BytesIO(url),
            media_type='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(url))
            }
        )


@router.post("/batch", response_model=List[UsuarioResponse])
async def get_all_usuarios(
    ids:  str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todos los usuarios sin paginación
    """
    if ids:
        ids = [int(id.strip()) for id in ids.split(",") if id.strip().isdigit()]
    result = await db.execute(
        select(UsuarioModel).where(UsuarioModel.id.in_(ids))
    )
    usuarios = result.scalars().all()
    return [UsuarioResponse.model_validate(usuario) for usuario in usuarios]