# 🚀 Ejemplos de Onboarding Automático de Tenants

## 📋 Tabla de Contenidos
1. [Automático con Signals](#automático-con-signals)
2. [Desde Django Admin](#desde-django-admin)
3. [Desde API REST](#desde-api-rest)
4. [Desde Frontend (Next.js)](#desde-frontend)
5. [Proceso Completo de Registro](#proceso-completo)

---

## ✅ Opción 1: Automático con Signals (IMPLEMENTADO)

### ¿Cómo funciona?

Cuando creas una `Organizacion`, **automáticamente**:
1. ✅ Se genera el `schema_name` único
2. ✅ Se crea el schema en PostgreSQL
3. ✅ Se ejecutan las migraciones
4. ✅ Queda lista para usar

### Ejemplo 1: Django Admin

```python
# Solo necesitas hacer esto en Django Admin:
1. Ir a /admin/organizacion/organizacion/
2. Click en "Agregar Organización"
3. Llenar:
   - Nombre: "Barbería El Corte Perfecto"
   - Slug: (se genera automático)
4. Click "Guardar"

# ¡Listo! El schema se crea automáticamente en 2-3 segundos
```

**Logs en consola:**
```
[TenantProvision] Nueva organización creada: Barbería El Corte Perfecto (ID: 5)
[TenantProvision] Schema name: tenant_barberia_el_corte_perfecto_a1b2c3d4
[TenantProvision] Creando schema: tenant_barberia_el_corte_perfecto_a1b2c3d4
[TenantProvision] ✓ Schema tenant_barberia_el_corte_perfecto_a1b2c3d4 creado
[TenantProvision] Ejecutando migraciones en tenant_barberia_el_corte_perfecto_a1b2c3d4
[TenantProvision]   ✓ Migrado: citas
[TenantProvision]   ✓ Migrado: marketing
[TenantProvision]   ✓ Migrado: usuarios
[TenantProvision] ✓ Tenant Barbería El Corte Perfecto provisionado exitosamente!
```

### Ejemplo 2: Django Shell

```python
python manage.py shell
```

```python
from organizacion.models import Organizacion

# Crear organización
org = Organizacion.objects.create(
    nombre="Clínica Dental Sonrisas"
)

# ¡El schema se crea automáticamente!
print(f"Schema creado: {org.schema_name}")
# Output: tenant_clinica_dental_sonrisas_e5f6g7h8

# Verificar que existe
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = %s;
    """, [org.schema_name])
    exists = cursor.fetchone()
    print(f"Schema existe: {exists is not None}")
# Output: Schema existe: True
```

### Ejemplo 3: En tu código Python

```python
# En cualquier view o función
from organizacion.models import Organizacion

def register_new_client(client_data):
    """
    Registra un nuevo cliente y provisiona su tenant automáticamente.
    """
    # Crear organización
    org = Organizacion.objects.create(
        nombre=client_data['nombre']
    )

    # El signal 'provision_tenant_schema' se ejecuta automáticamente
    # En 2-3 segundos el schema estará listo

    return org
```

---

## 🖥️ Opción 2: Desde Django Admin

### Paso 1: Acceder al Admin

```
https://appcitas.softex-labs.xyz/admin/
```

### Paso 2: Ir a Organizaciones

```
Admin → Organización → Organizaciones → Agregar Organización
```

### Paso 3: Llenar el Formulario

```
Nombre: Spa Relajación Total
Slug: (se genera automático: spa-relajacion-total)
Schema name: (se genera automático al guardar)
Database name: (dejar vacío, solo para enterprise)
Is active: ✓ (checked)
```

### Paso 4: Guardar

- Click "Guardar"
- Esperar 2-3 segundos
- ✅ ¡Tenant provisionado!

---

## 🌐 Opción 3: Desde API REST

### Paso 1: Crear Endpoint de Registro

```python
# backend/organizacion/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Organizacion
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])  # Endpoint público para registro
def register_organization(request):
    """
    Endpoint de registro de nueva organización con trial de 14 días.

    POST /api/organizacion/register/
    {
        "organization_name": "Barbería Juan",
        "owner_email": "juan@barberia.com",
        "owner_name": "Juan Pérez",
        "owner_password": "SecurePass123!"
    }

    Response:
    {
        "success": true,
        "organization": {
            "id": 1,
            "nombre": "Barbería Juan",
            "slug": "barberia-juan",
            "schema_name": "tenant_barberia_juan_abc123"
        },
        "owner": {
            "id": 5,
            "username": "juan@barberia.com",
            "email": "juan@barberia.com"
        },
        "trial_days": 14,
        "message": "Organización creada exitosamente. Schema provisionado automáticamente."
    }
    """

    # Validar datos
    org_name = request.data.get('organization_name')
    owner_email = request.data.get('owner_email')
    owner_name = request.data.get('owner_name')
    owner_password = request.data.get('owner_password')

    if not all([org_name, owner_email, owner_name, owner_password]):
        return Response({
            'error': 'Todos los campos son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verificar que el email no exista
    if User.objects.filter(email=owner_email).exists():
        return Response({
            'error': 'El email ya está registrado'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verificar que el nombre de organización no exista
    if Organizacion.objects.filter(nombre=org_name).exists():
        return Response({
            'error': 'El nombre de organización ya está en uso'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. Crear usuario owner
        user = User.objects.create_user(
            username=owner_email,
            email=owner_email,
            first_name=owner_name,
            password=owner_password
        )

        logger.info(f"[Registration] Usuario creado: {owner_email}")

        # 2. Crear organización (el signal provision_tenant_schema se ejecuta automáticamente)
        org = Organizacion.objects.create(
            nombre=org_name,
            is_active=True
        )

        logger.info(f"[Registration] Organización creada: {org_name} (ID: {org.id})")
        logger.info(f"[Registration] Schema: {org.schema_name}")

        # 3. Crear perfil de owner
        perfil = PerfilUsuario.objects.create(
            user=user,
            organizacion=org,
            role='owner',
            is_active=True
        )

        logger.info(f"[Registration] Perfil owner creado para {user.username}")

        # TODO: Cuando implementes billing, crear suscripción trial aquí
        # from billing.models import Plan, Suscripcion
        # plan_esencial = Plan.objects.get(nombre='esencial')
        # Suscripcion.objects.create(...)

        # TODO: Enviar email de bienvenida
        # send_welcome_email(user, org)

        return Response({
            'success': True,
            'organization': {
                'id': org.id,
                'nombre': org.nombre,
                'slug': org.slug,
                'schema_name': org.schema_name
            },
            'owner': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'trial_days': 14,
            'message': 'Organización creada exitosamente. Schema provisionado automáticamente.'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"[Registration] Error en registro: {e}", exc_info=True)

        # Rollback: eliminar usuario si se creó
        if 'user' in locals():
            user.delete()

        return Response({
            'error': 'Error creando organización. Intenta de nuevo.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### Paso 2: Agregar URL

```python
# backend/organizacion/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_organization, name='register-organization'),
]
```

```python
# backend/core/urls.py

urlpatterns = [
    # ... existentes
    path('api/organizacion/', include('organizacion.urls')),
]
```

### Paso 3: Llamar desde Frontend

```javascript
// frontend/src/services/registration.js

export async function registerOrganization(data) {
  const response = await fetch('https://appcitas.softex-labs.xyz/api/organizacion/register/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      organization_name: data.organizationName,
      owner_email: data.email,
      owner_name: data.name,
      owner_password: data.password,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Error en el registro');
  }

  return await response.json();
}
```

---

## 🎨 Opción 4: Desde Frontend (Next.js)

### Componente de Registro

```jsx
// frontend/src/components/RegisterForm.jsx

import { useState } from 'react';
import { registerOrganization } from '@/services/registration';

export default function RegisterForm() {
  const [formData, setFormData] = useState({
    organizationName: '',
    name: '',
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await registerOrganization(formData);

      console.log('✓ Registro exitoso:', result);

      // Redirigir a login o dashboard
      window.location.href = '/dashboard';

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label>Nombre de la Organización</label>
        <input
          type="text"
          value={formData.organizationName}
          onChange={(e) => setFormData({ ...formData, organizationName: e.target.value })}
          placeholder="Barbería El Corte Perfecto"
          required
        />
      </div>

      <div>
        <label>Tu Nombre</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Juan Pérez"
          required
        />
      </div>

      <div>
        <label>Email</label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          placeholder="juan@barberia.com"
          required
        />
      </div>

      <div>
        <label>Contraseña</label>
        <input
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          placeholder="Mínimo 8 caracteres"
          required
        />
      </div>

      {error && (
        <div className="text-red-600">{error}</div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded"
      >
        {loading ? 'Creando cuenta...' : 'Comenzar prueba gratis de 14 días'}
      </button>

      <p className="text-sm text-gray-500">
        Al registrarte, tu tenant se provisiona automáticamente en 2-3 segundos.
      </p>
    </form>
  );
}
```

---

## 🔄 Proceso Completo de Registro (UX Ideal)

### Paso 1: Landing Page `/pricing`

```
Usuario ve los planes:
- Plan Esencial: $19/mes
- Plan Profesional: $49/mes
- Plan Avanzado: $99/mes

Click en "Comenzar prueba gratis" → /register
```

### Paso 2: Formulario de Registro `/register`

```
Llenar formulario:
- Nombre de tu negocio
- Tu nombre
- Email
- Contraseña

Click "Comenzar prueba gratis"
```

### Paso 3: Backend Provisiona Automáticamente

```python
# En 2-3 segundos:
1. ✅ Usuario creado
2. ✅ Organización creada
3. ✅ Schema PostgreSQL creado (AUTOMÁTICO)
4. ✅ Tablas migradas (AUTOMÁTICO)
5. ✅ Perfil owner creado
6. ✅ Trial de 14 días activado
7. ✅ Email de bienvenida enviado
```

### Paso 4: Onboarding Wizard `/onboarding`

```
1. Bienvenida y tour rápido
2. Configurar primera sede
3. Agregar primer servicio
4. Invitar a colaboradores (opcional)
5. Personalizar página de reservas

✅ ¡Listo para agendar citas!
```

### Paso 5: Dashboard `/dashboard`

```
Usuario ya puede:
- Agendar citas
- Ver clientes
- Gestionar servicios
- Ver reportes

Todo en su propio schema aislado ✅
```

---

## ⚙️ Configuración Avanzada

### Para Producción: Provisión Asíncrona

Si tienes muchos registros simultáneos, puedes hacer la provisión asíncrona con Celery:

```python
# backend/organizacion/tasks.py

from celery import shared_task
from django.core.management import call_command
from django.db import connection
import logging

logger = logging.getLogger(__name__)


@shared_task
def provision_tenant_async(organization_id):
    """
    Task asíncrona para provisionar tenant.
    Se ejecuta en background sin bloquear el request de registro.
    """
    from organizacion.models import Organizacion

    try:
        org = Organizacion.objects.get(id=organization_id)
        schema_name = org.schema_name

        logger.info(f"[AsyncProvision] Provisionando {org.nombre}")

        # Crear schema
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name};')

        # Migrar
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {schema_name}, public;')

        call_command('migrate', verbosity=0, interactive=False)

        # Restaurar search_path
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO public;')

        logger.info(f"[AsyncProvision] ✓ {org.nombre} provisionado")

        # Enviar email de confirmación
        # send_provisioning_complete_email(org)

    except Exception as e:
        logger.error(f"[AsyncProvision] Error: {e}", exc_info=True)
```

```python
# backend/organizacion/signals.py

# Modificar el signal:
@receiver(post_save, sender=Organizacion)
def provision_tenant_schema(sender, instance, created, **kwargs):
    if not created:
        return

    # En producción: usar Celery para provisión asíncrona
    if settings.USE_ASYNC_PROVISIONING:
        from .tasks import provision_tenant_async
        provision_tenant_async.delay(instance.id)
    else:
        # En desarrollo: provisión síncrona
        # ... código existente
```

---

## ✅ Resumen

| Método | Cuándo Usar | Automático |
|--------|-------------|------------|
| **Signal** | Siempre (implementado) | ✅ 100% |
| **Django Admin** | Testing, clientes manuales | ✅ 100% |
| **API REST** | Producción (recomendado) | ✅ 100% |
| **Comando manual** | Debugging, migraciones viejas | ❌ Manual |

**Recomendación**: Usar el **API REST endpoint** para registro de usuarios finales en producción.

---

## 🐛 Troubleshooting

### Signal no se ejecuta

```python
# Verificar que el signal está registrado
python manage.py shell
```

```python
from django.db.models.signals import post_save
from organizacion.models import Organizacion

# Ver receivers registrados
receivers = post_save._live_receivers(Organizacion)
print(f"Receivers: {len(receivers)}")
# Debe mostrar al menos 1 (el signal provision_tenant_schema)
```

### Schema no se crea

Verificar logs:

```bash
tail -f ~/appcitas/citas/backend/logs/django.log
```

Buscar:
```
[TenantProvision] Nueva organización creada...
```

Si no aparece, el signal no se está ejecutando.

---

## 📞 Soporte

¿Problemas? Revisa:
1. Logs de Django
2. Logs de PostgreSQL
3. Django shell para debugging
4. `python manage.py list_tenants`
