#!/usr/bin/env python3
"""
Script de configuración inicial para MySQL
"""

import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.models import *  # Importar todos los modelos
from app.core.database import Base
from app.crud.crud_usuario import usuario as crud_usuario
from app.crud.crud_rol import rol as crud_rol
from app.crud.crud_aplicacion import aplicacion as crud_aplicacion
from app.schemas.usuario import UsuarioCreate
from app.schemas.rol import RolCreate
from app.schemas.aplicacion import AplicacionCreate

async def create_tables():
    """Crear todas las tablas en la base de datos MySQL"""
    print("🔧 Creando tablas en MySQL...")
    
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        # Crear todas las tablas
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Tablas creadas exitosamente en MySQL")

async def create_initial_data():
    """Crear datos iniciales del sistema"""
    print("📊 Creando datos iniciales en MySQL...")
    
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            # Crear aplicación principal
            print("  📱 Creando aplicación principal...")
            app_data = AplicacionCreate(
                key="AUTH_SYSTEM",
                nombre="Sistema de Autenticación",
                descripcion="Sistema principal de autenticación y autorización"
            )
            
            existing_app = await crud_aplicacion.get_by_key(db, key="AUTH_SYSTEM")
            if not existing_app:
                app = await crud_aplicacion.create(db, obj_in=app_data)
                print(f"     ✅ Aplicación creada: {app.nombre}")
            else:
                app = existing_app
                print(f"     ⚠️  Aplicación ya existe: {app.nombre}")
            
            # Crear roles básicos
            print("  👥 Creando roles básicos...")
            roles_data = [
                {
                    "nombre": "SUPER_ADMIN",
                    "descripcion": "Super Administrador del sistema",
                    "key_publico": "SUPER_ADMIN",
                    "id_aplicacion": app.id
                },
                {
                    "nombre": "ADMIN",
                    "descripcion": "Administrador del sistema",
                    "key_publico": "ADMIN",
                    "id_aplicacion": app.id
                },
                {
                    "nombre": "user",
                    "descripcion": "Usuario básico del sistema",
                    "key_publico": "USER",
                    "id_aplicacion": app.id
                }
            ]
            
            created_roles = {}
            for role_data in roles_data:
                existing_role = await crud_rol.get_by_nombre(db, nombre=role_data["nombre"])
                if not existing_role:
                    role = await crud_rol.create(db, obj_in=RolCreate(**role_data))
                    created_roles[role_data["nombre"]] = role
                    print(f"     ✅ Rol creado: {role.nombre}")
                else:
                    created_roles[role_data["nombre"]] = existing_role
                    print(f"     ⚠️  Rol ya existe: {existing_role.nombre}")
            
            # Crear usuario super administrador
            print("  👤 Creando usuario super administrador...")
            admin_data = UsuarioCreate(
                username="superadmin",
                email="superadmin@sistema.com",
                password="SuperAdmin123!",
                nombres="Super",
                apellidos="Administrador"
            )
            
            existing_admin = await crud_usuario.get_by_email(db, email="superadmin@sistema.com")
            if not existing_admin:
                admin_user = await crud_usuario.create(db, obj_in=admin_data)
                print(f"     ✅ Super admin creado: {admin_user.username}")
                
                # Asignar rol de super_admin
                from app.crud.crud_usuario_rol import usuario_rol as crud_usuario_rol
                from app.schemas.usuario_rol import UsuarioRolCreate
                
                user_role_data = UsuarioRolCreate(
                    id_usuario=admin_user.id,
                    id_rol=created_roles["SUPER_ADMIN"].id,
                    id_persona=admin_user.id
                )
                
                await crud_usuario_rol.create(db, obj_in=user_role_data)
                print(f"     ✅ Rol super_admin asignado al usuario")
                
            else:
                print(f"     ⚠️  Super admin ya existe: {existing_admin.username}")
            
            # Crear usuario administrador regular
            print("  👤 Creando usuario administrador...")
            admin_regular_data = UsuarioCreate(
                username="ADMIN",
                email="admin@sistema.com",
                password="Admin123!",
                nombres="Administrador",
                apellidos="Sistema"
            )
            
            existing_admin_regular = await crud_usuario.get_by_email(db, email="admin@sistema.com")
            if not existing_admin_regular:
                admin_regular_user = await crud_usuario.create(db, obj_in=admin_regular_data)
                print(f"     ✅ Admin creado: {admin_regular_user.username}")
                
                # Asignar rol de admin
                from app.crud.crud_usuario_rol import usuario_rol as crud_usuario_rol
                from app.schemas.usuario_rol import UsuarioRolCreate
                
                user_role_data = UsuarioRolCreate(
                    id_usuario=admin_regular_user.id,
                    id_rol=created_roles["ADMIN"].id,
                    id_persona=admin_regular_user.id
                )
                
                await crud_usuario_rol.create(db, obj_in=user_role_data)
                print(f"     ✅ Rol admin asignado al usuario")
                
            else:
                print(f"     ⚠️  Admin ya existe: {existing_admin_regular.username}")
            
            print("✅ Datos iniciales creados exitosamente en MySQL")
            
        except Exception as e:
            print(f"❌ Error creando datos iniciales: {e}")
            await db.rollback()
            raise
        finally:
            await engine.dispose()

async def verify_mysql_setup():
    """Verificar que la configuración MySQL sea correcta"""
    print("🔍 Verificando configuración MySQL...")
    
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with AsyncSessionLocal() as db:
            # Verificar conexión a base de datos
            result = await db.execute(text("SELECT 1"))
            print("  ✅ Conexión a MySQL exitosa")
            
            # Verificar usuarios
            users = await crud_usuario.get_all(db)
            print(f"  ✅ Usuarios en sistema: {len(users)}")
            
            # Verificar roles
            roles = await crud_rol.get_all(db)
            print(f"  ✅ Roles en sistema: {len(roles)}")
            
            # Verificar aplicaciones
            apps = await crud_aplicacion.get_all(db)
            print(f"  ✅ Aplicaciones en sistema: {len(apps)}")
            
            print("✅ Verificación MySQL completada exitosamente")
            
    except Exception as e:
        print(f"❌ Error en verificación MySQL: {e}")
        raise
    finally:
        await engine.dispose()

async def main():
    """Función principal de configuración para MySQL"""
    print("🚀 Configuración Inicial del Sistema de Autenticación - MySQL")
    print("=" * 70)
    
    try:
        # Paso 1: Crear tablas
        await create_tables()
        print()
        
        # Paso 2: Crear datos iniciales
        await create_initial_data()
        print()
        
        # Paso 3: Verificar configuración
        await verify_mysql_setup()
        print()
        
        print("🎉 ¡Configuración inicial MySQL completada exitosamente!")
        print()
        print("📋 Credenciales creadas:")
        print("   Super Admin:")
        print("     Email: superadmin@sistema.com")
        print("     Password: SuperAdmin123!")
        print()
        print("   Admin:")
        print("     Email: admin@sistema.com") 
        print("     Password: Admin123!")
        print()
        print("🔧 Configuración MySQL:")
        print(f"   URL: {settings.database_url}")
        print()
        print("🌐 Para iniciar el servidor:")
        print("   uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print()
        print("📚 Documentación disponible en:")
        print("   http://localhost:8000/docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración inicial MySQL: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

