"""
Pruebas unitarias para el endpoint /menus/tree
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Crear cliente de prueba"""
    return TestClient(app)

def test_get_menu_tree_endpoint_exists(client):
    """Prueba: verificar que el endpoint /menus/tree existe"""
    response = client.get("/api/v1/menus/tree")
    # No debe ser 404 (endpoint no existe)
    assert response.status_code != 404, "Endpoint /menus/tree no encontrado"
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_menu_tree_rol_endpoint_exists(client):
    """Prueba: verificar que el endpoint /menus/tree/rol/{rol_id} existe"""
    response = client.get("/api/v1/menus/tree/rol/1")
    # No debe ser 404 (endpoint no existe)
    assert response.status_code != 404, "Endpoint /menus/tree/rol/{rol_id} no encontrado"
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_api_endpoints(client):
    """Prueba: verificar que los endpoints de API están disponibles"""
    response = client.get("/api/v1/menus")
    print(f"GET /api/v1/menus - Status: {response.status_code}")
    
    response = client.get("/api/v1/menus/tree")
    print(f"GET /api/v1/menus/tree - Status: {response.status_code}")
    
    response = client.get("/api/v1/menus/tree/rol/1")
    print(f"GET /api/v1/menus/tree/rol/1 - Status: {response.status_code}")
