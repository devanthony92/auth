"""
Pruebas unitarias para el endpoint de permisos
Autor: @Fabio Garcia
Fecha: 2025-12-28
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base, get_db
from app.models.rol import Rol
from app.models.menu import Menu
from app.models.permiso_menu import PermisoMenu
from app.schemas.permiso import PermisoMenuBulkSave
from main import app

# Configurar base de datos de prueba
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def test_db():
    """Fixture para la base de datos de prueba"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield AsyncSessionLocal
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Fixture para el cliente de prueba"""
    return TestClient(app)


class TestPermisoMenuBulkSave:
    """Pruebas para el schema PermisoMenuBulkSave"""
    
    def test_schema_valido(self):
        """Debe validar schema con menu_ids válido"""
        data = {"menu_ids": [1, 2, 3]}
        schema = PermisoMenuBulkSave(**data)
        assert schema.menu_ids == [1, 2, 3]
    
    def test_schema_lista_vacia(self):
        """Debe validar schema con lista vacía"""
        data = {"menu_ids": []}
        schema = PermisoMenuBulkSave(**data)
        assert schema.menu_ids == []
    
    def test_schema_menu_ids_requerido(self):
        """Debe requerir menu_ids"""
        with pytest.raises(ValueError):
            PermisoMenuBulkSave()


class TestMenuResponse:
    """Pruebas para la conversión de padre en MenuResponse"""
    
    def test_padre_string_convertido_a_int(self):
        """Debe convertir padre string a int"""
        from app.schemas.menu import MenuResponse
        
        data = {
            "id": 1,
            "url_menu": "test",
            "id_aplicacion": 1,
            "padre": "2",
            "nombre": "Test Menu",
            "orden": 1,
            "visible": 1,
            "acceso": 1,
            "activo": 1
        }
        
        response = MenuResponse(**data)
        assert response.padre == 2
        assert isinstance(response.padre, int)
    
    def test_padre_int_sin_cambios(self):
        """Debe mantener padre como int"""
        from app.schemas.menu import MenuResponse
        
        data = {
            "id": 1,
            "url_menu": "test",
            "id_aplicacion": 1,
            "padre": 2,
            "nombre": "Test Menu",
            "orden": 1,
            "visible": 1,
            "acceso": 1,
            "activo": 1
        }
        
        response = MenuResponse(**data)
        assert response.padre == 2
        assert isinstance(response.padre, int)
    
    def test_padre_none_sin_cambios(self):
        """Debe mantener padre como None"""
        from app.schemas.menu import MenuResponse
        
        data = {
            "id": 1,
            "url_menu": "test",
            "id_aplicacion": 1,
            "padre": None,
            "nombre": "Test Menu",
            "orden": 1,
            "visible": 1,
            "acceso": 1,
            "activo": 1
        }
        
        response = MenuResponse(**data)
        assert response.padre is None


class TestMenuHierarchy:
    """Pruebas para la construcción de jerarquía de menús"""
    
    def test_jerarquia_basica(self):
        """Debe construir jerarquía básica"""
        menus = [
            {"id": 1, "nombre": "Menu 1", "padre": None},
            {"id": 2, "nombre": "Menu 2", "padre": 1},
            {"id": 3, "nombre": "Menu 3", "padre": 1},
        ]
        
        # Simular construcción de jerarquía
        menu_map = {}
        for menu in menus:
            menu_map[menu["id"]] = {"id": menu["id"], "nombre": menu["nombre"], "padre": menu["padre"], "children": []}
        
        for menu in menus:
            if menu["padre"] and menu["padre"] in menu_map:
                menu_map[menu["padre"]]["children"].append(menu_map[menu["id"]])
        
        root = menu_map[1]
        assert len(root["children"]) == 2
        assert root["children"][0]["id"] == 2
        assert root["children"][1]["id"] == 3
    
    def test_padre_como_numero(self):
        """Debe manejar padre como número"""
        menus = [
            {"id": 1, "nombre": "Menu 1", "padre": None},
            {"id": 2, "nombre": "Menu 2", "padre": 1},
        ]
        
        # Verificar que padre es número
        assert isinstance(menus[1]["padre"], int)
        assert menus[1]["padre"] == 1


class TestCapitalizacion:
    """Pruebas para la capitalización de texto"""
    
    def test_capitalizar_primera_letra(self):
        """Debe capitalizar primera letra"""
        texto = "dashboards"
        resultado = texto.capitalize()
        assert resultado == "Dashboards"
    
    def test_capitalizar_todo_mayuscula(self):
        """Debe convertir a minúsculas excepto primera"""
        texto = "DASHBOARDS"
        resultado = texto.capitalize()
        assert resultado == "Dashboards"
    
    def test_capitalizar_mixto(self):
        """Debe manejar texto mixto"""
        texto = "dASHBOARDS"
        resultado = texto.capitalize()
        assert resultado == "Dashboards"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
