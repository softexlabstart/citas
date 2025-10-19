# 📋 Sistema de Roles Multi-Tenant - Documentación Completa

## 🎯 Visión General

Este sistema permite gestionar usuarios con **múltiples roles** en un entorno **multi-tenant** (multi-organización). Es perfecto para SaaS donde:
- Un usuario puede tener diferentes roles en diferentes organizaciones
- Un usuario puede tener múltiples roles simultáneos (ej: colaborador + cliente)
- Se necesita control granular de permisos y acceso a sedes

---

## 🎭 Los 5 Roles del Sistema

### 1. 👑 **Owner (Propietario)**
- **Descripción**: Dueño de la organización
- **Acceso**: TOTAL a todas las sedes y funcionalidades
- **Uso**: Para el fundador/dueño del negocio
- **Ejemplo**: Juan es dueño de la cadena de salones "Glamour" con 3 sedes

### 2. 🔴 **Admin (Administrador)**
- **Descripción**: Administrador global de la organización
- **Acceso**: TOTAL a todas las sedes (como owner pero sin ser propietario)
- **Uso**: Para gerentes generales o co-administradores
- **Ejemplo**: María es administradora general y puede gestionar todas las sedes

### 3. 🟠 **Sede Admin (Administrador de Sede)**
- **Descripción**: Administrador de sedes específicas
- **Acceso**: Solo a las sedes que administra
- **Uso**: Para gerentes de sucursales individuales
- **Ejemplo**: Carlos administra solo la Sede Norte

### 4. 🟢 **Colaborador**
- **Descripción**: Empleado/recurso que atiende citas
- **Acceso**: Solo a su(s) sede(s) de trabajo y citas asignadas
- **Uso**: Para estilistas, médicos, técnicos, etc.
- **Ejemplo**: Ana es manicurista en la Sede Centro
- **Multi-sede**: Puede trabajar en varias sedes

### 5. 🔵 **Cliente**
- **Descripción**: Usuario final que agenda citas
- **Acceso**: Solo sus propias citas
- **Uso**: Para clientes/pacientes del servicio
- **Ejemplo**: Pedro agenda citas para cortarse el pelo

---

## ✨ Características Clave

### Multi-Rol Simultáneo
Un usuario puede tener **rol principal + roles adicionales**:

```python
# Ana es colaboradora PERO también cliente
perfil.role = 'colaborador'
perfil.additional_roles = ['cliente']

# Puede:
# - Atender citas como manicurista
# - Agendar citas para ella misma como cliente
```

### Multi-Sede
Colaboradores pueden trabajar en múltiples sedes:

```python
# Dr. López trabaja en 2 sedes
perfil.role = 'colaborador'
perfil.sedes_trabajo = [sede_cardiologia, sede_urgencias]
```

### Permisos Personalizados
Sistema flexible de permisos granulares:

```python
perfil.permissions = {
    "can_view_reports": True,
    "can_export_data": False,
    "can_manage_inventory": True
}
```

---

## 🏗️ Arquitectura del Sistema

### Modelo Principal: `PerfilUsuario`

```python
class PerfilUsuario(models.Model):
    # Relación con usuario y organización
    user = ForeignKey(User)
    organizacion = ForeignKey(Organizacion)

    # Sistema de Roles
    role = CharField(choices=ROLE_CHOICES)  # Rol principal
    additional_roles = JSONField()  # Roles adicionales
    is_active = BooleanField()  # Membresía activa

    # Sedes según rol
    sede = ForeignKey(Sede)  # Sede principal
    sedes = ManyToManyField(Sede)  # Sedes de trabajo (colaboradores)
    sedes_administradas = ManyToManyField(Sede)  # Sedes administradas

    # Permisos
    permissions = JSONField()  # Permisos personalizados
```

### Helpers Principales

```python
# Obtener rol de un usuario
from usuarios.utils import get_user_role_in_org
role = get_user_role_in_org(user, organizacion)  # 'colaborador'

# Verificar si tiene un rol
from usuarios.utils import user_has_role
if user_has_role(user, 'admin'):
    # Hacer algo solo para admins

# Obtener sedes accesibles
from usuarios.utils import get_user_accessible_sedes
sedes = get_user_accessible_sedes(user, organizacion)

# Verificar acceso a sede específica
from usuarios.utils import user_can_access_sede
if user_can_access_sede(user, sede):
    # Permitir acceso
```

---

## 🔐 Sistema de Permisos

### Clases de Permisos Disponibles

#### 1. `IsOwnerOrAdmin`
Solo propietarios y administradores:
```python
class MiVista(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
```

#### 2. `IsSedeAdmin`
Administradores de sede (y superiores):
```python
class MiVista(APIView):
    permission_classes = [IsAuthenticated, IsSedeAdmin]
```

#### 3. `IsColaborador`
Colaboradores (y superiores):
```python
class MiVista(APIView):
    permission_classes = [IsAuthenticated, IsColaborador]
```

#### 4. `HasRoleInCurrentOrg`
Verifica roles específicos:
```python
class MiVista(APIView):
    permission_classes = [HasRoleInCurrentOrg]
    required_roles = ['owner', 'admin', 'sede_admin']
```

#### 5. `CanAccessSede`
Verifica acceso a sede (nivel de objeto):
```python
class MiVista(APIView):
    permission_classes = [IsAuthenticated, CanAccessSede]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj
```

#### 6. `HasCustomPermission`
Verifica permisos personalizados:
```python
class ReportsView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = 'can_view_reports'
```

---

## 📡 API Endpoints

### 1. Crear Usuario con Rol

**POST** `/api/usuarios/create-user/`

```json
{
    "email": "ana@example.com",
    "first_name": "Ana",
    "last_name": "García",
    "password": "secure123",
    "role": "colaborador",
    "additional_roles": ["cliente"],
    "sede_principal_id": 1,
    "sedes_trabajo_ids": [1, 2],
    "permissions": {"can_view_reports": true}
}
```

**Respuesta:**
```json
{
    "id": 42,
    "email": "ana@example.com",
    "role": "colaborador",
    "additional_roles": ["cliente"],
    "display_badge": "🟢 Colaborador +1",
    "message": "Usuario creado exitosamente como Colaborador"
}
```

### 2. Listar Organizaciones del Usuario

**GET** `/api/usuarios/my-organizations/`

**Respuesta:**
```json
{
    "count": 2,
    "organizations": [
        {
            "id": 1,
            "nombre": "Salon Glamour",
            "slug": "salon-glamour",
            "role": "colaborador",
            "all_roles": ["colaborador", "cliente"],
            "display_badge": "🟢 Colaborador +1"
        },
        {
            "id": 2,
            "nombre": "Clínica Salud",
            "slug": "clinica-salud",
            "role": "cliente",
            "all_roles": ["cliente"],
            "display_badge": "🔵 Cliente"
        }
    ]
}
```

### 3. Cambiar Organización Activa

**POST** `/api/usuarios/switch-organization/`

```json
{
    "organization_id": 2
}
```

**Respuesta:**
```json
{
    "message": "Organización cambiada exitosamente",
    "organization_id": 2
}
```

---

## 🎨 Django Admin

### Interfaz Simplificada

El Django Admin ahora tiene una interfaz intuitiva con:

#### List Display
- Email del usuario
- Organización
- Badge del rol (🟢 Colaborador +1)
- Roles adicionales
- Estado activo/inactivo
- Cantidad de sedes accesibles

#### Fieldsets Organizados

1. **👤 Usuario y Organización**
   - Usuario, Organización, Estado activo

2. **🎭 Sistema de Roles**
   - Rol Principal (dropdown)
   - Roles Adicionales (JSON, ej: `["cliente"]`)

3. **🏢 Sedes según Rol**
   - Sede Principal
   - Sedes de Trabajo (para colaboradores)
   - Sedes Administradas (para admins de sede)

4. **🔐 Permisos Personalizados**
   - JSON con permisos granulares

#### Acciones Disponibles
- ✅ Activar perfiles
- ❌ Desactivar perfiles

#### Auto-Sincronización
Cuando guardas un perfil con rol `colaborador`, automáticamente:
- Crea el registro en el modelo `Colaborador`
- Sincroniza la sede principal

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Crear un Colaborador Multi-Sede

**Django Admin:**
1. Agregar Perfil de Usuario
2. Seleccionar Usuario y Organización
3. Rol Principal: `Colaborador`
4. Sede Principal: `Sede Centro`
5. Sedes de Trabajo: `Sede Centro, Sede Norte`
6. Guardar

**Código Python:**
```python
perfil = PerfilUsuario.objects.create(
    user=ana_user,
    organizacion=mi_org,
    role='colaborador',
    sede=sede_centro
)
perfil.sedes.set([sede_centro, sede_norte])
```

### Ejemplo 2: Colaborador que También es Cliente

**API Request:**
```json
POST /api/usuarios/create-user/
{
    "email": "pedro@example.com",
    "first_name": "Pedro",
    "last_name": "Ruiz",
    "password": "secure123",
    "role": "colaborador",
    "additional_roles": ["cliente"],
    "sede_principal_id": 1
}
```

**Código Python:**
```python
perfil = PerfilUsuario.objects.create(
    user=pedro_user,
    organizacion=mi_org,
    role='colaborador',
    additional_roles=['cliente'],
    sede_id=1
)
```

### Ejemplo 3: Verificar Permisos en una Vista

```python
from rest_framework.views import APIView
from usuarios.permissions import HasRoleInCurrentOrg

class CrearColaboradorView(APIView):
    permission_classes = [HasRoleInCurrentOrg]
    required_roles = ['owner', 'admin', 'sede_admin']

    def post(self, request):
        # Solo owners, admins y admins de sede pueden acceder
        ...
```

### Ejemplo 4: Obtener Sedes Accesibles para un Usuario

```python
from usuarios.utils import get_user_accessible_sedes

# En una vista
def get_queryset(self):
    sedes = get_user_accessible_sedes(self.request.user)
    return Cita.objects.filter(sede__in=sedes)
```

---

## 🔄 Migración desde Sistema Anterior

El sistema es **totalmente compatible** con el código anterior. Los campos antiguos siguen existiendo:

- ✅ `perfil.sede` - Sigue funcionando
- ✅ `perfil.sedes` - Sigue funcionando
- ✅ `perfil.sedes_administradas` - Sigue funcionando
- ✅ `get_perfil_or_first(user)` - Sigue funcionando

**Nuevas capacidades agregadas:**
- ✨ Campo `role` para identificar rol fácilmente
- ✨ Campo `additional_roles` para multi-rol
- ✨ Campo `is_active` para control de membresías
- ✨ Campo `permissions` para permisos granulares
- ✨ Métodos helper en el modelo
- ✨ Helpers utilitarios para verificar roles

---

## ✅ Checklist de Implementación

### Backend
- [x] Modelo `PerfilUsuario` actualizado
- [x] Migración de base de datos aplicada
- [x] Helpers en `usuarios/utils.py`
- [x] Clases de permisos en `usuarios/permissions.py`
- [x] Django Admin actualizado
- [x] Serializers creados
- [x] Endpoints de API implementados
- [x] URLs configuradas

### Frontend (Pendiente)
- [ ] Componente `CreateUserForm`
- [ ] Selector de organización
- [ ] Dashboard por rol
- [ ] Integración con API

---

## 🚀 Próximos Pasos

1. **Testing**: Crear tests unitarios para los nuevos helpers y permisos
2. **Frontend**: Implementar componentes React para crear usuarios
3. **Documentación de API**: Usar Swagger/OpenAPI para documentar endpoints
4. **Migraciones de Datos**: Script para poblar `role` en perfiles existentes (si es necesario)

---

## 📞 Soporte

Para dudas o problemas con el sistema de roles:
- Revisar este documento
- Revisar código en `/backend/usuarios/`
- Revisar permisos en `/backend/usuarios/permissions.py`

---

## 📚 Referencias

- **Modelos**: `/backend/usuarios/models.py`
- **Helpers**: `/backend/usuarios/utils.py`
- **Permisos**: `/backend/usuarios/permissions.py`
- **Admin**: `/backend/usuarios/admin.py`
- **Serializers**: `/backend/usuarios/serializers.py`
- **Views**: `/backend/usuarios/views.py`
- **URLs**: `/backend/usuarios/urls.py`

---

**Última actualización**: 2025-10-19
**Versión**: 1.0.0
