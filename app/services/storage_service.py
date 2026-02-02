"""
Helper para compatibilidad con el servicio de storage
Autor: Fabio Garcia
Fecha: 2025-11-27
"""

from app.services.storages import storage_service
from typing import Dict, Any, Optional
from app.core.config import settings
import aiohttp
import logging


async def send_file_to_external_service(filename: str, file_content: bytes, subfolder: Optional[str] = None) -> Dict[str, Any]:
    """
    Función síncrona wrapper para subir archivos al servicio de storage
    Esta función es para compatibilidad con código existente
    
    Args:
        filename: Nombre del archivo
        file_content: Contenido del archivo en bytes
        subfolder: Subcarpeta donde se guardará el archivo
    
    Returns:
        Dict con el resultado de la operación
    """
    
    try:
        api_url = settings.base_url_storage + "/v1/api/cloud/oracle"
        api_key = settings.key_storage

        headers = {
            "X-API-Key": api_key
        }

        data = aiohttp.FormData()
        if subfolder:
            data.add_field('prefix', subfolder)
        else:
            data.add_field('prefix', 'general-files')
        data.add_field('file', file_content, filename=filename, content_type='application/octet-stream')
        data.add_field('object_name', filename)
        data.add_field('bucket', 'Bucket-test')

        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, data=data) as resp:
                resp.raise_for_status()
                result = await resp.json()
                # Se espera que la API retorne la ruta del archivo guardado
                data = result.get("data", {})
                if not result.get("success"):
                    print("error en upload")
                    return { "message": result.get("message"), "status": "error" }
                else:
                    return {
                        "success": True,
                        "message": result.get("message"),
                        "bucket": data.get("bucket"),
                        "path": data.get("key"),
                        "size": data.get("size"),
                        "uploaded_at": data.get("uploaded_at")
                        
                    }
        
    except Exception as e:
        logging.error(f"Error subiendo archivo: {e}")
        return {"status": "error", "message": str(e)}


# async def send_file_to_external_service(filename: str, file_content: bytes, subfolder: str) -> Dict[str, Any]:
#     """
#     Función síncrona wrapper para subir archivos al servicio de storage
#     Esta función es para compatibilidad con código existente
    
#     Args:
#         filename: Nombre del archivo
#         file_content: Contenido del archivo en bytes
#         subfolder: Subcarpeta donde se guardará el archivo
    
#     Returns:
#         Dict con el resultado de la operación
#     """
    
#     try:
#         # Ejecutar la función asíncrona de manera síncrona
#         result = await storage_service.upload_file(
#             file_content=file_content,
#             filename=filename,
#             subfolder=subfolder
#         )
        
#         # Adaptar el formato de respuesta
#         if result.get("status") == "success":
#             return {
#                 "success": True,
#                 "message": result.get("message", "Archivo subido correctamente"),
#                 "filename": result.get("relative_path", filename),
#                 "url": result.get("path", "")
#             }
#         else:
#             return {
#                 "success": False,
#                 "error": result.get("message", "Error al subir el archivo")
#             }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }
