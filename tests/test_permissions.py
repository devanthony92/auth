
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_save_permissions(client):
    """Prueba: guardar permisos para un rol"""
    # Asume que el rol 1 existe
    rol_id = 1
    # Asume que los menu_ids 1, 2, 3 existen
    menu_ids = [1, 2, 3]
    
    response = client.post(f"/api/v1/permisos/menu/rol/{rol_id}/bulk", json=menu_ids)
    
    assert response.status_code != 404, "Endpoint no encontrado"
    # Se espera un 403 porque no estamos autenticados
    assert response.status_code == 403, f"Se esperaba 403 pero se obtuvo {response.status_code}"
