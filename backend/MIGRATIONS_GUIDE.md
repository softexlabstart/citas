# 🔄 Guía Definitiva de Migraciones Django

## 🚨 Problema Común: Conflictos de Migraciones

### Error Típico:
```
NodeNotFoundError: Migration organizacion.0007_... dependencies reference
nonexistent parent node ('organizacion', '0006_organizacion_slug')
```

### ¿Por qué sucede?

```
LOCAL (tu computadora):          SERVIDOR (producción):
migrations/                      migrations/
├── 0001_initial.py              ├── 0001_initial.py
├── 0002_...                     ├── 0002_...
├── 0003_...                     ├── 0003_...
├── 0004_...                     ├── 0004_...
├── 0005_...                     ├── 0005_...
├── 0006_organizacion_slug.py    └── (NO EXISTE 0006)
└── 0007_tenant_schema.py

❌ 0007 depende de 0006, pero el servidor no tiene 0006!
```

---

## ✅ SOLUCIÓN DEFINITIVA

### Estrategia: "Unified Migrations" (Migraciones Unificadas)

Cuando vayas a hacer cambios que requieran migración:

#### Paso 1: Antes de crear migraciones, verifica el servidor

```bash
# En el servidor
ssh ec2-user@appcitas.softex-labs.xyz
cd ~/appcitas/citas/backend
source ../venv/bin/activate

# Ver qué migraciones están aplicadas
python manage.py showmigrations organizacion
```

**Salida:**
```
organizacion
 [X] 0001_initial
 [X] 0002_create_groups
 [X] 0003_create_recurso_group
 [X] 0004_organizacion_alter_sede_nombre_sede_organizacion
 [X] 0005_auto_20250925_1552
```

**Anota la última migración:** `0005_auto_20250925_1552`

#### Paso 2: En local, crea UNA sola migración que incluya TODO

```bash
# En local
cd ~/Desktop/proyecto-citas-/backend

# Si ya tienes migraciones problemáticas (0006, 0007), elimínalas
rm organizacion/migrations/0006_*.py
rm organizacion/migrations/0007_*.py

# Crear una nueva migración unificada
python manage.py makemigrations organizacion --name tenant_schema_support
```

#### Paso 3: Editar la migración para que dependa de la última del servidor

```python
# backend/organizacion/migrations/0006_tenant_schema_support.py

class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0005_auto_20250925_1552'),  # ← La última que existe en servidor
    ]

    operations = [
        # Todos tus cambios aquí
        migrations.AddField(...),
        migrations.AddField(...),
        # etc.
    ]
```

#### Paso 4: Buscar y actualizar referencias en otras apps

```bash
# Buscar referencias a migraciones viejas
grep -r "0006_organizacion_slug" backend/*/migrations/*.py
grep -r "0007_organizacion" backend/*/migrations/*.py
```

Si encuentras referencias, actualízalas:

```python
# Cambiar de:
dependencies = [
    ('organizacion', '0006_organizacion_slug'),
]

# A:
dependencies = [
    ('organizacion', '0006_tenant_schema_support'),
]
```

#### Paso 5: Commit y push

```bash
git add backend/*/migrations/
git commit -m "fix: unify migrations to avoid conflicts"
git push
```

#### Paso 6: En el servidor, pull y migrar

```bash
# En el servidor
cd ~/appcitas/citas
git pull

cd backend
source ../venv/bin/activate

# Migrar
python manage.py migrate

# Reiniciar
sudo systemctl restart gunicorn
```

---

## 📋 Checklist para Crear Migraciones (SIEMPRE SEGUIR)

Antes de hacer `python manage.py makemigrations`:

- [ ] 1. Verificar última migración en servidor: `ssh ... && python manage.py showmigrations`
- [ ] 2. Si tienes migraciones locales no pusheadas, considera eliminarlas y recrear
- [ ] 3. Hacer `git pull` para sincronizar con el repo
- [ ] 4. Crear migración con nombre descriptivo: `makemigrations --name descriptive_name`
- [ ] 5. Editar dependencies para que apunte a la última del servidor
- [ ] 6. Buscar referencias en otras apps: `grep -r "nombre_migracion_vieja"`
- [ ] 7. Hacer commit y push INMEDIATAMENTE
- [ ] 8. Aplicar en servidor dentro de las siguientes 24 horas

---

## 🛠️ Comandos Útiles

### Ver estado de migraciones

```bash
# Ver todas las migraciones y su estado
python manage.py showmigrations

# Ver solo de una app
python manage.py showmigrations organizacion

# Ver migraciones no aplicadas
python manage.py showmigrations --plan
```

### Fake migrations (CUIDADO)

Si una migración ya está aplicada manualmente en la BD pero Django no lo sabe:

```bash
# Marcar como aplicada sin ejecutar
python manage.py migrate organizacion 0006_tenant_schema_support --fake
```

### Revertir migraciones

```bash
# Volver a migración específica
python manage.py migrate organizacion 0005_auto_20250925_1552

# Deshacer todas las migraciones de una app
python manage.py migrate organizacion zero
```

### Squash migrations (Combinar varias en una)

```bash
# Combinar migraciones 0001-0010 en una sola
python manage.py squashmigrations organizacion 0001 0010
```

---

## 🚀 Estrategia Recomendada: Squash Periódico

Cada 3-6 meses, combina todas las migraciones en una sola:

```bash
# 1. Backup de la BD primero
pg_dump appcitas > backup_before_squash.sql

# 2. Squash todas las migraciones
python manage.py squashmigrations organizacion 0001 0006

# Esto crea: 0001_squashed_0006_tenant_schema_support.py

# 3. Aplicar en desarrollo
python manage.py migrate

# 4. Si funciona, eliminar migraciones viejas
rm organizacion/migrations/0001_initial.py
rm organizacion/migrations/0002_*.py
# ... etc (dejar solo la squashed)

# 5. Renombrar la squashed migration
mv 0001_squashed_0006_tenant_schema_support.py 0001_initial.py

# 6. Commit y aplicar en servidor
```

---

## 🔥 Fix de Emergencia: Servidor Desincronizado

Si el servidor ya tiene el error y no puedes hacer migrate:

### Opción 1: Fake la migración problemática

```bash
# En el servidor
python manage.py migrate organizacion 0006_tenant_schema_support --fake

# Esto marca la migración como aplicada sin ejecutar SQL
# Úsala SOLO si los campos ya existen en la BD
```

### Opción 2: Aplicar SQL manualmente y luego fake

```bash
# 1. Conectar a PostgreSQL
psql -U postgres appcitas

# 2. Aplicar los cambios manualmente
ALTER TABLE organizacion_organizacion ADD COLUMN schema_name VARCHAR(63);
ALTER TABLE organizacion_organizacion ADD COLUMN database_name VARCHAR(63);
ALTER TABLE organizacion_organizacion ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
-- etc.

# 3. Salir de psql
\q

# 4. Marcar migración como aplicada
python manage.py migrate organizacion 0006_tenant_schema_support --fake
```

### Opción 3: Reset migrations (ÚLTIMA OPCIÓN, DESTRUCTIVA)

```bash
# ⚠️ SOLO SI NO TIENES DATOS IMPORTANTES

# 1. Eliminar todas las tablas de la app
python manage.py migrate organizacion zero

# 2. Borrar historial de migraciones en BD
psql -U postgres appcitas
DELETE FROM django_migrations WHERE app = 'organizacion';
\q

# 3. Aplicar migraciones desde cero
python manage.py migrate organizacion
```

---

## 📊 Debugging de Conflictos

### Ver el grafo de dependencias

```python
python manage.py shell
```

```python
from django.db.migrations.loader import MigrationLoader

loader = MigrationLoader(None, ignore_no_migrations=True)

# Ver todas las migraciones cargadas
for app_label, migrations in loader.disk_migrations.items():
    print(f"\n{app_label}:")
    for migration_name, migration in migrations.items():
        print(f"  {migration_name}")
        print(f"    Depends on: {migration.dependencies}")

# Ver migraciones aplicadas
applied = loader.applied_migrations
print(f"\nAplicadas: {len(applied)}")
```

### Ver SQL de una migración sin aplicarla

```bash
python manage.py sqlmigrate organizacion 0006_tenant_schema_support
```

---

## 🎯 Mejores Prácticas

### ✅ DO (Hacer)

1. **Siempre verificar el servidor antes de crear migraciones**
2. **Usar nombres descriptivos**: `--name add_tenant_support`
3. **Una migración por feature**: No mezclar cambios de diferentes features
4. **Commit y push inmediatamente** después de crear migración
5. **Aplicar en servidor dentro de 24 horas** después del push
6. **Hacer backup antes de migrar en producción**
7. **Revisar el SQL generado**: `python manage.py sqlmigrate app nombre`
8. **Usar default values o null=True** para campos nuevos

### ❌ DON'T (No hacer)

1. **Nunca editar migraciones ya pusheadas/aplicadas**
2. **No crear múltiples migraciones en ramas diferentes**
3. **No hacer `makemigrations` sin verificar estado del servidor**
4. **No eliminar migraciones que ya están en producción**
5. **No hacer cambios de schema directamente en PostgreSQL** sin fake
6. **No usar `migrate --fake-initial` sin entender qué hace**
7. **No dejar migraciones sin aplicar por más de 1 semana**

---

## 🔧 Template para Migraciones Complejas

```python
# organizacion/migrations/0007_descriptive_name.py

from django.db import migrations, models

def forwards_func(apps, schema_editor):
    """
    Data migration: modifica datos existentes
    """
    Organizacion = apps.get_model('organizacion', 'Organizacion')
    db_alias = schema_editor.connection.alias

    # Ejemplo: generar schema_name para organizaciones existentes
    for org in Organizacion.objects.using(db_alias).all():
        if not org.schema_name:
            org.schema_name = f"tenant_{org.slug}_{org.id}"
            org.save()

def reverse_func(apps, schema_editor):
    """
    Revertir data migration
    """
    pass  # O implementar rollback

class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0006_previous_migration'),
    ]

    operations = [
        # 1. Cambios de schema primero
        migrations.AddField(
            model_name='organizacion',
            name='schema_name',
            field=models.CharField(max_length=63, blank=True),
        ),

        # 2. Data migration después
        migrations.RunPython(forwards_func, reverse_func),

        # 3. Constraints al final
        migrations.AlterField(
            model_name='organizacion',
            name='schema_name',
            field=models.CharField(max_length=63, unique=True),  # Ahora con unique
        ),
    ]
```

---

## 📞 Cuándo Pedir Ayuda

Si encuentras estos errores, detente y revisa esta guía:

- `NodeNotFoundError: ... dependencies reference nonexistent parent node`
- `InconsistentMigrationHistory: ... applied before its dependency`
- `django.db.utils.ProgrammingError: column "..." does not exist`
- `django.db.utils.IntegrityError: ... violates unique constraint`

---

## ✅ Resumen Ejecutivo

1. **SIEMPRE verificar servidor** antes de crear migraciones
2. **UNA migración unificada** mejor que varias pequeñas
3. **Commit y push INMEDIATAMENTE**
4. **Aplicar en servidor en < 24 horas**
5. **Hacer backup antes de migrar en producción**
6. **Squash cada 3-6 meses** para limpiar historial

**Regla de oro:** Si tienes dudas, pregunta ANTES de hacer migrate en producción.
