"""
Servicio asíncrono para gestionar archivos.
"""

import asyncio
import logging
from typing import List, Dict, Optional, BinaryIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings
import aiohttp


class StorageService:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=20)

    async def upload_file(
        self,
        file_content: bytes,
        filename: Optional[str] = None,
        subfolder: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Subir un archivo de manera asíncrona.
        
        Args:
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo a subir
            subfolder: Carpeta en la que se subirá el archivo

        Returns:
            Dict con información del archivo subido
            
        Raises:
            Exception: Si hay error en la subida
        """
        try:
            api_url = settings.base_url_storage + "/v1/api/local/upload"
            api_key = settings.key_storage

            headers = {
                "X-API-Key": api_key
            }

            data = aiohttp.FormData()
            if subfolder:
                data.add_field('subfolder', subfolder)
            data.add_field('file', file_content, filename=filename, content_type='application/octet-stream')

            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, data=data) as resp:
                    resp.raise_for_status()
                    result = await resp.json()
                    # Se espera que la API retorne la ruta del archivo guardado
                    data = result.get("data", {})
                    if not result.get("success"):
                        return { "message": result.get("message"), "status": "error" }
                    else:
                        return {
                            "message": result.get("message"),
                            "relative_path": data.get("relative_path"),
                            "path": data.get("path"),
                            "status": "success"
                        }
            
        except Exception as e:
            logging.error(f"Error subiendo archivo: {e}")
            return {"status": "error", "message": str(e)}

    async def download_file(self, key: str) -> bytes:
        """
        Descargar un archivo de manera asíncrona.
        
        Args:
            key: Clave del archivo en S3
           
            
        Returns:
            bytes: Contenido del archivo
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            Exception: Si hay error en la descarga
        """
        try:
            api_url = settings.base_url_storage + "/v1/api/local/download/{file_path}".format(file_path=key)
            api_key = settings.key_storage

            headers = {
                "X-API-Key": api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as resp:
                    if resp.status == 404:
                        raise FileNotFoundError(f"Archivo no encontrado: {key}")
                    resp.raise_for_status()
                    # La API responde con un archivo, así que devolvemos el contenido binario
                    return await resp.read()
            
        except Exception as e:
            logging.error(f"Error inesperado descargando {key}: {e}")
            return {"status": "error", "message": str(e)}
    

# Instancia global del servicio de almacenamiento
storage_service = StorageService()

