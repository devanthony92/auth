# Guía de migración de MySQL a PostgreSQL

**Autor:** Manus AI (@Fabio Garcia)  
**Fecha:** 2025-01-18  
**Versión:** 1.0

## Descripción general

Esta guía proporciona instrucciones para migrar la base de datos del sistema de autenticación de MySQL a PostgreSQL.

## Requisitos previos

- Python 3.8 o superior
- MySQL con datos existentes
- PostgreSQL instalado y ejecutándose
- Acceso a ambas bases de datos

## Paso 1: Preparar el entorno

### 1.1 Instalar dependencias necesarias

```bash
# Instalar paquetes Python requeridos
pip install aiomysql asyncpg aiohttp

# O si usas pip3
pip3 install aiomysql asyncpg aiohttp
```

### 1.2 Verificar conexión a MySQL

```bash
# Probar conexión a MySQL
mysql -h mysql-idpyba-shared-dev-centralus-001.mysql.database.azure.com \
      -u dev_idpyba \
      -p \
      -e "SELECT VERSION();"
```

### 1.3 Verificar conexión a PostgreSQL

```bash
# Probar conexión a PostgreSQL
psql -h localhost -U auth_user -d auth_db -c "SELECT VERSION();"
```

## Paso 2: Configurar archivos de configuración

### 2.1 Actualizar mysql_config.json

Editar `scripts/mysql_config_example.json`:

```json
{
  "host": "mysql-idpyba-shared-dev-centralus-001.mysql.database.azure.com",
  "port": 3306,
  "user": "dev_idpyba",
  "password": "p6cOPEtElETO",
  "database": "auth_db"
}
```

Guardar como `scripts/mysql_config.json`

### 2.2 Actualizar postgresql_config.json

Editar `scripts/postgresql_config_example.json`:

```json
{
  "host": "localhost",
  "port": 5432,
  "user": "auth_user",
  "password": "auth_password_secure",
  "database": "auth_db"
}
```

Guardar como `scripts/postgresql_config.json`

## Paso 3: Crear base de datos PostgreSQL

### 3.1 Crear la base de datos

```bash
# Conectarse a PostgreSQL como superusuario
psql -U postgres

# Crear base de datos
CREATE DATABASE auth_db;

# Crear usuario
CREATE USER auth_user WITH PASSWORD 'auth_password_secure';

# Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;

# Conectarse a la nueva base de datos
\c auth_db

# Otorgar permisos en el schema public
GRANT ALL ON SCHEMA public TO auth_user;

# Salir
\q
```

### 3.2 Verificar la base de datos

```bash
# Verificar que la base de datos se creó
psql -U auth_user -d auth_db -c "SELECT 1;"
```

## Paso 4: Ejecutar la migración

### 4.1 Ejecutar el script de migración

```bash
# Navegar al directorio del proyecto
cd /ruta/al/proyecto

# Ejecutar el script de migración
python3 scripts/migrate_mysql_to_postgresql.py \
  --source-db scripts/mysql_config.json \
  --target-db scripts/postgresql_config.json
```

### 4.2 Monitorear el progreso

El script mostrará logs indicando:
- Tablas encontradas en MySQL
- Conversión de tipos de datos
- Creación de tablas en PostgreSQL
- Errores o advertencias

Ejemplo de salida:
```
2025-01-18 10:30:45,123 - INFO - Iniciando migración de MySQL a PostgreSQL...
2025-01-18 10:30:45,234 - INFO - Exportando esquema de MySQL...
2025-01-18 10:30:46,345 - INFO - Tablas encontradas: ['usuarios', 'roles', 'menus', ...]
2025-01-18 10:30:46,456 - INFO - Se exportaron 10 tablas
2025-01-18 10:30:46,567 - INFO - Importando esquema a PostgreSQL...
2025-01-18 10:30:47,678 - INFO - Tabla creada exitosamente
...
2025-01-18 10:30:50,789 - INFO - Migración completada exitosamente
```

## Paso 5: Validar la migración

### 5.1 Verificar tablas creadas

```bash
# Conectarse a PostgreSQL
psql -U auth_user -d auth_db

# Listar tablas
\dt

# Verificar estructura de una tabla
\d usuarios

# Contar registros
SELECT COUNT(*) FROM usuarios;

# Salir
\q
```

### 5.2 Comparar datos entre bases de datos

```bash
# MySQL - Contar registros
mysql -h mysql-idpyba-shared-dev-centralus-001.mysql.database.azure.com \
      -u dev_idpyba \
      -p auth_db \
      -e "SELECT TABLE_NAME, TABLE_ROWS FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'auth_db';"

# PostgreSQL - Contar registros
psql -U auth_user -d auth_db -c "
SELECT schemaname, tablename, n_live_tup 
FROM pg_stat_user_tables 
ORDER BY schemaname, tablename;
"
```

## Paso 6: Actualizar configuración de la aplicación

### 6.1 Actualizar .env

Editar el archivo `.env` en la raíz del proyecto:

```env
# ============================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================
# Tipo de base de datos: mysql, postgresql, mssql
DB_TYPE=postgresql

# Parámetros de conexión a la base de datos
DB_HOST=localhost
DB_PORT=5432
DB_USER=auth_user
DB_PASSWORD=auth_password_secure
DB_NAME=auth_db
DB_SCHEMA=public

# Configuración SSL para la conexión
DB_SSL=prefer
```

### 6.2 Actualizar requirements.txt (si es necesario)

Si aún no está instalado, agregar:

```
asyncpg==0.29.0
```

## Paso 7: Reiniciar la aplicación

### 7.1 Detener la aplicación actual

```bash
# Presionar Ctrl+C en la terminal donde corre la aplicación
```

### 7.2 Reiniciar con PostgreSQL

```bash
# Navegar al directorio del proyecto
cd /ruta/al/proyecto

# Instalar dependencias (si es necesario)
pip install -r requirements.txt

# Ejecutar la aplicación
python main.py

# O si usas uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7.3 Verificar que la aplicación funciona

```bash
# Probar endpoint de verificación
curl http://localhost:8000/api/v1/

# Respuesta esperada:
# {"message":"API v1 funcionando correctamente"}
```

## Paso 8: Migrar datos (si es necesario)

Si necesitas migrar datos además del esquema:

### 8.1 Exportar datos de MySQL

```bash
# Exportar datos en formato SQL
mysqldump -h mysql-idpyba-shared-dev-centralus-001.mysql.database.azure.com \
          -u dev_idpyba \
          -p \
          auth_db > backup_mysql.sql
```

### 8.2 Importar datos a PostgreSQL

```bash
# Crear script de conversión (si es necesario)
# Algunos tipos de datos pueden requerir conversión

# Importar datos
psql -U auth_user -d auth_db < backup_mysql.sql
```

## Solución de problemas

### Error: "aiomysql not installed"

**Solución:**
```bash
pip install aiomysql
```

### Error: "asyncpg not installed"

**Solución:**
```bash
pip install asyncpg
```

### Error: "connection refused" para MySQL

**Causa:** No se puede conectar a MySQL

**Solución:**
1. Verificar que MySQL está ejecutándose
2. Verificar credenciales en `mysql_config.json`
3. Verificar conectividad de red
4. Verificar firewall

### Error: "connection refused" para PostgreSQL

**Causa:** No se puede conectar a PostgreSQL

**Solución:**
1. Verificar que PostgreSQL está ejecutándose: `pg_isready`
2. Verificar credenciales en `postgresql_config.json`
3. Verificar que la base de datos existe: `psql -l`
4. Verificar permisos del usuario

### Error: "permission denied" en PostgreSQL

**Causa:** El usuario no tiene permisos suficientes

**Solución:**
```bash
# Conectarse como superusuario
psql -U postgres -d auth_db

# Otorgar permisos
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auth_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auth_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO auth_user;

# Salir
\q
```

### Tablas no se crean

**Causa:** Puede haber errores en la conversión de tipos de datos

**Solución:**
1. Revisar los logs del script de migración
2. Ejecutar manualmente el CREATE TABLE para la tabla problemática
3. Verificar que los tipos de datos son válidos en PostgreSQL

## Reversión (volver a MySQL)

Si necesitas revertir a MySQL:

### 1. Actualizar .env

```env
DB_TYPE=mysql
DB_HOST=mysql-idpyba-shared-dev-centralus-001.mysql.database.azure.com
DB_PORT=3306
DB_USER=dev_idpyba
DB_PASSWORD=p6cOPEtElETO
DB_NAME=auth_db
```

### 2. Reinstalar dependencias

```bash
pip install aiomysql
```

### 3. Reiniciar la aplicación

```bash
python main.py
```

## Mejores prácticas

1. **Hacer backup antes de migrar**
   ```bash
   mysqldump -h mysql-idpyba-shared-dev-centralus-001.mysql.database.azure.com \
             -u dev_idpyba -p auth_db > backup_mysql.sql
   ```

2. **Probar en ambiente de desarrollo primero**
   - Migrar a una base de datos de prueba
   - Validar que todo funciona correctamente
   - Luego migrar a producción

3. **Mantener ambas bases de datos temporalmente**
   - Hasta estar seguro de que la migración fue exitosa
   - Tener un plan de rollback

4. **Documentar cambios**
   - Registrar la fecha y hora de la migración
   - Documentar cualquier problema encontrado
   - Documentar soluciones aplicadas

## Referencias

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MySQL to PostgreSQL Migration](https://wiki.postgresql.org/wiki/MySQL_to_PostgreSQL_Conversion)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [aiomysql Documentation](https://aiomysql.readthedocs.io/)

## Soporte

Para reportar problemas o sugerencias, contactar al equipo de desarrollo.

---

**Última actualización:** 2025-01-18
