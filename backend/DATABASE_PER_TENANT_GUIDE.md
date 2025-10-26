# 🏗️ Guía de Database-per-Tenant (Schema Isolation)

## 📋 Tabla de Contenidos
1. [Qué es Database-per-Tenant](#qué-es)
2. [Arquitectura](#arquitectura)
3. [Setup Inicial](#setup-inicial)
4. [Uso Diario](#uso-diario)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Qué es Database-per-Tenant

Tu aplicación ahora soporta **aislamiento total de datos por cliente** usando **schemas de PostgreSQL**.

### Antes (Multi-tenant con filtros):
```sql
-- Todas las citas en la misma tabla
SELECT * FROM citas_cita WHERE organizacion_id = 1;
```

### Ahora (Database-per-tenant):
```sql
-- Cada cliente tiene su propio schema
SET search_path TO tenant_barberia_juan_abc123, public;
SELECT * FROM citas_cita;  -- Solo ve sus propias citas
```

---

## 🏗️ Arquitectura

```
PostgreSQL Database: appcitas
│
├── Schema: public (COMPARTIDO)
│   ├── organizacion_organizacion  ← Lista de clientes
│   ├── auth_user                  ← Usuarios para login
│   ├── billing_plan               ← Planes de suscripción
│   └── billing_suscripcion        ← Suscripciones
│
├── Schema: tenant_barberia_juan_abc123 (Cliente 1)
│   ├── citas_cita
│   ├── citas_servicio
│   ├── usuarios_perfilusuario
│   └── organizacion_sede
│
├── Schema: tenant_clinica_dental_def456 (Cliente 2)
│   ├── citas_cita
│   ├── citas_servicio
│   └── ...
│
└── Schema: tenant_spa_belleza_ghi789 (Cliente 3)
    └── ...
```

### ✅ Ventajas:

1. **Máximo aislamiento**: Los datos de cada cliente están físicamente separados
2. **Seguridad**: Imposible ver datos de otro cliente por error de código
3. **Backups independientes**: `pg_dump -n tenant_X`
4. **Escalabilidad**: Clientes grandes pueden ir a otro servidor
5. **Compliance**: GDPR, HIPAA ready
6. **Migración a on-premise**: Solo exportas el schema del cliente

---

## 🚀 Setup Inicial

### 1. Ejecutar migración de base de datos compartida

```bash
cd ~/appcitas/citas/backend

# Migrar schema 'public' (tablas compartidas)
python manage.py migrate
```

Esto crea las tablas compartidas en el schema `public`:
- `organizacion_organizacion`
- `auth_user`
- `billing_*` (cuando lo implementes)

### 2. Actualizar organizaciones existentes

Si ya tienes organizaciones creadas, necesitas asignarles un `schema_name`:

```bash
python manage.py shell
```

```python
from organizacion.models import Organizacion
from django.utils.text import slugify
import uuid

# Asignar schema_name a organizaciones existentes
for org in Organizacion.objects.filter(schema_name=''):
    base_name = org.slug.replace('-', '_')[:20]
    unique_suffix = str(uuid.uuid4())[:8]
    org.schema_name = f"tenant_{base_name}_{unique_suffix}"
    org.is_active = True
    org.save()
    print(f"✓ {org.nombre} → {org.schema_name}")
```

### 3. Crear schemas para organizaciones existentes

```bash
# Listar tenants
python manage.py list_tenants

# Crear schema para un tenant específico
python manage.py create_tenant_schema --organization_id=1

# O crear para todos los tenants
python manage.py migrate_all_tenants
```

**Salida esperada:**
```
=== Migrando schema PUBLIC (compartido) ===
✓ Schema public migrado exitosamente

=== Migrando 3 tenants ===

[1/3] Migrando: Barbería Juan (schema: tenant_barberia_juan_abc123)
  ✓ Barbería Juan migrado

[2/3] Migrando: Clínica Dental (schema: tenant_clinica_dental_def456)
  ✓ Clínica Dental migrado

[3/3] Migrando: Spa Belleza (schema: tenant_spa_belleza_ghi789)
  ✓ Spa Belleza migrado

============================================================
✓ Exitosos: 3
============================================================
```

### 4. Reiniciar Gunicorn

```bash
sudo systemctl restart gunicorn
```

---

## 🎮 Uso Diario

### Cuando creas una nueva organización (cliente)

**Opción A: Automático (Recomendado)**

El schema se crea automáticamente cuando registras un nuevo cliente:

```python
# En tu view de registro o panel admin
from organizacion.models import Organizacion
from django.core.management import call_command

org = Organizacion.objects.create(nombre="Nueva Peluquería")
org.save()  # schema_name se genera automáticamente

# Crear el schema en PostgreSQL
call_command('create_tenant_schema', organization_id=org.id)
```

**Opción B: Manual**

```bash
# Crear organización en Django Admin primero
# Luego ejecutar:
python manage.py create_tenant_schema --slug=nueva-peluqueria
```

### Cuando haces cambios en modelos (migraciones)

```bash
cd ~/appcitas/citas/backend

# 1. Crear la migración
python manage.py makemigrations

# 2. Aplicar a schema público Y todos los tenants
python manage.py migrate_all_tenants
```

Esto ejecuta:
1. Migración en `public` (tablas compartidas)
2. Migración en cada `tenant_X` (tablas de cada cliente)

### Verificar estado de schemas

```bash
python manage.py list_tenants
```

**Salida:**
```
================================================================================
  TENANTS REGISTRADOS
================================================================================
ID    Nombre                        Schema                        Estado
--------------------------------------------------------------------------------
1     Barbería Juan                 tenant_barberia_juan_abc123   ✓ Activo
2     Clínica Dental                tenant_clinica_dental_def456  ✓ Activo
3     Spa Belleza                   tenant_spa_belleza_ghi789     ✓ Activo

================================================================================
  SCHEMAS EN POSTGRESQL
================================================================================
✓ public                                     → (Schema compartido)
✓ tenant_barberia_juan_abc123                → Barbería Juan
✓ tenant_clinica_dental_def456               → Clínica Dental
✓ tenant_spa_belleza_ghi789                  → Spa Belleza
================================================================================
```

---

## 🔍 Cómo Funciona (Para Entender)

### 1. Request llega al servidor

```
GET /api/citas/
Headers:
  Authorization: Bearer <jwt_token>
  X-Organization-ID: 1
```

### 2. OrganizacionMiddleware identifica el tenant

```python
# organizacion/middleware.py
def __call__(self, request):
    # Extrae el tenant del header o JWT
    org = Organizacion.objects.get(id=1)  # Barbería Juan
    set_current_organization(org)  # Guarda en thread-local
```

### 3. TenantSchemaMiddleware setea el search_path

```python
# core/tenant_middleware.py
def __call__(self, request):
    org = get_current_organization()

    # Ejecuta en PostgreSQL:
    # SET search_path TO tenant_barberia_juan_abc123, public;
```

### 4. TenantRouter enruta las queries

```python
# core/tenant_router.py
def db_for_read(self, model, **hints):
    if model == Cita:
        # Ya está en el schema correcto por search_path
        return 'default'
```

### 5. Django ejecuta la query

```python
# En tu view
citas = Cita.objects.all()
# SELECT * FROM citas_cita;
# PostgreSQL busca en: tenant_barberia_juan_abc123.citas_cita
```

---

## 🐛 Troubleshooting

### Error: "relation citas_cita does not exist"

**Causa**: El schema del tenant no ha sido creado o migrado.

**Solución**:
```bash
# Verificar schemas existentes
python manage.py list_tenants

# Crear schema faltante
python manage.py create_tenant_schema --organization_id=1
```

### Error: "User attempting to access unauthorized organization"

**Causa**: El usuario está intentando acceder a una organización donde no tiene perfil.

**Solución**:
```python
# Crear perfil para el usuario en esa organización
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User
from organizacion.models import Organizacion

user = User.objects.get(username='usuario')
org = Organizacion.objects.get(id=1)

PerfilUsuario.objects.create(
    user=user,
    organizacion=org,
    role='admin',
    is_active=True
)
```

### Ver queries ejecutadas (debugging)

```python
# En Django shell
import logging
logging.basicConfig(level=logging.DEBUG)

# O en settings.py (desarrollo)
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Consultar directamente un schema específico

```bash
psql -U postgres appcitas
```

```sql
-- Ver todos los schemas
\dn

-- Cambiar a schema de un tenant
SET search_path TO tenant_barberia_juan_abc123, public;

-- Ver tablas del tenant
\dt

-- Consultar datos
SELECT * FROM citas_cita;
```

### Backup de un tenant específico

```bash
# Backup solo de un cliente
pg_dump -U postgres -n tenant_barberia_juan_abc123 appcitas > barberia_juan_backup.sql

# Restore
psql -U postgres appcitas < barberia_juan_backup.sql
```

### Eliminar schema de un tenant (¡CUIDADO!)

```bash
psql -U postgres appcitas
```

```sql
-- Eliminar schema y TODOS sus datos (irreversible)
DROP SCHEMA tenant_barberia_juan_abc123 CASCADE;
```

---

## 📊 Comandos Útiles

| Comando | Descripción |
|---------|-------------|
| `python manage.py list_tenants` | Lista todos los tenants y schemas |
| `python manage.py create_tenant_schema --organization_id=1` | Crea schema para un tenant |
| `python manage.py migrate_all_tenants` | Migra todos los tenants |
| `python manage.py migrate_all_tenants --skip-public` | Solo migra tenants, no public |

---

## 🚀 Próximos Pasos

1. ✅ Sistema de database-per-tenant implementado
2. ⏳ Implementar sistema de billing con Wompi
3. ⏳ Crear proceso de onboarding automático (registro → trial → schema creation)
4. ⏳ Implementar backups automáticos por tenant
5. ⏳ Dashboard de admin para gestionar tenants

---

## 💡 Preguntas Frecuentes

**P: ¿Puedo tener clientes en diferentes servidores PostgreSQL?**
R: Sí, puedes configurar `database_name` en el modelo Organizacion para clientes enterprise.

**P: ¿Cuántos tenants puedo tener por servidor?**
R: PostgreSQL soporta miles de schemas. El límite práctico es ~500-1000 tenants por servidor.

**P: ¿Qué pasa si un tenant crece mucho?**
R: Puedes migrarlo a una base de datos dedicada:
1. `pg_dump -n tenant_X > tenant_X.sql`
2. Crear nuevo servidor PostgreSQL
3. `psql -d nueva_db < tenant_X.sql`
4. Actualizar `database_name` en Organizacion

**P: ¿Cómo hago búsquedas globales (cross-tenant)?**
R: Para admin/superuser, necesitas queries especiales con UNION:
```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT * FROM tenant_1.citas_cita
        UNION ALL
        SELECT * FROM tenant_2.citas_cita
        -- etc.
    """)
```

---

## 📞 Soporte

Si tienes problemas, revisa los logs:

```bash
# Logs de Django
tail -f ~/appcitas/citas/backend/logs/django.log

# Logs de PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log

# Logs de Gunicorn
sudo journalctl -u gunicorn -f
```
