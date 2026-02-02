# Sistema de Autenticación FastAPI - Documentación Completa

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Instalación y Configuración](#instalación-y-configuración)
4. [Autenticación y Autorización](#autenticación-y-autorización)
5. [APIs Disponibles](#apis-disponibles)
6. [Modelos de Datos](#modelos-de-datos)
7. [Ejemplos de Uso](#ejemplos-de-uso)
8. [Guía de Desarrollo](#guía-de-desarrollo)
9. [Seguridad](#seguridad)
10. [Troubleshooting](#troubleshooting)

## Introducción

Este sistema de autenticación desarrollado con FastAPI Async proporciona una solución completa y robusta para la gestión de usuarios, roles, menús y permisos en aplicaciones web modernas. El sistema está diseñado con una arquitectura escalable que soporta autenticación tradicional con email/contraseña, así como integración con Microsoft OAuth2 para usuarios corporativos.

### Características Principales

El sistema incluye las siguientes funcionalidades clave:

- **Autenticación JWT**: Sistema de tokens seguros con datos completos del usuario
- **Integración Microsoft OAuth2**: Soporte para autenticación con cuentas de Outlook/Microsoft
- **Gestión de Roles y Permisos**: Sistema granular de control de acceso
- **CRUD Completo**: Operaciones asíncronas para todas las entidades
- **Soft Delete**: Eliminación lógica con posibilidad de reactivación
- **Paginación y Filtros**: APIs optimizadas para grandes volúmenes de datos
- **Auditoría**: Sistema de bitácoras para seguimiento de cambios
- **Documentación Automática**: Swagger/OpenAPI integrado

### Tecnologías Utilizadas

- **FastAPI**: Framework web moderno y de alto rendimiento
- **SQLAlchemy**: ORM asíncrono para manejo de base de datos
- **PostgreSQL**: Base de datos relacional principal
- **JWT**: Tokens de autenticación seguros
- **Pydantic**: Validación y serialización de datos
- **HTTPX**: Cliente HTTP asíncrono para integraciones
- **Passlib**: Hashing seguro de contraseñas
- **Python-JOSE**: Manejo de tokens JWT

## Arquitectura del Sistema

### Estructura de Directorios

```
auth_system/
├── app/
│   ├── models/          # Modelos SQLAlchemy
│   │   ├── usuario.py
│   │   ├── rol.py
│   │   ├── aplicacion.py
│   │   ├── menu.py
│   │   ├── api.py
│   │   ├── permiso.py
│   │   ├── usuario_rol.py
│   │   ├── cuenta_social.py
│   │   ├── bitacora.py
│   │   ├── aplicacion_cliente.py
│   │   └── recording.py
│   ├── schemas/         # Esquemas Pydantic
│   │   ├── usuario.py
│   │   ├── rol.py
│   │   ├── aplicacion.py
│   │   ├── menu.py
│   │   ├── api.py
│   │   ├── permiso.py
│   │   ├── usuario_rol.py
│   │   └── cuenta_social.py
│   ├── crud/           # Operaciones CRUD
│   │   ├── base.py
│   │   ├── crud_usuario.py
│   │   ├── crud_rol.py
│   │   ├── crud_aplicacion.py
│   │   ├── crud_menu.py
│   │   ├── crud_api.py
│   │   ├── crud_permiso.py
│   │   ├── crud_usuario_rol.py
│   │   └── crud_cuenta_social.py
│   ├── api/            # Endpoints de la API
│   │   └── endpoints/
│   │       ├── auth.py
│   │       ├── usuarios.py
│   │       ├── microsoft_auth.py
│   │       ├── roles.py
│   │       ├── menus.py
│   │       ├── apis.py
│   │       └── permisos.py
│   ├── core/           # Configuración central
│   │   ├── config.py
│   │   └── database.py
│   ├── auth/           # Lógica de autenticación
│   │   ├── jwt_handler.py
│   │   ├── dependencies.py
│   │   ├── user_data.py
│   │   └── microsoft_oauth.py
│   └── utils/          # Utilidades
├── tests/              # Pruebas
├── docs/               # Documentación
├── requirements.txt    # Dependencias
├── .env.example       # Ejemplo de variables de entorno
└── main.py            # Aplicación principal
```

### Patrones de Diseño

El sistema implementa varios patrones de diseño para garantizar mantenibilidad y escalabilidad:

**Repository Pattern**: Cada entidad tiene su propio CRUD que hereda de una clase base común, proporcionando operaciones estándar y especializadas.

**Dependency Injection**: FastAPI maneja automáticamente las dependencias, incluyendo sesiones de base de datos y autenticación.

**Factory Pattern**: Los tokens JWT se crean mediante funciones especializadas que encapsulan la lógica de generación.

**Decorator Pattern**: Los decoradores de roles y permisos proporcionan control de acceso granular.

## Instalación y Configuración

### Requisitos del Sistema

- Python 3.11 o superior
- PostgreSQL 12 o superior
- Redis (opcional, para almacenamiento de sesiones OAuth)

### Instalación

1. **Clonar el repositorio y navegar al directorio:**

```bash
cd auth_system
```

2. **Crear entorno virtual:**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias:**

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**

```bash
cp .env.example .env
```

Editar el archivo `.env` con los valores apropiados:

```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://usuario:password@localhost:5432/auth_db

# JWT
SECRET_KEY=tu_clave_secreta_super_segura_aqui_cambiar_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Microsoft OAuth2
MICROSOFT_CLIENT_ID=tu_client_id_de_microsoft
MICROSOFT_CLIENT_SECRET=tu_client_secret_de_microsoft
MICROSOFT_TENANT_ID=tu_tenant_id_de_microsoft
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/auth/microsoft/callback

# Configuración de la aplicación
APP_NAME=Sistema de Autenticación
APP_VERSION=1.0.0
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

5. **Crear la base de datos:**

```bash
# Ejecutar el script SQL proporcionado en PostgreSQL
psql -U usuario -d auth_db -f auth_db.sql
```

6. **Ejecutar la aplicación:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Configuración de Microsoft OAuth2

Para habilitar la autenticación con Microsoft, es necesario registrar la aplicación en Azure Active Directory:

1. **Acceder al Portal de Azure** (https://portal.azure.com)
2. **Navegar a Azure Active Directory > App registrations**
3. **Crear nueva aplicación** con los siguientes parámetros:
   - Nombre: Sistema de Autenticación
   - Tipos de cuenta soportados: Cuentas en cualquier directorio organizacional
   - URI de redirección: `http://localhost:8000/api/v1/auth/microsoft/callback`

4. **Configurar permisos de API:**
   - Microsoft Graph: User.Read (Delegated)
   - Microsoft Graph: openid (Delegated)
   - Microsoft Graph: profile (Delegated)
   - Microsoft Graph: email (Delegated)

5. **Generar secreto de cliente** y actualizar las variables de entorno correspondientes.

## Autenticación y Autorización

### Sistema de Autenticación JWT

El sistema utiliza JSON Web Tokens (JWT) para manejar la autenticación de usuarios. Los tokens incluyen información completa del usuario, incluyendo roles, menús permitidos, APIs accesibles y aplicaciones autorizadas.

#### Estructura del Token

```json
{
	"sub": "123",
	"email": "usuario@ejemplo.com",
	"username": "usuario123",
	"user_id": 123,
	"roles": [
		{
			"id": 1,
			"nombre": "admin",
			"descripcion": "Administrador del sistema",
			"key_publico": "ADMIN",
			"id_aplicacion": 1
		}
	],
	"menus": [
		{
			"id": 1,
			"nombre": "Dashboard",
			"url_menu": "/dashboard",
			"ruta_front": "/dashboard",
			"orden": 1,
			"visible": 1,
			"icono": "dashboard",
			"id_aplicacion": 1
		}
	],
	"apis": [
		{
			"id": 1,
			"nombre": "Listar Usuarios",
			"url_api": "/api/v1/usuarios",
			"grupo": "usuarios",
			"tipo_accion": 1,
			"id_aplicacion": 1
		}
	],
	"aplicaciones": [
		{
			"id": 1,
			"key": "AUTH_SYSTEM",
			"nombre": "Sistema de Autenticación",
			"descripcion": "Sistema principal de autenticación"
		}
	],
	"token_type": "access",
	"exp": 1640995200
}
```

#### Flujo de Autenticación

1. **Login**: El usuario envía credenciales (email/password) al endpoint `/api/v1/auth/login`
2. **Validación**: El sistema verifica las credenciales contra la base de datos
3. **Generación de Token**: Se crea un JWT con todos los datos del usuario
4. **Respuesta**: Se retorna el token junto con los datos del usuario
5. **Uso**: El cliente incluye el token en el header `Authorization: Bearer <token>`
6. **Validación**: Cada request protegido valida el token automáticamente

### Control de Acceso Basado en Roles (RBAC)

El sistema implementa un modelo de control de acceso granular que permite:

**Roles**: Agrupaciones lógicas de permisos asignables a usuarios
**Permisos de Menú**: Control de acceso a secciones de la interfaz
**Permisos de API**: Control de acceso a endpoints específicos
**Aplicaciones**: Segmentación por aplicación o módulo

#### Decoradores de Seguridad

```python
# Requerir roles específicos
@require_roles(["ADMIN", "SUPER_ADMIN"])
async def endpoint_admin():
    pass

# Requerir permisos de API específicos
@require_permissions(["/api/v1/usuarios"])
async def endpoint_usuarios():
    pass
```

### Autenticación con Microsoft

El sistema soporta autenticación OAuth2 con Microsoft, permitiendo que usuarios corporativos accedan usando sus cuentas de Outlook/Microsoft 365.

#### Flujo OAuth2

1. **Inicio**: Cliente solicita URL de autorización via `/api/v1/auth/microsoft/login`
2. **Redirección**: Usuario es redirigido a Microsoft para autenticación
3. **Autorización**: Usuario autoriza la aplicación en Microsoft
4. **Callback**: Microsoft redirige con código de autorización
5. **Intercambio**: Sistema intercambia código por token de acceso
6. **Datos de Usuario**: Se obtienen datos del usuario desde Microsoft Graph
7. **Creación/Vinculación**: Se crea nuevo usuario o vincula cuenta existente
8. **Token JWT**: Se genera token JWT con permisos del usuario

## APIs Disponibles

### Autenticación

#### POST /api/v1/auth/login

Autenticar usuario con email y contraseña.

**Request Body:**

```json
{
	"email": "usuario@ejemplo.com",
	"password": "contraseña123"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "usuario123",
    "email": "usuario@ejemplo.com",
    "nombres": "Juan",
    "apellidos": "Pérez",
    "nombre_completo": "Juan Pérez",
    "activo": true
  },
  "roles": [...],
  "menus": [...],
  "apis": [...],
  "aplicaciones": [...]
}
```

#### GET /api/v1/auth/me

Obtener datos básicos del usuario autenticado.

**Headers:**

```
Authorization: Bearer <token>
```

**Response:**

```json
{
	"id": 1,
	"username": "usuario123",
	"email": "usuario@ejemplo.com",
	"nombres": "Juan",
	"apellidos": "Pérez",
	"nombre_completo": "Juan Pérez",
	"activo": true,
	"created_at": "2023-01-01T00:00:00Z"
}
```

#### GET /api/v1/auth/me/complete

Obtener datos completos del usuario con roles, menús y permisos.

**Response:**

```json
{
  "user": {...},
  "roles": [...],
  "menus": [...],
  "apis": [...],
  "aplicaciones": [...]
}
```

### Autenticación Microsoft

#### GET /api/v1/auth/microsoft/login

Iniciar proceso de autenticación con Microsoft.

**Query Parameters:**

- `redirect_url` (opcional): URL de redirección después del login

**Response:**

```json
{
	"authorization_url": "https://login.microsoftonline.com/...",
	"state": "estado_unico_csrf"
}
```

#### GET /api/v1/auth/microsoft/callback

Callback de Microsoft OAuth2 (manejado automáticamente).

### Usuarios

#### GET /api/v1/usuarios

Listar usuarios con paginación y filtros.

**Query Parameters:**

- `skip`: Número de registros a omitir (default: 0)
- `limit`: Número máximo de registros (default: 100)
- `search`: Término de búsqueda
- `activo`: Filtrar por estado activo (true/false)

**Response:**

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 100,
  "pages": 2
}
```

#### POST /api/v1/usuarios

Crear nuevo usuario.

**Request Body:**

```json
{
	"username": "nuevo_usuario",
	"email": "nuevo@ejemplo.com",
	"password": "contraseña123",
	"nombres": "Nuevo",
	"apellidos": "Usuario",
	"activo": true
}
```

#### PUT /api/v1/usuarios/{usuario_id}

Actualizar usuario existente.

#### DELETE /api/v1/usuarios/{usuario_id}

Eliminar usuario (soft delete).

#### POST /api/v1/usuarios/{usuario_id}/reactivate

Reactivar usuario eliminado.

### Roles

#### GET /api/v1/roles

Listar roles con paginación y filtros.

#### GET /api/v1/roles/{rol_id}/menus

Obtener menús permitidos para un rol específico.

#### GET /api/v1/roles/{rol_id}/apis

Obtener APIs permitidas para un rol específico.

#### GET /api/v1/roles/{rol_id}/aplicaciones

Obtener aplicaciones permitidas para un rol específico.

#### POST /api/v1/roles

Crear nuevo rol.

#### PUT /api/v1/roles/{rol_id}

Actualizar rol existente.

#### DELETE /api/v1/roles/{rol_id}

Eliminar rol (soft delete).

### Menús

#### GET /api/v1/menus

Listar menús con paginación y filtros.

#### GET /api/v1/menus/hierarchy

Obtener jerarquía completa de menús.

**Query Parameters:**

- `aplicacion_id` (opcional): Filtrar por aplicación

**Response:**

```json
[
	{
		"id": 1,
		"nombre": "Dashboard",
		"url_menu": "/dashboard",
		"padre": null,
		"orden": 1,
		"children": [
			{
				"id": 2,
				"nombre": "Estadísticas",
				"url_menu": "/dashboard/stats",
				"padre": "/dashboard",
				"orden": 1,
				"children": []
			}
		]
	}
]
```

#### GET /api/v1/menus/visible

Obtener solo menús visibles.

#### POST /api/v1/menus

Crear nuevo menú.

#### PUT /api/v1/menus/{menu_id}

Actualizar menú existente.

#### DELETE /api/v1/menus/{menu_id}

Eliminar menú (soft delete).

### APIs

#### GET /api/v1/apis

Listar APIs con paginación y filtros.

#### GET /api/v1/apis/by-grupo/{grupo}

Obtener APIs por grupo.

#### GET /api/v1/apis/by-tipo-accion/{tipo_accion}

Obtener APIs por tipo de acción.

#### POST /api/v1/apis

Crear nueva API.

#### PUT /api/v1/apis/{api_id}

Actualizar API existente.

#### DELETE /api/v1/apis/{api_id}

Eliminar API (soft delete).

### Permisos

#### GET /api/v1/permisos/menu/rol/{rol_id}

Obtener menús permitidos para un rol.

#### GET /api/v1/permisos/api/rol/{rol_id}

Obtener APIs permitidas para un rol.

#### POST /api/v1/permisos/menu/

Crear permiso de menú.

**Request Body:**

```json
{
	"rol": 1,
	"menu": 5,
	"id_persona": 1
}
```

#### POST /api/v1/permisos/api/

Crear permiso de API.

#### DELETE /api/v1/permisos/menu/{rol_id}/{menu_id}

Eliminar permiso de menú específico.

#### DELETE /api/v1/permisos/api/{rol_id}/{api_id}

Eliminar permiso de API específico.

## Modelos de Datos

### Usuario

Entidad principal que representa a los usuarios del sistema.

**Campos:**

- `id`: Identificador único (Integer, PK)
- `username`: Nombre de usuario único (String, 50)
- `email`: Correo electrónico único (String, 100)
- `hash_clave`: Hash de la contraseña (String, 255)
- `nombres`: Nombres del usuario (String, 250)
- `apellidos`: Apellidos del usuario (String, 250)
- `firma`: Firma digital (String, 250)
- `foto`: URL de la foto de perfil (String, 250)
- `activo`: Estado activo/inactivo (Boolean)
- `created_at`: Fecha de creación (DateTime)
- `updated_at`: Fecha de última actualización (DateTime)
- `deleted_at`: Fecha de eliminación lógica (DateTime)

**Relaciones:**

- `usuario_roles`: Roles asignados al usuario
- `cuentas_sociales`: Cuentas sociales vinculadas
- `bitacoras`: Registros de auditoría del usuario

### Rol

Define los roles disponibles en el sistema.

**Campos:**

- `id`: Identificador único (Integer, PK)
- `nombre`: Nombre del rol único (String, 50)
- `id_aplicacion`: ID de la aplicación (Integer)
- `descripcion`: Descripción del rol (String, 255)
- `key_publico`: Clave pública única (String, 50)
- `id_persona`: ID de la persona que creó (Integer)
- `activo`: Estado activo/inactivo (Integer)
- `created_at`: Fecha de creación (DateTime)
- `updated_at`: Fecha de última actualización (DateTime)
- `deleted_at`: Fecha de eliminación lógica (DateTime)

**Relaciones:**

- `usuario_roles`: Usuarios con este rol
- `permiso_menus`: Permisos de menú del rol
- `permiso_apis`: Permisos de API del rol

### Menu

Define la estructura de menús del sistema.

**Campos:**

- `id`: Identificador único (BigInteger, PK)
- `url_menu`: URL única del menú (String, 250)
- `id_aplicacion`: ID de la aplicación (Integer, FK)
- `padre`: Menú padre para jerarquía (String, 100)
- `nombre`: Nombre del menú (String, 250)
- `ruta_front`: Ruta en el frontend (String, 250)
- `orden`: Orden de visualización (Integer)
- `visible`: Visibilidad del menú (Integer)
- `acceso`: Nivel de acceso (Integer)
- `icono`: Icono del menú (String, 300)
- `target`: Target del enlace (String, 49)
- `activo`: Estado activo/inactivo (Integer)
- `descripcion`: Descripción del menú (String, 255)
- `created_at`: Fecha de creación (DateTime)
- `updated_at`: Fecha de última actualización (DateTime)
- `deleted_at`: Fecha de eliminación lógica (DateTime)
- `id_persona`: ID de la persona que creó (Integer)

**Relaciones:**

- `aplicacion`: Aplicación a la que pertenece
- `permiso_menus`: Permisos asociados al menú

### Api

Define los endpoints de API disponibles.

**Campos:**

- `id`: Identificador único (BigInteger, PK)
- `grupo`: Grupo de la API (String, 50)
- `url_api`: URL de la API (String, 460)
- `id_aplicacion`: ID de la aplicación (Integer, FK)
- `class_front`: Clase del frontend (String, 460)
- `tipo_accion`: Tipo de acción (Integer)
- `nombre`: Nombre de la API (String, 145)
- `descripcion`: Descripción de la API (String, 255)
- `id_persona`: ID de la persona que creó (Integer)
- `activo`: Estado activo/inactivo (Integer)
- `created_at`: Fecha de creación (DateTime)
- `updated_at`: Fecha de última actualización (DateTime)
- `deleted_at`: Fecha de eliminación lógica (DateTime)

**Relaciones:**

- `aplicacion`: Aplicación a la que pertenece
- `permiso_apis`: Permisos asociados a la API

### CuentaSocial

Almacena las cuentas sociales vinculadas a usuarios.

**Campos:**

- `id`: Identificador único (Integer, PK)
- `id_usuario`: ID del usuario (Integer, FK)
- `proveedor`: Proveedor de la cuenta social (String, 20)
- `id_usuario_proveedor`: ID del usuario en el proveedor (String, 255)
- `token_proveedor`: Token del proveedor (Text)
- `correo`: Correo en el proveedor (String, 100)
- `nombre`: Nombre en el proveedor (String, 100)
- `created_at`: Fecha de creación (DateTime)
- `updated_at`: Fecha de última actualización (DateTime)
- `deleted_at`: Fecha de eliminación lógica (DateTime)

**Relaciones:**

- `usuario`: Usuario al que pertenece la cuenta

## Ejemplos de Uso

### Autenticación Básica

```python
import httpx
import asyncio

async def login_example():
    async with httpx.AsyncClient() as client:
        # Login
        login_data = {
            "email": "admin@ejemplo.com",
            "password": "admin123"
        }

        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data
        )

        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            print(f"Token obtenido: {token}")

            # Usar token para acceder a endpoint protegido
            headers = {"Authorization": f"Bearer {token}"}

            user_response = await client.get(
                "http://localhost:8000/api/v1/auth/me",
                headers=headers
            )

            if user_response.status_code == 200:
                user_data = user_response.json()
                print(f"Usuario: {user_data['nombre_completo']}")
            else:
                print("Error al obtener datos del usuario")
        else:
            print("Error en login")

# Ejecutar ejemplo
asyncio.run(login_example())
```

### Gestión de Usuarios

```python
async def user_management_example():
    async with httpx.AsyncClient() as client:
        # Obtener token de admin
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Crear nuevo usuario
        new_user = {
            "username": "nuevo_usuario",
            "email": "nuevo@ejemplo.com",
            "password": "password123",
            "nombres": "Nuevo",
            "apellidos": "Usuario"
        }

        response = await client.post(
            "http://localhost:8000/api/v1/usuarios",
            json=new_user,
            headers=headers
        )

        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data["id"]
            print(f"Usuario creado con ID: {user_id}")

            # Listar usuarios con paginación
            list_response = await client.get(
                "http://localhost:8000/api/v1/usuarios?skip=0&limit=10",
                headers=headers
            )

            if list_response.status_code == 200:
                users_data = list_response.json()
                print(f"Total de usuarios: {users_data['total']}")
                print(f"Usuarios en página: {len(users_data['items'])}")
```

### Gestión de Roles y Permisos

```python
async def role_permission_example():
    async with httpx.AsyncClient() as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Crear nuevo rol
        new_role = {
            "nombre": "editor",
            "descripcion": "Editor de contenido",
            "key_publico": "EDITOR",
            "id_aplicacion": 1
        }

        role_response = await client.post(
            "http://localhost:8000/api/v1/roles",
            json=new_role,
            headers=headers
        )

        if role_response.status_code == 200:
            role_data = role_response.json()
            role_id = role_data["id"]

            # Asignar permiso de menú al rol
            menu_permission = {
                "rol": role_id,
                "menu": 1,  # ID del menú
                "id_persona": 1
            }

            await client.post(
                "http://localhost:8000/api/v1/permisos/menu/",
                json=menu_permission,
                headers=headers
            )

            # Obtener menús del rol
            menus_response = await client.get(
                f"http://localhost:8000/api/v1/roles/{role_id}/menus",
                headers=headers
            )

            if menus_response.status_code == 200:
                menus = menus_response.json()
                print(f"Menús permitidos para el rol: {len(menus)}")
```

### Autenticación con Microsoft

```javascript
// Frontend JavaScript
async function loginWithMicrosoft() {
	try {
		// Obtener URL de autorización
		const response = await fetch(
			"/api/v1/auth/microsoft/login?redirect_url=http://localhost:3000/dashboard",
		);
		const data = await response.json();

		// Redirigir a Microsoft
		window.location.href = data.authorization_url;
	} catch (error) {
		console.error("Error al iniciar login con Microsoft:", error);
	}
}

// Manejar callback en la página de destino
function handleMicrosoftCallback() {
	const urlParams = new URLSearchParams(window.location.search);
	const token = urlParams.get("token");
	const type = urlParams.get("type");

	if (token && type === "microsoft") {
		// Guardar token en localStorage
		localStorage.setItem("auth_token", token);

		// Obtener datos del usuario
		fetch("/api/v1/auth/me", {
			headers: {
				Authorization: `Bearer ${token}`,
			},
		})
			.then((response) => response.json())
			.then((userData) => {
				console.log("Usuario autenticado:", userData);
				// Redirigir al dashboard
				window.location.href = "/dashboard";
			});
	}
}
```

### Búsqueda y Filtros

```python
async def search_filter_example():
    async with httpx.AsyncClient() as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Búsqueda de usuarios
        search_params = {
            "search": "juan",
            "skip": 0,
            "limit": 20,
            "activo": True
        }

        response = await client.get(
            "http://localhost:8000/api/v1/usuarios",
            params=search_params,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print(f"Usuarios encontrados: {data['total']}")

            for user in data['items']:
                print(f"- {user['nombre_completo']} ({user['email']})")

        # Filtrar menús por aplicación
        menu_response = await client.get(
            "http://localhost:8000/api/v1/menus/by-aplicacion/1",
            headers=headers
        )

        if menu_response.status_code == 200:
            menus = menu_response.json()
            print(f"Menús de la aplicación 1: {len(menus)}")
```

## Guía de Desarrollo

### Agregar Nuevos Endpoints

Para agregar nuevos endpoints al sistema, sigue estos pasos:

1. **Crear el modelo SQLAlchemy** (si es necesario):

```python
# app/models/nueva_entidad.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class NuevaEntidad(Base):
    __tablename__ = "nueva_entidad"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

2. **Crear esquemas Pydantic**:

```python
# app/schemas/nueva_entidad.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NuevaEntidadBase(BaseModel):
    nombre: str

class NuevaEntidadCreate(NuevaEntidadBase):
    pass

class NuevaEntidadUpdate(BaseModel):
    nombre: Optional[str] = None

class NuevaEntidadResponse(NuevaEntidadBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

3. **Crear CRUD**:

```python
# app/crud/crud_nueva_entidad.py
from app.crud.base import CRUDBase
from app.models.nueva_entidad import NuevaEntidad
from app.schemas.nueva_entidad import NuevaEntidadCreate, NuevaEntidadUpdate

class CRUDNuevaEntidad(CRUDBase[NuevaEntidad, NuevaEntidadCreate, NuevaEntidadUpdate]):
    pass

nueva_entidad = CRUDNuevaEntidad(NuevaEntidad)
```

4. **Crear endpoints**:

```python
# app/api/endpoints/nueva_entidad.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud.crud_nueva_entidad import nueva_entidad
from app.schemas.nueva_entidad import NuevaEntidadCreate, NuevaEntidadResponse
from app.auth.dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=NuevaEntidadResponse)
async def create_nueva_entidad(
    entidad_in: NuevaEntidadCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    return await nueva_entidad.create(db, obj_in=entidad_in)
```

5. **Registrar en el router principal**:

```python
# app/api/__init__.py
from app.api.endpoints import nueva_entidad

api_router.include_router(
    nueva_entidad.router,
    prefix="/nueva-entidad",
    tags=["Nueva Entidad"]
)
```

### Personalizar Autenticación

Para agregar nuevos proveedores de autenticación OAuth2:

1. **Crear cliente OAuth**:

```python
# app/auth/nuevo_proveedor_oauth.py
class NuevoProveedorOAuth:
    def __init__(self):
        self.client_id = settings.nuevo_proveedor_client_id
        self.client_secret = settings.nuevo_proveedor_client_secret

    def get_authorization_url(self, state: str) -> str:
        # Implementar lógica específica del proveedor
        pass

    async def exchange_code_for_token(self, code: str) -> dict:
        # Implementar intercambio de código por token
        pass

    async def get_user_info(self, access_token: str) -> dict:
        # Implementar obtención de datos del usuario
        pass
```

2. **Crear endpoints de autenticación**:

```python
# app/api/endpoints/nuevo_proveedor_auth.py
@router.get("/nuevo-proveedor/login")
async def nuevo_proveedor_login():
    # Implementar inicio de autenticación
    pass

@router.get("/nuevo-proveedor/callback")
async def nuevo_proveedor_callback():
    # Implementar callback
    pass
```

### Agregar Validaciones Personalizadas

```python
# app/schemas/usuario.py
from pydantic import BaseModel, validator
import re

class UsuarioCreate(BaseModel):
    username: str
    email: str
    password: str

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('El username debe tener al menos 3 caracteres')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('El username solo puede contener letras, números y guiones bajos')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v
```

### Middleware Personalizado

```python
# app/middleware/custom_middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logging.info(f"Request: {request.method} {request.url}")

        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logging.info(f"Response: {response.status_code} - {process_time:.4f}s")

        return response

# Agregar al main.py
app.add_middleware(LoggingMiddleware)
```

## Seguridad

### Mejores Prácticas Implementadas

El sistema implementa múltiples capas de seguridad para proteger contra amenazas comunes:

**Autenticación Segura**: Las contraseñas se almacenan usando bcrypt con salt automático, proporcionando protección contra ataques de diccionario y rainbow tables.

**Tokens JWT Seguros**: Los tokens incluyen tiempo de expiración y están firmados con una clave secreta robusta. Se recomienda rotar la clave periódicamente en producción.

**Validación de Entrada**: Todos los datos de entrada se validan usando Pydantic, previniendo inyecciones y datos malformados.

**Control de Acceso Granular**: El sistema RBAC permite control fino sobre qué usuarios pueden acceder a qué recursos.

**CORS Configurado**: Las políticas CORS están configuradas para permitir solo orígenes autorizados.

**Protección CSRF**: Los flujos OAuth incluyen tokens de estado únicos para prevenir ataques CSRF.

### Configuración de Seguridad

#### Variables de Entorno Críticas

```env
# Clave secreta para JWT - DEBE ser única y compleja en producción
SECRET_KEY=clave_super_secreta_de_al_menos_32_caracteres_aleatorios

# Configurar orígenes CORS permitidos
CORS_ORIGINS=["https://miapp.com", "https://admin.miapp.com"]

# Configurar tiempo de expiración de tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configurar base de datos con SSL en producción
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?sslmode=require
```

#### Configuración de Producción

Para despliegue en producción, considera las siguientes configuraciones adicionales:

```python
# app/core/config.py
class ProductionSettings(Settings):
    debug: bool = False

    # Configuración de seguridad adicional
    secure_cookies: bool = True
    https_only: bool = True

    # Configuración de rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hora

    # Configuración de logging
    log_level: str = "WARNING"
    log_file: str = "/var/log/auth_system.log"
```

### Auditoría y Monitoreo

El sistema incluye capacidades de auditoría a través de la tabla `bitacoras`:

```python
# Ejemplo de registro de auditoría
async def log_user_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    details: dict,
    menu: str = None,
    api_url: str = None
):
    from app.models.bitacora import Bitacora

    bitacora = Bitacora(
        id_tipo_bitacora=1,  # Tipo de acción
        datos_insertados=json.dumps(details),
        observacion=action,
        menu=menu,
        url_api=api_url,
        id_persona=user_id
    )

    db.add(bitacora)
    await db.commit()
```

### Recomendaciones de Seguridad

1. **Rotación de Claves**: Implementar rotación automática de la clave JWT cada 90 días.

2. **Rate Limiting**: Agregar middleware de rate limiting para prevenir ataques de fuerza bruta.

3. **Monitoreo**: Implementar alertas para intentos de login fallidos repetidos.

4. **Backup Seguro**: Configurar backups encriptados de la base de datos.

5. **Actualizaciones**: Mantener todas las dependencias actualizadas para parches de seguridad.

6. **Logs de Seguridad**: Implementar logging detallado de eventos de seguridad.

7. **Validación de Sesión**: Implementar validación de sesión en cada request crítico.

## Troubleshooting

### Problemas Comunes

#### Error de Conexión a Base de Datos

**Síntoma**: `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server`

**Solución**:

1. Verificar que PostgreSQL esté ejecutándose
2. Confirmar credenciales en DATABASE_URL
3. Verificar conectividad de red
4. Revisar configuración de firewall

```bash
# Verificar estado de PostgreSQL
sudo systemctl status postgresql

# Probar conexión manual
psql -h localhost -U usuario -d auth_db
```

#### Token JWT Inválido

**Síntoma**: `HTTPException: Token inválido`

**Posibles Causas**:

- Token expirado
- Clave secreta incorrecta
- Token malformado

**Solución**:

```python
# Verificar configuración de JWT
from app.auth.jwt_handler import verify_token

try:
    payload = verify_token(token)
    print("Token válido:", payload)
except Exception as e:
    print("Error en token:", str(e))
```

#### Error de Permisos

**Síntoma**: `HTTPException: No tiene permisos para acceder a esta funcionalidad`

**Solución**:

1. Verificar que el usuario tenga roles asignados
2. Confirmar que el rol tenga permisos para la API
3. Revisar configuración de decoradores de seguridad

```sql
-- Verificar roles del usuario
SELECT u.username, r.nombre as rol
FROM usuarios u
JOIN usuario_roles ur ON u.id = ur.id_usuario
JOIN roles r ON ur.id_rol = r.id
WHERE u.id = 123;

-- Verificar permisos de API del rol
SELECT a.url_api, a.nombre
FROM api a
JOIN permiso_api pa ON a.id = pa.api
WHERE pa.rol = 1;
```

#### Error de Autenticación Microsoft

**Síntoma**: `Error al obtener token: invalid_client`

**Solución**:

1. Verificar configuración en Azure AD
2. Confirmar CLIENT_ID y CLIENT_SECRET
3. Revisar URL de redirección registrada
4. Verificar permisos de API en Azure

```python
# Verificar configuración OAuth
from app.auth.microsoft_oauth import microsoft_oauth

print("Client ID:", microsoft_oauth.client_id)
print("Redirect URI:", microsoft_oauth.redirect_uri)
print("Authority:", microsoft_oauth.authority)
```

### Logs y Debugging

#### Habilitar Logging Detallado

```python
# main.py
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auth_system.log'),
        logging.StreamHandler()
    ]
)

# Habilitar logs de SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Debugging de Base de Datos

```python
# Habilitar echo en SQLAlchemy para ver queries
engine = create_async_engine(
    settings.database_url,
    echo=True,  # Mostrar todas las queries SQL
    future=True
)
```

#### Monitoreo de Performance

```python
# Middleware para medir tiempo de respuesta
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### Herramientas de Diagnóstico

#### Script de Verificación del Sistema

```python
# scripts/health_check.py
import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def check_database():
    try:
        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Error de base de datos: {e}")
        return False

async def check_api():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            return response.status_code == 200
    except Exception as e:
        print(f"Error de API: {e}")
        return False

async def main():
    print("Verificando sistema...")

    db_ok = await check_database()
    api_ok = await check_api()

    print(f"Base de datos: {'✓' if db_ok else '✗'}")
    print(f"API: {'✓' if api_ok else '✗'}")

    if db_ok and api_ok:
        print("Sistema funcionando correctamente")
    else:
        print("Sistema con problemas")

if __name__ == "__main__":
    asyncio.run(main())
```

#### Validación de Configuración

```python
# scripts/validate_config.py
from app.core.config import settings
import re

def validate_config():
    errors = []

    # Validar SECRET_KEY
    if len(settings.secret_key) < 32:
        errors.append("SECRET_KEY debe tener al menos 32 caracteres")

    # Validar DATABASE_URL
    if not settings.database_url.startswith("postgresql"):
        errors.append("DATABASE_URL debe usar PostgreSQL")

    # Validar configuración Microsoft
    if not settings.microsoft_client_id:
        errors.append("MICROSOFT_CLIENT_ID no configurado")

    # Validar CORS
    if "*" in settings.cors_origins and not settings.debug:
        errors.append("CORS con '*' no recomendado en producción")

    if errors:
        print("Errores de configuración:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Configuración válida")

if __name__ == "__main__":
    validate_config()
```

Este sistema de autenticación proporciona una base sólida y escalable para aplicaciones web modernas, con todas las funcionalidades requeridas implementadas de manera segura y eficiente. La documentación completa y los ejemplos proporcionados facilitan tanto el uso como el mantenimiento del sistema.
