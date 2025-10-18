# Sistema de Roles y Permisos

## Definición de Roles

### 1. SUPERUSUARIO (Superuser)
**Identificación**: `user.is_superuser = True`

**Permisos**:
- ✅ Acceso total al panel de administración de Django (`/admin`)
- ✅ Acceso total al panel de administración del frontend
- ✅ Puede ver y gestionar datos de TODAS las organizaciones
- ✅ Puede crear, editar y eliminar cualquier recurso
- ✅ Sin restricciones multi-tenant

**Casos de uso**:
- Administrador del sistema completo
- Soporte técnico de nivel superior
- Gestión de múltiples organizaciones

---

### 2. ADMINISTRADOR DE SEDE (Sede Admin)
**Identificación**: `user.perfil.sedes_administradas.exists() = True`

**Permisos**:
- ❌ NO puede acceder al panel de administración de Django
- ✅ Acceso al panel de administración del frontend
- ✅ Puede ver informes, marketing, configuración avanzada
- ✅ Solo de las sedes que administra
- ✅ Puede gestionar:
  - Citas de sus sedes
  - Servicios de sus sedes
  - Colaboradores de sus sedes
  - Clientes de su organización
  - Bloqueos de recursos de sus sedes

**Restricciones multi-tenant**:
- Solo ve datos de la organización a la que pertenece
- Solo puede administrar las sedes asignadas en `user.perfil.sedes_administradas`

**Casos de uso**:
- Gerente de una sucursal
- Administrador de clínica/consultorio
- Supervisor de sede

---

### 3. COLABORADOR (Colaborador)
**Identificación**: Existe registro en `Colaborador.all_objects.filter(usuario=user)`

**Permisos**:
- ❌ NO puede acceder al panel de administración de Django
- ⚠️ Acceso limitado al frontend
- ✅ Solo puede ver citas asignadas a él
- ✅ Puede generar citas a nombre de clientes
- ✅ Solo para clientes de su organización
- ✅ Solo para su sede

**Restricciones multi-tenant**:
- Solo ve citas donde está asignado como colaborador
- Solo puede crear citas para clientes de su organización
- Solo puede crear citas para su sede (`colaborador.sede`)
- Solo ve servicios de su organización
- Solo ve otros colaboradores de su organización
- Solo ve clientes de su organización

**Casos de uso**:
- Médico que atiende pacientes
- Estilista en salón de belleza
- Profesional que ofrece servicios
- Recepcionista que agenda citas

---

### 4. CLIENTE (Cliente)
**Identificación**: Usuario que NO es superuser, NO es sede admin, NO es colaborador

**Permisos**:
- ❌ NO puede acceder al panel de administración
- ✅ Puede ver su historial de citas
- ✅ Puede ver servicios (debe proporcionar `sede_id`)
- ✅ Puede sacar citas para sí mismo
- ✅ Puede cancelar sus propias citas
- ✅ Puede ver detalles de sus propias citas

**Restricciones multi-tenant**:
- Solo ve sus propias citas
- Para ver servicios, debe proporcionar `sede_id` en la petición
- No puede ver datos de otros clientes
- No puede crear citas a nombre de otros

**Casos de uso**:
- Paciente que agenda su cita médica
- Cliente que reserva servicio de belleza
- Usuario final del sistema

---

## Flujo de Permisos por Endpoint

### GET /api/citas/citas/
| Rol | Puede Ver |
|-----|-----------|
| Superusuario | Todas las citas |
| Sede Admin | Citas de sus sedes |
| Colaborador | Solo citas donde está asignado |
| Cliente | Solo sus propias citas |

### POST /api/citas/citas/
| Rol | Puede Crear |
|-----|-------------|
| Superusuario | Citas para cualquier usuario, cualquier sede |
| Sede Admin | Citas para usuarios de su organización, en sus sedes |
| Colaborador | Citas para clientes de su organización, en su sede (usando `user_id`) |
| Cliente | Solo citas para sí mismo |

### GET /api/citas/servicios/
| Rol | Puede Ver |
|-----|-----------|
| Superusuario | Todos los servicios |
| Sede Admin | Servicios de su organización |
| Colaborador | Servicios de su organización |
| Cliente | Servicios si proporciona `sede_id` |
| Anónimo | Servicios si proporciona `sede_id` |

### GET /api/citas/recursos/ (colaboradores)
| Rol | Puede Ver |
|-----|-----------|
| Superusuario | Todos los colaboradores |
| Sede Admin | Colaboradores de su organización |
| Colaborador | Colaboradores de su organización |
| Cliente | Colaboradores si proporciona `sede_id` |
| Anónimo | Colaboradores si proporciona `sede_id` |

### GET /api/clients/
| Rol | Puede Ver |
|-----|-----------|
| Superusuario | Todos los clientes |
| Sede Admin | Clientes de su organización |
| Colaborador | Clientes de su organización |
| Cliente | ❌ Ninguno |

---

## Validaciones Multi-Tenant

### Al crear una cita como Colaborador

1. **Validación de Sede**:
   ```python
   if sede_cita != colaborador.sede:
       raise PermissionDenied("Solo puedes crear citas para tu sede.")
   ```

2. **Validación de Organización**:
   ```python
   if client_user.perfil.organizacion != colaborador.sede.organizacion:
       raise PermissionDenied("Solo puedes crear citas para clientes de tu organización.")
   ```

### Al crear una cita como Sede Admin

1. **Validación de Sede Administrada**:
   ```python
   if sede_cita not in user.perfil.sedes_administradas.all():
       raise PermissionDenied("Solo puedes crear citas para las sedes que administras.")
   ```

---

## Clases de Permiso Implementadas

### `IsSuperUser`
Verifica `user.is_superuser`

### `IsSedeAdmin`
Verifica `user.perfil.sedes_administradas.exists()`

### `IsColaborador`
Verifica `Colaborador.all_objects.filter(usuario=user).exists()`

### `IsClient`
Usuario autenticado que NO es ninguno de los anteriores

### `IsAdminOrSedeAdminOrReadOnly`
- Lectura: cualquier autenticado
- Escritura: solo superuser o sede admin

### `IsColaboradorOrAdmin`
Permite acceso a superuser, sede admin, colaborador, y cliente (con permisos de objeto limitados)

### `CanAccessOrganizationData`
Verifica que el objeto pertenece a la misma organización del usuario

---

## Problema Solucionado

### Antes:
- Usuario colaborador no podía ver clientes para crear citas a su nombre
- `ClientViewSet` solo permitía acceso a `IsAdminOrSedeAdmin`
- No había filtrado por organización en `ClientViewSet`

### Después:
- `ClientViewSet` ahora permite acceso a colaboradores
- Colaboradores ven solo clientes de su organización
- Filtrado multi-tenant estricto en todos los endpoints
- Validaciones que previenen acceso cross-tenant

---

## Cómo Asignar Roles

### Superusuario
```bash
python manage.py createsuperuser
```

### Administrador de Sede
```python
# En Django Admin o mediante código
user.perfil.sedes_administradas.add(sede)
user.perfil.organizacion = organizacion
user.perfil.save()
```

### Colaborador
```python
# Crear registro de Colaborador vinculado al usuario
colaborador = Colaborador.objects.create(
    usuario=user,
    nombre=user.get_full_name(),
    email=user.email,
    sede=sede
)
```

### Cliente
```python
# Simplemente crear usuario sin asignar roles adicionales
user = User.objects.create_user(username, email, password)
PerfilUsuario.objects.create(
    user=user,
    organizacion=organizacion,  # Opcional
    sede=sede  # Opcional
)
```

---

## Testing de Permisos

Para verificar que un usuario tiene los permisos correctos:

```python
from citas.models import Colaborador

# Verificar si es superusuario
is_superuser = user.is_superuser

# Verificar si es sede admin
is_sede_admin = hasattr(user, 'perfil') and user.perfil.sedes_administradas.exists()

# Verificar si es colaborador
is_colaborador = Colaborador.all_objects.filter(usuario=user).exists()

# Si no es ninguno, es cliente
is_client = not (is_superuser or is_sede_admin or is_colaborador)
```
