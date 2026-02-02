from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.profile import UpdateProfileRequest, ChangePasswordRequest, ProfileResponse
from app.auth.dependencies import get_current_active_user
from app.crud import usuario as crud_usuario
from app.core.security import get_password_hash, verify_password
from app.services.storage_service import send_file_to_external_service

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_user_profile(
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene la información del perfil del usuario autenticado
    """
    try:
        return ProfileResponse(
            success=True,
            message="Perfil obtenido correctamente",
            data={
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "nombres": current_user.nombres,
                "apellidos": current_user.apellidos,
                "nombre_completo": current_user.nombre_completo,
                "firma": current_user.firma,
                "foto": current_user.foto,
                "activo": current_user.activo,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el perfil: {str(e)}"
        )


@router.put("/me/actualizar", response_model=ProfileResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza los datos del perfil del usuario
    """
    try:
        # Preparar datos de actualización
        update_data = {}
        
        if profile_data.nombres is not None:
            update_data["nombres"] = profile_data.nombres
        if profile_data.apellidos is not None:
            update_data["apellidos"] = profile_data.apellidos
        if profile_data.email is not None:
            # Verificar que el email no esté en uso por otro usuario
            existing_user = await crud_usuario.get_by_email(db, email=profile_data.email)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está en uso"
                )
            update_data["email"] = profile_data.email
        if profile_data.username is not None:
            # Verificar que el username no esté en uso por otro usuario
            existing_user = await crud_usuario.get_by_username(db, username=profile_data.username)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El nombre de usuario ya está en uso"
                )
            update_data["username"] = profile_data.username
        
        # Actualizar usuario
        updated_user = await crud_usuario.update(db, db_obj=current_user, obj_in=update_data)
        
        return ProfileResponse(
            success=True,
            message="Perfil actualizado correctamente",
            data={
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "nombres": updated_user.nombres,
                "apellidos": updated_user.apellidos,
                "nombre_completo": updated_user.nombre_completo
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el perfil: {str(e)}"
        )


@router.post("/me/cambiar-contrasena", response_model=ProfileResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cambia la contraseña del usuario
    """
    try:
        # Verificar contraseña actual
        if not verify_password(password_data.current_password, current_user.hash_clave):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual es incorrecta"
            )
        
        # Verificar que las contraseñas coincidan
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las contraseñas no coinciden"
            )
        
        # Actualizar contraseña
        hashed_password = get_password_hash(password_data.new_password)
        await crud_usuario.update(db, db_obj=current_user, obj_in={"hash_clave": hashed_password})
        
        return ProfileResponse(
            success=True,
            message="Contraseña cambiada correctamente",
            data={}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar la contraseña: {str(e)}"
        )


@router.post("/me/foto-perfil", response_model=ProfileResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sube la foto de perfil del usuario
    """
    try:
        # Validar tipo de archivo
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos JPEG, JPG, PNG o GIF"
            )
        
        # Validar tamaño (4MB)
        contents = await file.read()
        if len(contents) > 4 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no puede ser mayor a 4MB"
            )
        
        # Subir al storage externo
        result = await send_file_to_external_service(file.filename, contents, subfolder="profile_photos")
        
        if result and result.get("success"):
            # Actualizar usuario con el nombre del archivo
            await crud_usuario.update(db, db_obj=current_user, obj_in={"foto": result.get("path")})
            
            return ProfileResponse(
                success=True,
                message="Foto de perfil actualizada correctamente",
                data={
                    "bucket": result.get("bucket"),
                    "path": result.get("path"),
                    "size": result.get("size"),
                    "uploaded_at": result.get("uploaded_at")
                }
            )
        else:
            print("error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Error al subir el archivo")
            )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir la foto: {str(e)}"
        )


@router.post("/me/firma", response_model=ProfileResponse)
async def upload_signature(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sube la firma del usuario
    """
    try:
        # Validar tipo de archivo
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos JPEG, JPG, PNG o GIF"
            )
        
        # Validar tamaño (2MB)
        contents = await file.read()
        if len(contents) > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no puede ser mayor a 2MB"
            )
        
        # Subir al storage externo
        result = await send_file_to_external_service(file.filename, contents, subfolder="signatures")
        
        if result and result.get("success"):
            # Actualizar usuario con el nombre del archivo
            await crud_usuario.update(db, db_obj=current_user, obj_in={"firma": result.get("path")})
            
            return ProfileResponse(
                success=True,
                message="Firma actualizada correctamente",
                data={
                    "bucket": result.get("bucket"),
                    "path": result.get("path"),
                    "size": result.get("size"),
                    "uploaded_at": result.get("uploaded_at")
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Error al subir el archivo")
            )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir la firma: {str(e)}"
        )


@router.delete("/me/foto-perfil", response_model=ProfileResponse)
async def delete_profile_photo(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina la foto de perfil del usuario
    """
    try:
        # Establecer imagen por defecto
        await crud_usuario.update(db, db_obj=current_user, obj_in={"foto": "not_found.png"})
        
        return ProfileResponse(
            success=True,
            message="Foto de perfil eliminada correctamente",
            data={"foto": "not_found.png"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la foto de perfil: {str(e)}"
        )


@router.delete("/me/firma", response_model=ProfileResponse)
async def delete_signature(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina la firma del usuario
    """
    try:
        # Establecer imagen por defecto
        await crud_usuario.update(db, db_obj=current_user, obj_in={"firma": "not_found.png"})
        
        return ProfileResponse(
            success=True,
            message="Firma eliminada correctamente",
            data={"firma": "not_found.png"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la firma: {str(e)}"
        )
