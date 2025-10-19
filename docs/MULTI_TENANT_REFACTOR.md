# Refactor Multi-Tenant: Un Email, Múltiples Organizaciones

## 📋 Resumen Ejecutivo

Este documento describe el refactor completo del sistema de usuarios para soportar **verdadero multi-tenancy**, permitiendo que un usuario con un solo email y contraseña pueda acceder a múltiples organizaciones.

### Antes ❌
- Usuario necesitaba cuentas separadas para cada organización
- `juan@example.com` en Clínica ABC → Cuenta 1
- `juan@example.com` en Salón Bella → Cuenta 2 (ERROR: email duplicado)
- Experiencia fragmentada y confusa

### Ahora ✅
- Un solo usuario puede tener perfiles en múltiples organizaciones
- `juan@example.com` → Acceso a Clínica ABC, Salón Bella, Taller García
- Cambio fluido entre organizaciones
- Experiencia profesional tipo Slack/Discord

---

## 🎯 Casos de Uso Reales

### Caso 1: Usuario Colaborador en Varias Empresas
**Escenario:** María es estilista freelance que trabaja en 3 salones diferentes.

**Antes:**
```
❌ maria@gmail.com en Salón A → Cuenta 1
❌ maria.perez@gmail.com en Salón B → Cuenta 2  
❌ maria.stylist@gmail.com en Salón C → Cuenta 3
❌ 3 usuarios, 3 contraseñas diferentes
```

**Ahora:**
```
✅ maria@gmail.com → UN SOLO LOGIN
   ├── Salón Bella (Perfil 1)
   ├── Salón Glamour (Perfil 2)  
   └── Spa Relax (Perfil 3)
✅ Selecciona organización al iniciar sesión
✅ Cambia entre organizaciones sin volver a autenticarse
```

### Caso 2: Administrador Multi-Sede
**Escenario:** Carlos administra clínicas en diferentes ciudades bajo diferentes marcas.

**Antes:**
```
❌ No podía usar el mismo email
❌ Tenía que recordar múltiples contraseñas
```

**Ahora:**
```
✅ carlos@admin.com → UN SOLO LOGIN
   ├── Clínica Norte (Admin)
   ├── Clínica Sur (Admin)
   └── Clínica Centro (Admin)
✅ Dashboard muestra tarjetas de cada organización
✅ Click para cambiar de contexto
```

---

## 🏗️ Arquitectura del Refactor

### 1. Modelo de Datos

#### Antes (OneToOne)
```python
# ❌ Problema: Un usuario solo puede tener UN perfil
user = models.OneToOneField(User, related_name='perfil')
```

#### Ahora (ForeignKey)
```python
# ✅ Solución: Un usuario puede tener MÚLTIPLES perfiles
user = models.ForeignKey(User, related_name='perfiles')
organizacion = models.ForeignKey(Organizacion, ...)

class Meta:
    unique_together = ('user', 'organizacion')  # Un perfil por org
```

**Diagrama:**
```
User (juan@example.com)
├── PerfilUsuario 1 → Clínica ABC
├── PerfilUsuario 2 → Salón Bella
└── PerfilUsuario 3 → Taller García
```

### 2. Flujo de Autenticación

```
┌─────────────────────────────────────────────────────────┐
│ 1. Usuario ingresa credenciales                        │
│    username: juan@example.com                          │
│    password: ************                              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ 2. LoginView autentica y cuenta perfiles               │
│    perfiles_count = user.perfiles.count()              │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    count > 1            count == 1
         │                   │
         ▼                   ▼
┌─────────────────┐   ┌─────────────────┐
│ Múltiples Orgs  │   │ Una Sola Org    │
│ ├─ response:    │   │ ├─ response:    │
│ │  {           │   │ │  {           │
│ │   organizations│   │ │   user: {...}│
│ │   user: {...}│   │ │  }           │
│ │  }           │   │ └─ Flujo normal │
│ └─ Frontend:    │   └─────────────────┘
│    redirect to  │
│    /select-org  │
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ 3. SelectOrganizationPage                               │
│    Muestra tarjetas con cada organización               │
│    Usuario selecciona: "Clínica ABC"                    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ 4. localStorage.setItem('selectedOrganization', ...)    │
│    navigate('/')                                        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Axios interceptor agrega header                      │
│    X-Organization-ID: 123                               │
│    En TODAS las peticiones                              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ 6. Middleware lee header y filtra datos                 │
│    set_current_organization(org)                        │
│    Usuario ve solo datos de Clínica ABC                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Cambios Técnicos Detallados

### Backend

#### 1. Modelo PerfilUsuario (`backend/usuarios/models.py`)

```python
class PerfilUsuario(models.Model):
    # ANTES:
    # user = models.OneToOneField(User, related_name='perfil')
    
    # AHORA:
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='perfiles')
    organizacion = models.ForeignKey(Organizacion, ...)
    
    class Meta:
        unique_together = ('user', 'organizacion')
        indexes = [models.Index(fields=['user', 'organizacion'])]
```

**Migración requerida:**
```bash
python manage.py makemigrations usuarios
python manage.py migrate
```

#### 2. LoginView (`backend/usuarios/views.py`)

```python
class LoginView(APIView):
    def post(self, request):
        user = authenticate(...)
        
        # MULTI-TENANT: Contar perfiles
        perfiles_count = user.perfiles.count()
        
        if perfiles_count > 1:
            # Retornar lista de organizaciones
            organizaciones = []
            for perfil in user.perfiles.select_related('organizacion').all():
                if perfil.organizacion:
                    organizaciones.append({
                        'id': perfil.organizacion.id,
                        'nombre': perfil.organizacion.nombre,
                        'slug': perfil.organizacion.slug,
                        'perfil_id': perfil.id
                    })
            
            return Response({
                'organizations': organizaciones,
                'user': {...},
                'tokens': {...}
            })
        else:
            # Flujo normal (backward compatible)
            return Response({
                'user': {...},
                'tokens': {...}
            })
```

#### 3. RegisterByOrganizacionView & AcceptInvitationView

**Patrón get_or_create:**
```python
# ANTES: Siempre crear nuevo usuario
user = User.objects.create_user(...)

# AHORA: Buscar o crear
user, created = User.objects.get_or_create(
    email=email,
    defaults={
        'username': username or email.split('@')[0],
        'first_name': first_name,
        'last_name': last_name
    }
)

if created:
    # Usuario nuevo: establecer contraseña
    user.set_password(password)
    user.save()
else:
    # Usuario existente: verificar que no tenga perfil en esta org
    if PerfilUsuario.objects.filter(user=user, organizacion=org).exists():
        return Response({'error': 'Ya tienes acceso a esta organización'})

# Crear perfil en la organización
PerfilUsuario.objects.create(user=user, organizacion=org, ...)
```

#### 4. Middleware (`backend/organizacion/middleware.py`)

**Prioridades:**
```python
# 1. Header HTTP (usuarios multi-org)
org_id = request.META.get('HTTP_X_ORGANIZATION_ID')
if org_id:
    organizacion = Organizacion.objects.get(id=int(org_id))

# 2. Perfil único del usuario autenticado  
elif user.perfiles.count() == 1:
    organizacion = user.perfiles.first().organizacion

# 3. Slug en la URL (páginas públicas)
else:
    slug = resolver_match.kwargs.get('organizacion_slug')
    organizacion = Organizacion.objects.get(slug=slug)

set_current_organization(organizacion)
```

### Frontend

#### 1. AuthContext (`frontend/src/contexts/AuthContext.tsx`)

**Nuevas interfaces:**
```typescript
interface Organization {
    id: number;
    nombre: string;
    slug: string;
    perfil_id: number;
}

interface AuthContextType {
    user: User | null;
    organizations: Organization[] | null;
    selectedOrganization: Organization | null;
    login: (user, pwd) => Promise<{ needsOrgSelection: boolean }>;
    selectOrganization: (org: Organization) => void;
    // ... otros métodos
}
```

**Nuevo flujo de login:**
```typescript
const login = async (username, password) => {
    const response = await apiLogin(username, password);
    
    if (response.organizations && response.organizations.length > 0) {
        // Múltiples organizaciones
        setOrganizations(response.organizations);
        localStorage.setItem('organizations', JSON.stringify(response.organizations));
        return { needsOrgSelection: true };
    } else {
        // Una sola organización
        return { needsOrgSelection: false };
    }
};
```

#### 2. SelectOrganizationPage (`frontend/src/pages/SelectOrganizationPage.tsx`)

```typescript
const SelectOrganizationPage = () => {
    const { organizations, selectOrganization } = useAuth();
    const navigate = useNavigate();

    const handleSelect = (org: Organization) => {
        selectOrganization(org); // Guarda en localStorage
        navigate('/'); // Redirige al dashboard
    };

    return (
        <Container>
            {organizations.map(org => (
                <Card key={org.id} onClick={() => handleSelect(org)}>
                    <h5>{org.nombre}</h5>
                    <small>{org.slug}</small>
                </Card>
            ))}
        </Container>
    );
};
```

#### 3. Axios Interceptor (`frontend/src/api.ts`)

```typescript
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    // MULTI-TENANT: Agregar header con org seleccionada
    const selectedOrganization = localStorage.getItem('selectedOrganization');
    if (selectedOrganization) {
        const org = JSON.parse(selectedOrganization);
        if (org && org.id) {
            config.headers['X-Organization-ID'] = org.id.toString();
        }
    }

    return config;
});
```

---

## 🧪 Casos de Prueba

### Test 1: Usuario Nuevo en Primera Organización
```bash
# 1. Registrarse en Clínica ABC
POST /api/register/clinica-abc/
Body: { email: "juan@example.com", password: "test123", ... }

# ✅ Resultado:
# - Usuario creado
# - PerfilUsuario creado con organizacion=Clínica ABC
# - Login automático
# - Redirige a dashboard
```

### Test 2: Usuario Existente Se Registra en Segunda Organización
```bash
# 1. Juan ya tiene cuenta en Clínica ABC
# 2. Se registra en Salón Bella
POST /api/register/salon-bella/
Body: { email: "juan@example.com", password: "test123", ... }

# ✅ Resultado:
# - NO se crea nuevo User (ya existe)
# - SE crea nuevo PerfilUsuario con organizacion=Salón Bella
# - Ahora tiene 2 perfiles
```

### Test 3: Login con Múltiples Organizaciones
```bash
# 1. Login
POST /api/login/
Body: { username: "juan@example.com", password: "test123" }

# ✅ Respuesta:
{
    "organizations": [
        { "id": 1, "nombre": "Clínica ABC", "slug": "clinica-abc" },
        { "id": 2, "nombre": "Salón Bella", "slug": "salon-bella" }
    ],
    "user": { "id": 1, "username": "juan@example.com", ... },
    "tokens": { "access": "...", "refresh": "..." }
}

# 2. Frontend redirige a /select-organization
# 3. Usuario selecciona "Clínica ABC"
# 4. localStorage guarda org seleccionada
# 5. Todas las peticiones incluyen X-Organization-ID: 1
```

### Test 4: Verificar Filtrado de Datos
```bash
# Con X-Organization-ID: 1 (Clínica ABC)
GET /api/citas/citas/
Header: X-Organization-ID: 1

# ✅ Retorna solo citas de Clínica ABC

# Con X-Organization-ID: 2 (Salón Bella)
GET /api/citas/citas/
Header: X-Organization-ID: 2

# ✅ Retorna solo citas de Salón Bella
```

---

## 📊 Diagrama de Base de Datos

```
┌──────────────────┐
│      User        │
│ ────────────────│
│ id: 1            │
│ email: juan@...  │
│ password: ***    │
└────────┬─────────┘
         │
         │ ForeignKey
         │ (1 → Many)
         │
    ┌────┴────┬────────────┬────────────┐
    │         │            │            │
    ▼         ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Perfil1 │ │ Perfil2 │ │ Perfil3 │ │  ...    │
│ ───────│ │ ───────│ │ ───────│ │         │
│ id: 1   │ │ id: 2   │ │ id: 3   │ │         │
│ user: 1 │ │ user: 1 │ │ user: 1 │ │         │
│ org: 1  │ │ org: 2  │ │ org: 3  │ │         │
└────┬────┘ └────┬────┘ └────┬────┘ └─────────┘
     │           │           │
     │           │           │
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Org 1   │ │ Org 2   │ │ Org 3   │
│Clínica  │ │ Salón   │ │ Taller  │
│  ABC    │ │  Bella  │ │ García  │
└─────────┘ └─────────┘ └─────────┘
```

---

## ⚠️ Migraciones y Deployment

### Paso 1: Ejecutar en Servidor
```bash
cd /home/ec2-user/appcitas/citas/backend
source /home/ec2-user/appcitas/venv/bin/activate

# Crear migraciones
python manage.py makemigrations usuarios

# Revisar SQL generado (opcional)
python manage.py sqlmigrate usuarios XXXX

# Aplicar migración
python manage.py migrate

# Reiniciar gunicorn
sudo systemctl restart gunicorn
```

### Paso 2: Rebuild Frontend
```bash
cd /home/ec2-user/appcitas/citas/frontend
npm install  # Si hay nuevas dependencias
npm run build

# Reiniciar nginx si es necesario
sudo systemctl reload nginx
```

### Paso 3: Verificación Post-Deploy
```bash
# 1. Verificar migraciones aplicadas
python manage.py showmigrations usuarios

# 2. Verificar que usuarios existentes tienen perfiles
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from usuarios.models import PerfilUsuario
>>> for user in User.objects.all():
...     print(f"{user.email}: {user.perfiles.count()} perfiles")

# 3. Probar login desde frontend
# - Login con usuario existente
# - Verificar que no rompe flujo normal
```

---

## 🐛 Troubleshooting

### Problema 1: Migration Fails
```
django.db.utils.IntegrityError: duplicate key value violates unique constraint
```

**Causa:** Datos existentes violan unique_together

**Solución:**
```python
# Crear migración de datos ANTES del cambio de modelo
# migration_001_prepare_data.py

def prepare_data(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    PerfilUsuario = apps.get_model('usuarios', 'PerfilUsuario')
    
    # Encontrar duplicados
    duplicates = User.objects.annotate(
        perfiles_count=Count('perfil')
    ).filter(perfiles_count__gt=1)
    
    for user in duplicates:
        # Resolver duplicados
        # ... lógica específica según tus datos
```

### Problema 2: Frontend No Muestra Organizaciones
```
Usuario tiene múltiples perfiles pero ve flujo normal
```

**Debug:**
```typescript
// En LoginPage.tsx, agregar console.log
const result = await login(username, password);
console.log('Login result:', result);

// Verificar que:
// - result.needsOrgSelection === true
// - organizations en localStorage
```

**Verificar Backend:**
```python
# En LoginView, agregar logging
perfiles_count = user.perfiles.count()
logger.info(f'User {user.username} has {perfiles_count} profiles')
```

### Problema 3: Datos de Otra Organización Aparecen
```
Usuario ve citas que no debería ver
```

**Verificar:**
```bash
# 1. Revisar headers enviados
# En DevTools → Network → Request Headers
X-Organization-ID: 123

# 2. Verificar middleware
# Logs del servidor deben mostrar:
[OrgMiddleware] Org from header: Clínica ABC

# 3. Verificar OrganizacionManager
# ¿Todos los modelos usan el manager correcto?
```

---

## 📈 Métricas y Beneficios

### Antes del Refactor
- ❌ 1 usuario = 1 organización
- ❌ Email duplicado error al registrar en otra org
- ❌ Experiencia fragmentada
- ❌ 100 usuarios en 3 orgs = 300 cuentas

### Después del Refactor  
- ✅ 1 usuario = N organizaciones
- ✅ Mismo email en múltiples orgs
- ✅ Experiencia fluida
- ✅ 100 usuarios en 3 orgs = 100 cuentas, 300 perfiles

### Reducción de Complejidad
- **Usuarios**: -66% (300 → 100)
- **Contraseñas olvidadas**: -66%
- **Support tickets**: -40% (estimado)
- **UX profesional**: +∞%

---

## 🚀 Próximos Pasos

### Mejoras Futuras

1. **Selector de Organización en Navbar**
   - Dropdown para cambiar sin volver a login
   - Ver todas las orgs y cambiar con un click

2. **Notificaciones Multi-Org**
   - Badge con total de notificaciones de todas las orgs
   - Vista unificada de actividad

3. **Búsqueda Global**
   - Buscar clientes/citas en TODAS las organizaciones
   - Filtrar por organización específica

4. **Workspace Personalizado**
   - Cada org puede tener logo/colores personalizados
   - UI se adapta según org seleccionada

5. **Analytics Multi-Org**
   - Dashboard consolidado de todas las organizaciones
   - Comparativas de rendimiento

---

## 📚 Referencias

- [Django Multi-Tenancy Best Practices](https://books.agiliq.com/projects/django-multi-tenant/en/latest/)
- [Slack-like Organization Switching](https://slack.com/help/articles/206845317-Switch-between-workspaces)
- [Discord Server Switching UX](https://support.discord.com/hc/en-us/articles/115001494052)

---

**Versión:** 1.0  
**Fecha:** 2025-10-18  
**Autor:** Sistema Multi-Tenant  
**Generado con:** Claude Code 🤖
