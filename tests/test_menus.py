"""
Pruebas unitarias para el endpoint de menús
Actualizado: 2025-12-27
Autor: Fabio Garcia
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestMenusEndpoints:
    """Pruebas para los endpoints de menús"""
    
    def test_health_check(self):
        """Verifica que el servidor esté funcionando"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Verifica que el endpoint raíz funciona"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_menus_endpoint_requires_auth(self):
        """Verifica que el endpoint de menús requiere autenticación"""
        response = client.get("/api/v1/menus/")
        # El endpoint retorna 403 (Forbidden) cuando no está autenticado
        assert response.status_code in [401, 403]
    
    def test_menus_by_user_requires_auth(self):
        """Verifica que el endpoint de menús por usuario requiere autenticación"""
        response = client.get("/api/v1/menus/by-user")
        # El endpoint retorna 403 (Forbidden) cuando no está autenticado
        assert response.status_code in [401, 403]
    
    def test_menus_hierarchy_requires_auth(self):
        """Verifica que el endpoint de jerarquía de menús requiere autenticación"""
        response = client.get("/api/v1/menus/hierarchy")
        # El endpoint retorna 403 (Forbidden) cuando no está autenticado
        assert response.status_code in [401, 403]


class TestMenuStructure:
    """Pruebas para la estructura de menús"""
    
    def test_menu_model_fields(self):
        """Verifica que el modelo de menú tiene los campos correctos"""
        from app.models.menu import Menu
        
        # Verificar que el modelo tiene los campos esperados
        assert hasattr(Menu, 'id')
        assert hasattr(Menu, 'nombre')
        assert hasattr(Menu, 'url_menu')
        assert hasattr(Menu, 'padre')
        assert hasattr(Menu, 'ruta_front')
        assert hasattr(Menu, 'icono')
        assert hasattr(Menu, 'activo')
        assert hasattr(Menu, 'visible')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
