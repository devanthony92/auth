#!/usr/bin/env python3
"""
Script de pruebas básicas para el sistema de autenticación
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "username": "test_user",
    "email": "test@ejemplo.com",
    "password": "test123456",
    "nombres": "Usuario",
    "apellidos": "Prueba"
}

class AuthSystemTester:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.admin_token = None
        self.test_user_id = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_health_check(self):
        """Probar endpoint de salud"""
        print("🔍 Probando health check...")
        try:
            response = await self.client.get(f"{BASE_URL}/../health")
            assert response.status_code == 200
            print("✅ Health check exitoso")
            return True
        except Exception as e:
            print(f"❌ Error en health check: {e}")
            return False
    
    async def test_create_admin_user(self):
        """Crear usuario administrador para pruebas"""
        print("🔍 Creando usuario administrador...")
        try:
            admin_user = {
                "username": "admin_test",
                "email": "admin@ejemplo.com", 
                "password": "admin123456",
                "nombres": "Admin",
                "apellidos": "Test"
            }
            
            # Intentar crear usuario admin (puede fallar si ya existe)
            response = await self.client.post(f"{BASE_URL}/usuarios", json=admin_user)
            
            if response.status_code in [200, 400]:  # 400 si ya existe
                print("✅ Usuario administrador disponible")
                return True
            else:
                print(f"❌ Error creando admin: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error en creación de admin: {e}")
            return False
    
    async def test_login(self):
        """Probar login básico"""
        print("🔍 Probando login...")
        try:
            login_data = {
                "email": "admin@ejemplo.com",
                "password": "admin123456"
            }
            
            response = await self.client.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                print("✅ Login exitoso")
                print(f"   Token obtenido: {self.admin_token[:50]}...")
                return True
            else:
                print(f"❌ Error en login: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en login: {e}")
            return False
    
    async def test_get_current_user(self):
        """Probar obtener usuario actual"""
        print("🔍 Probando obtener usuario actual...")
        try:
            if not self.admin_token:
                print("❌ No hay token disponible")
                return False
                
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = await self.client.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                print("✅ Usuario actual obtenido")
                print(f"   Usuario: {user_data.get('username')} ({user_data.get('email')})")
                return True
            else:
                print(f"❌ Error obteniendo usuario: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error obteniendo usuario: {e}")
            return False
    
    async def test_create_user(self):
        """Probar creación de usuario"""
        print("🔍 Probando creación de usuario...")
        try:
            if not self.admin_token:
                print("❌ No hay token de admin disponible")
                return False
                
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = await self.client.post(
                f"{BASE_URL}/usuarios", 
                json=TEST_USER, 
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data["id"]
                print("✅ Usuario creado exitosamente")
                print(f"   ID: {self.test_user_id}")
                return True
            elif response.status_code == 400:
                print("⚠️  Usuario ya existe (esperado en pruebas repetidas)")
                return True
            else:
                print(f"❌ Error creando usuario: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            return False
    
    async def test_list_users(self):
        """Probar listado de usuarios"""
        print("🔍 Probando listado de usuarios...")
        try:
            if not self.admin_token:
                print("❌ No hay token de admin disponible")
                return False
                
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = await self.client.get(
                f"{BASE_URL}/usuarios?skip=0&limit=10", 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Listado de usuarios exitoso")
                print(f"   Total: {data.get('total', 0)} usuarios")
                print(f"   En página: {len(data.get('items', []))} usuarios")
                return True
            else:
                print(f"❌ Error listando usuarios: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error listando usuarios: {e}")
            return False
    
    async def test_create_role(self):
        """Probar creación de rol"""
        print("🔍 Probando creación de rol...")
        try:
            if not self.admin_token:
                print("❌ No hay token de admin disponible")
                return False
                
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            role_data = {
                "nombre": "test_role",
                "descripcion": "Rol de prueba",
                "key_publico": "TEST_ROLE",
                "id_aplicacion": 1
            }
            
            response = await self.client.post(
                f"{BASE_URL}/roles", 
                json=role_data, 
                headers=headers
            )
            
            if response.status_code == 200:
                role_data = response.json()
                print("✅ Rol creado exitosamente")
                print(f"   ID: {role_data['id']}, Nombre: {role_data['nombre']}")
                return True
            elif response.status_code == 400:
                print("⚠️  Rol ya existe (esperado en pruebas repetidas)")
                return True
            else:
                print(f"❌ Error creando rol: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error creando rol: {e}")
            return False
    
    async def test_microsoft_auth_url(self):
        """Probar obtención de URL de Microsoft"""
        print("🔍 Probando URL de autenticación Microsoft...")
        try:
            response = await self.client.get(f"{BASE_URL}/auth/microsoft/login")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ URL de Microsoft obtenida")
                print(f"   URL: {data.get('authorization_url', '')[:100]}...")
                return True
            else:
                print(f"❌ Error obteniendo URL Microsoft: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error obteniendo URL Microsoft: {e}")
            return False
    
    async def test_api_documentation(self):
        """Probar acceso a documentación"""
        print("🔍 Probando documentación de API...")
        try:
            response = await self.client.get("http://localhost:8000/docs")
            
            if response.status_code == 200:
                print("✅ Documentación accesible")
                return True
            else:
                print(f"❌ Error accediendo a docs: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error accediendo a docs: {e}")
            return False
    
    async def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 Iniciando pruebas del sistema de autenticación\n")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Documentación API", self.test_api_documentation),
            ("Crear Admin", self.test_create_admin_user),
            ("Login", self.test_login),
            ("Usuario Actual", self.test_get_current_user),
            ("Crear Usuario", self.test_create_user),
            ("Listar Usuarios", self.test_list_users),
            ("Crear Rol", self.test_create_role),
            ("URL Microsoft", self.test_microsoft_auth_url),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ Error inesperado en {test_name}: {e}")
            
            await asyncio.sleep(0.5)  # Pausa entre pruebas
        
        print(f"\n{'='*50}")
        print(f"📊 RESUMEN DE PRUEBAS")
        print(f"{'='*50}")
        print(f"✅ Exitosas: {passed}/{total}")
        print(f"❌ Fallidas: {total - passed}/{total}")
        print(f"📈 Porcentaje: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        else:
            print(f"\n⚠️  {total - passed} pruebas fallaron. Revisar configuración.")
        
        return passed == total

async def main():
    """Función principal"""
    print("Sistema de Pruebas - Autenticación FastAPI")
    print("=" * 50)
    
    async with AuthSystemTester() as tester:
        success = await tester.run_all_tests()
        
    if success:
        print("\n✅ Sistema funcionando correctamente")
        return 0
    else:
        print("\n❌ Sistema con problemas")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

