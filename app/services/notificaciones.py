"""
Servicio de notificaciones para la aplicación.
"""

from app.core.config import settings
import httpx


class NotificationService:
    @staticmethod
    async def send_email(payload: dict) -> dict:
        """
        Envía un correo electrónico utilizando un servicio externo vía API.
        Args:
            payload: Diccionario con los datos del correo (to, subject, body, etc.)
        Returns:
            Respuesta del servicio de correo.
        Raises:
            httpx.HTTPError: Si hay un error en la solicitud HTTP.
        """
        EMAIL_API_URL = settings.base_url_notificaciones + "/api/send/email"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                EMAIL_API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    # "Authorization": "Bearer <token>"  # si aplica
                }
            )

            response.raise_for_status()
            return response.json()