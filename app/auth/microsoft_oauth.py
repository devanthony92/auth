import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.core.config import settings


class MicrosoftOAuth:
    """Cliente para autenticación con Microsoft OAuth2"""
    
    def __init__(self):
        self.client_id = settings.microsoft_client_id
        self.client_secret = settings.microsoft_client_secret
        self.tenant_id = settings.microsoft_tenant_id
        self.redirect_uri = settings.microsoft_redirect_uri
        
        # URLs de Microsoft
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"
        self.userinfo_endpoint = "https://graph.microsoft.com/v1.0/me"
        
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generar URL de autorización para Microsoft"""
        scopes = "openid profile email User.Read"
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": scopes,
            "response_mode": "query"
        }
        
        if state:
            params["state"] = state
            
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authority}/oauth2/v2.0/authorize?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Intercambiar código de autorización por token de acceso"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email User.Read"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data=data,
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al obtener token: {response.text}"
                )
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Obtener información del usuario desde Microsoft Graph"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_endpoint,
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al obtener información del usuario: {response.text}"
                )
            
            return response.json()
    
    async def validate_token(self, access_token: str) -> bool:
        """Validar token de acceso"""
        try:
            await self.get_user_info(access_token)
            return True
        except:
            return False


# Instancia global del cliente OAuth
microsoft_oauth = MicrosoftOAuth()

