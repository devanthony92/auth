# Configuración de autenticación con Gmail OAuth2

**Autor:** Manus AI (@Fabio Garcia)  
**Fecha:** 2025-01-18  
**Versión:** 1.0

## Descripción general

Esta guía proporciona instrucciones paso a paso para configurar la autenticación con Gmail OAuth2 en el sistema de autenticación.

## Requisitos previos

- Cuenta de Google
- Acceso a Google Cloud Console
- Backend ejecutándose localmente o en producción

## Paso 1: Crear un proyecto en Google Cloud Console

### 1.1 Acceder a Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Iniciar sesión con tu cuenta de Google
3. Si es la primera vez, aceptar los términos de servicio

### 1.2 Crear un nuevo proyecto

1. En la barra superior, hacer clic en el selector de proyectos
2. Hacer clic en "Nuevo proyecto"
3. Ingresar un nombre descriptivo (ej: "Sistema de Autenticación")
4. Hacer clic en "Crear"
5. Esperar a que se cree el proyecto (puede tomar unos minutos)

## Paso 2: Habilitar la API de Google+

### 2.1 Acceder a la biblioteca de APIs

1. En el menú lateral, ir a "APIs y servicios" → "Biblioteca"
2. Buscar "Google+ API"
3. Hacer clic en el resultado

### 2.2 Habilitar la API

1. Hacer clic en el botón "Habilitar"
2. Esperar a que se complete la habilitación

## Paso 3: Crear credenciales OAuth2

### 3.1 Ir a la pantalla de consentimiento OAuth

1. En el menú lateral, ir a "APIs y servicios" → "Pantalla de consentimiento"
2. Seleccionar "Usuario externo" como tipo de usuario
3. Hacer clic en "Crear"

### 3.2 Completar la información de la aplicación

**Información de la aplicación:**
- **Nombre de la aplicación:** Sistema de Autenticación
- **Email de soporte:** tu_email@ejemplo.com
- **Logotipo de la aplicación:** (opcional) Subir un logo

**Información de contacto del desarrollador:**
- **Email:** tu_email@ejemplo.com

Hacer clic en "Guardar y continuar"

### 3.3 Definir permisos

1. Hacer clic en "Agregar o quitar permisos"
2. Buscar y seleccionar los siguientes permisos:
   - `openid` - Verificar identidad del usuario
   - `email` - Acceso al email del usuario
   - `profile` - Acceso al perfil del usuario

3. Hacer clic en "Guardar y continuar"

### 3.4 Agregar usuarios de prueba (opcional)

Si estás en desarrollo, puedes agregar usuarios de prueba:
1. Hacer clic en "Agregar usuarios"
2. Ingresar direcciones de email de prueba
3. Hacer clic en "Agregar"

Hacer clic en "Guardar y continuar"

## Paso 4: Crear credenciales de cliente OAuth

### 4.1 Ir a credenciales

1. En el menú lateral, ir a "APIs y servicios" → "Credenciales"
2. Hacer clic en "Crear credenciales" → "ID de cliente OAuth"

### 4.2 Configurar el tipo de aplicación

1. Seleccionar "Aplicación web" como tipo de aplicación
2. Ingresar un nombre descriptivo (ej: "Backend de Autenticación")

### 4.3 Configurar URIs autorizados

**URIs de redirección autorizados:**

Agregar las siguientes URIs según tu entorno:

**Desarrollo local:**
```
http://localhost:8000/api/v1/auth/gmail/callback
```

**Producción:**
```
https://tu-dominio.com/api/v1/auth/gmail/callback
```

**Otros entornos (si aplica):**
```
https://staging.tu-dominio.com/api/v1/auth/gmail/callback
```

### 4.4 Crear las credenciales

1. Hacer clic en "Crear"
2. Se mostrará un modal con tus credenciales
3. **Copiar y guardar:**
   - **Client ID**
   - **Client Secret**

⚠️ **IMPORTANTE:** Guardar estas credenciales en un lugar seguro. El Client Secret no se mostrará nuevamente.

## Paso 5: Configurar el archivo .env

### 5.1 Actualizar variables de entorno

Editar el archivo `.env` en la raíz del proyecto y agregar/actualizar:

```env
# ============================================
# AUTENTICACIÓN GMAIL OAUTH2
# ============================================
GMAIL_CLIENT_ID=tu_client_id_aqui
GMAIL_CLIENT_SECRET=tu_client_secret_aqui
GMAIL_REDIRECT_URI=http://localhost:8000/api/v1/auth/gmail/callback
```

### 5.2 Reemplazar valores

- `tu_client_id_aqui`: Reemplazar con el Client ID obtenido en el paso 4.4
- `tu_client_secret_aqui`: Reemplazar con el Client Secret obtenido en el paso 4.4
- `GMAIL_REDIRECT_URI`: Ajustar según tu entorno (local, staging, producción)

## Paso 6: Reiniciar el backend

```bash
# Detener el servidor actual (Ctrl+C)

# Reiniciar el servidor
python main.py

# O si usas uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Paso 7: Probar la autenticación

### 7.1 Obtener URL de autorización

Realizar una solicitud GET a:

```
GET http://localhost:8000/api/v1/auth/gmail/login
```

Respuesta esperada:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "token_estado_unico"
}
```

### 7.2 Redirigir al usuario

1. Copiar la `authorization_url`
2. Abrir en el navegador
3. Iniciar sesión con tu cuenta de Google
4. Autorizar el acceso a la aplicación

### 7.3 Verificar el callback

El usuario será redirigido a:
```
http://localhost:8000/api/v1/auth/gmail/callback?code=...&state=...
```

Si todo está configurado correctamente, recibirá un JWT token y será autenticado en el sistema.

## Endpoints disponibles

### Login con Gmail

**GET** `/api/v1/auth/gmail/login`

Parámetros de query:
- `redirect_url` (opcional): URL a la que redirigir después del login

Respuesta:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "token_estado_unico"
}
```

### Callback de Gmail

**GET** `/api/v1/auth/gmail/callback`

Parámetros de query (proporcionados por Google):
- `code`: Código de autorización
- `state`: Token de estado para validar CSRF

Respuesta (si es exitoso):
```json
{
  "access_token": "jwt_token_aqui",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "usuario@gmail.com",
    "nombres": "Juan",
    "apellidos": "Pérez"
  },
  "roles": [...],
  "menus": [...],
  "apis": [...],
  "aplicaciones": [...],
  "provider": "gmail"
}
```

### Vincular cuenta de Gmail

**POST** `/api/v1/auth/gmail/link`

Headers:
```
Authorization: Bearer {jwt_token}
```

Body:
```json
{
  "code": "codigo_de_autorizacion",
  "state": "token_estado"
}
```

Respuesta:
```json
{
  "message": "Cuenta de Gmail vinculada correctamente"
}
```

## Solución de problemas

### Error: "redirect_uri_mismatch"

**Causa:** La URI de redirección no coincide con la configurada en Google Cloud Console.

**Solución:**
1. Verificar que la URI en `.env` coincida exactamente con la configurada en Google Cloud Console
2. Verificar que no haya espacios en blanco adicionales
3. Verificar que el protocolo (http/https) sea correcto

### Error: "invalid_client"

**Causa:** Client ID o Client Secret son incorrectos.

**Solución:**
1. Verificar que el Client ID y Client Secret sean correctos
2. Copiar nuevamente desde Google Cloud Console
3. Reiniciar el backend después de actualizar

### Error: "access_denied"

**Causa:** El usuario rechazó la autorización.

**Solución:**
- Es un comportamiento normal. El usuario puede intentar de nuevo.

### El usuario no se crea automáticamente

**Causa:** Puede haber un error en la creación del usuario.

**Solución:**
1. Verificar los logs del backend
2. Verificar que la base de datos esté conectada correctamente
3. Verificar permisos de escritura en la base de datos

## Seguridad

### Mejores prácticas

1. **Nunca compartir el Client Secret**
   - Mantenerlo seguro en variables de entorno
   - No incluirlo en el control de versiones

2. **Usar HTTPS en producción**
   - Cambiar `http://` a `https://` en la URI de redirección
   - Actualizar en Google Cloud Console

3. **Validar tokens**
   - El backend valida automáticamente los tokens
   - Verificar que el token sea válido antes de usar los datos del usuario

4. **Usar CSRF tokens**
   - El sistema genera automáticamente tokens de estado para prevenir CSRF
   - No modificar ni ignorar estos tokens

## Integración en frontend

### Ejemplo con JavaScript/React

```javascript
// Obtener URL de autorización
const response = await fetch('http://localhost:8000/api/v1/auth/gmail/login', {
  method: 'GET'
});

const data = await response.json();

// Redirigir al usuario a Gmail
window.location.href = data.authorization_url;

// El callback será manejado automáticamente por el backend
// El usuario será redirigido con el token JWT
```

### Almacenar el token

```javascript
// El backend retornará el token en la URL o en la respuesta
const token = new URLSearchParams(window.location.search).get('token');

// Guardar en localStorage (o sessionStorage)
localStorage.setItem('access_token', token);

// Usar en futuras solicitudes
const headers = {
  'Authorization': `Bearer ${token}`
};
```

## Referencias

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## Soporte

Para reportar problemas o sugerencias, contactar al equipo de desarrollo.

---

**Última actualización:** 2025-01-18
