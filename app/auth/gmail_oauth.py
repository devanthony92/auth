"""
Módulo de autenticación con Gmail OAuth2
Autor: Manus AI (@Fabio Garcia)
Fecha: 2025-01-18
"""

import aiohttp
import json
from typing import Dict, Optional
from app.core.config import settings


class GmailOAuth:
    """Gestor de autenticación con Gmail OAuth2"""
    
    def __init__(self):
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret
        self.redirect_uri = settings.gmail_redirect_uri
        self.authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.scopes = [
            "openid",
            "email",
            "profile"
        ]
    
    def get_authorization_url(self, state: str) -> str:
        """
        Genera la URL de autorización para Gmail
        
        Args:
            state: Token único para prevenir CSRF
            
        Returns:
            URL de autorización
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorization_base_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Intercambia el código de autorización por tokens
        
        Args:
            code: Código de autorización de Gmail
            
        Returns:
            Diccionario con access_token y otros datos
        """
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Error intercambiando código: {error_text}")
    
    async def get_user_info(self, access_token: str) -> Dict:
        """
        Obtiene la información del usuario desde Gmail
        
        Args:
            access_token: Token de acceso de Gmail
            
        Returns:
            Información del usuario (email, nombre, etc.)
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.user_info_url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Error obteniendo información del usuario: {error_text}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresca el token de acceso usando el refresh token
        
        Args:
            refresh_token: Token de refresco de Gmail
            
        Returns:
            Nuevo access_token y otros datos
        """
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Error refrescando token: {error_text}")


# Instancia global
gmail_oauth = GmailOAuth()
