# ✅ Implementación: Registro por Organización

## 📌 Resumen

Se ha implementado exitosamente un sistema de **registro de usuarios por organización mediante slug en la URL**. Esto permite que cada organización tenga su propia URL de registro personalizada, asegurando que los nuevos usuarios se asocien automáticamente a la organización correcta.

---

## 🎯 Problema Solucionado

**Antes:**
```
❌ URL genérica: http://16.52.17.116/register
❌ Usuario se registra sin organización
❌ Requiere asignación manual del administrador
❌ Riesgo de errores en la asignación
```

**Ahora:**
```
✅ URL personalizada: http://16.52.17.116/register/clinica-abc
✅ Usuario se asocia automáticamente a "Clínica ABC"
✅ Sin intervención manual
✅ Login automático después del registro
```

---

## 🚀 Implementación

### 1. Backend

#### **Nuevo Endpoint**
```python
# /backend/usuarios/views.py

class RegisterByOrganizacionView(generics.CreateAPIView):
    """
    Vista para registro de usuarios asociados a una organización específica.
    La organización se identifica mediante su slug en la URL.
    """
    permission_classes = [AllowAny]

    def create(self, request, organizacion_slug):
        # Validar que la organización existe
        organizacion = Organizacion.objects.get(slug=organizacion_slug)

        # Crear usuario
        user = User.objects.create_user(...)

        # Crear perfil asociado a la organización
        PerfilUsuario.objects.create(
            user=user,
            organizacion=organizacion,
            ...
        )

        # Generar tokens JWT para login automático
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': f'Registro exitoso en {organizacion.nombre}',
            'tokens': {...}
        })
```

#### **Nueva URL**
```python
# /backend/usuarios/urls.py

urlpatterns = [
    ...
    path('register/<slug:organizacion_slug>/',
         RegisterByOrganizacionView.as_view(),
         name='register_by_organization'),
]
```

**Endpoint API:**
```
POST /api/register/{organizacion_slug}/
```

**Ejemplo:**
```
POST /api/register/clinica-abc/

Body:
{
  "username": "juan.perez",
  "password": "contraseña123",
  "email": "juan@example.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "has_consented_data_processing": true
}

Response:
{
  "message": "Registro exitoso en Clínica ABC",
  "user": {...},
  "organizacion": {
    "id": 1,
    "nombre": "Clínica ABC",
    "slug": "clinica-abc"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1...",
    "refresh": "eyJ0eXAiOiJKV1..."
  }
}
```

#### **Endpoint Público de Organización**
```python
# /backend/organizacion/views.py

class OrganizacionPublicView(APIView):
    """Vista pública para obtener información de una organización por slug."""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        organizacion = Organizacion.objects.get(slug=slug)
        return Response({
            'id': organizacion.id,
            'nombre': organizacion.nombre,
            'slug': organizacion.slug
        })
```

**URL:**
```python
# /backend/organizacion/urls.py

path('organizaciones/<slug:slug>/',
     OrganizacionPublicView.as_view(),
     name='organizacion-public'),
```

**Endpoint API:**
```
GET /api/organizacion/organizaciones/{slug}/

Response:
{
  "id": 1,
  "nombre": "Clínica ABC",
  "slug": "clinica-abc"
}
```

---

### 2. Frontend

#### **Nueva Ruta**
```typescript
// /frontend/src/App.tsx

<Route path="/register" element={<RegisterPage />} />
<Route path="/register/:organizacionSlug" element={<RegisterPage />} />
```

#### **Componente Actualizado**
```typescript
// /frontend/src/pages/RegisterPage.tsx

const RegisterPage: React.FC = () => {
    const { organizacionSlug } = useParams<{ organizacionSlug?: string }>();
    const [organizacionNombre, setOrganizacionNombre] = useState<string>('');

    useEffect(() => {
        // Obtener información de la organización
        if (organizacionSlug) {
            api.get(`/api/organizacion/organizaciones/${organizacionSlug}/`)
                .then(res => setOrganizacionNombre(res.data.nombre))
                .catch(() => setError('Organización no encontrada'));
        }
    }, [organizacionSlug]);

    const handleSubmit = async (e: React.FormEvent) => {
        if (organizacionSlug) {
            // Registro con organización
            const response = await api.post(
                `/api/register/${organizacionSlug}/`,
                userData
            );

            // Guardar tokens y login automático
            localStorage.setItem('access_token', response.data.tokens.access);
            localStorage.setItem('refresh_token', response.data.tokens.refresh);
            navigate('/');
        } else {
            // Registro genérico (sin organización)
            await register(userData);
            navigate('/login');
        }
    };

    return (
        <Card.Title>
            {t('register')}
            {organizacionNombre && (
                <div className="text-muted">{organizacionNombre}</div>
            )}
        </Card.Title>
    );
};
```

---

## 📋 Archivos Modificados

### Backend
- ✅ `/backend/usuarios/views.py` - Añadida `RegisterByOrganizacionView`
- ✅ `/backend/usuarios/urls.py` - Añadida ruta `register/<slug>/`
- ✅ `/backend/organizacion/views.py` - Añadida `OrganizacionPublicView`
- ✅ `/backend/organizacion/urls.py` - Añadida ruta pública

### Frontend
- ✅ `/frontend/src/App.tsx` - Añadida ruta `/register/:organizacionSlug`
- ✅ `/frontend/src/pages/RegisterPage.tsx` - Soporte para slug y validación

### Documentación
- ✅ `/REGISTRO_POR_ORGANIZACION.md` - Guía completa de uso
- ✅ `/MANUAL_DE_USO.md` - Actualizado con nueva funcionalidad
- ✅ `/RESUMEN_IMPLEMENTACION_REGISTRO.md` - Este archivo

---

## 🔗 URLs de Ejemplo

### Desarrollo
```
# Registro genérico (sin organización)
http://localhost:3001/register

# Registro por organización
http://localhost:3001/register/clinica-abc
http://localhost:3001/register/salon-bella
http://localhost:3001/register/taller-express
```

### Producción
```
# Registro genérico (sin organización)
http://16.52.17.116/register

# Registro por organización
http://16.52.17.116/register/clinica-abc
http://16.52.17.116/register/salon-bella
http://16.52.17.116/register/taller-express
```

---

## ✅ Validaciones Implementadas

### Backend
- ✅ Verificar que la organización existe (404 si no existe)
- ✅ Verificar que username no está duplicado
- ✅ Verificar que email no está duplicado
- ✅ Validar campos requeridos
- ✅ Asociar usuario a la organización correcta
- ✅ Generar tokens JWT para login automático

### Frontend
- ✅ Obtener nombre real de la organización desde API
- ✅ Mostrar nombre de la organización en el título
- ✅ Mostrar error si organización no existe
- ✅ Validar consentimiento de datos (GDPR)
- ✅ Guardar tokens y redirigir al dashboard
- ✅ Manejo de errores específicos

---

## 🎨 Experiencia de Usuario

### Flujo Completo

1. **Usuario recibe link de la organización:**
   ```
   http://16.52.17.116/register/clinica-abc
   ```

2. **Accede al link:**
   - Ve el formulario de registro
   - El título muestra: "Registro - CLÍNICA ABC"
   - Sabe exactamente a qué organización se está registrando

3. **Completa el formulario:**
   - Username
   - Password
   - Email
   - Nombre y Apellido
   - Acepta términos

4. **Envía el formulario:**
   - Backend valida datos
   - Crea usuario
   - Asocia a "Clínica ABC"
   - Genera tokens JWT

5. **Login automático:**
   - Tokens se guardan en localStorage
   - Usuario es redirigido al dashboard
   - Ya puede usar el sistema

---

## 🔐 Seguridad

### Permisos
- ✅ Endpoint público (`AllowAny`) - cualquiera puede registrarse
- ✅ Validación multi-tenant estricta
- ✅ Solo se asocia a la organización del slug
- ✅ No se puede cambiar organización después del registro

### Tokens JWT
- ✅ Access token de corta duración
- ✅ Refresh token para renovar sesión
- ✅ Login automático después del registro

### Validaciones
- ✅ Username único en todo el sistema
- ✅ Email único en todo el sistema
- ✅ Organización debe existir antes de crear usuario
- ✅ Mensajes de error genéricos (no revelan info sensible)

---

## 📊 Comparación con Magic Link

| Aspecto | Registro por Slug | Magic Link |
|---------|-------------------|------------|
| **Propósito** | Auto-registro de nuevos usuarios | Acceso sin contraseña para usuarios existentes |
| **¿Requiere usuario existente?** | ❌ No | ✅ Sí |
| **¿Asigna organización?** | ✅ Automático | ✅ Ya la tiene |
| **¿Requiere contraseña?** | ✅ Sí | ❌ No |
| **¿Quién lo usa?** | Usuarios nuevos | Usuarios existentes, invitados |
| **Flujo** | Link → Formulario → Registro | Link → Login directo |
| **Validez** | Permanente | 15 minutos |

### Casos de Uso Combinados

**Registro por Slug:**
- Cliente nuevo quiere registrarse
- Tiene el link de la organización
- Completa sus datos
- Se registra y accede

**Magic Link:**
- Cliente ya registrado
- Olvidó contraseña o quiere acceso rápido
- Admin le envía magic link
- Accede sin contraseña

**Ambos se complementan:**
1. Nuevos usuarios → Registro por slug
2. Usuarios existentes → Magic link para acceso rápido
3. Invitaciones de admin → Crear cuenta + magic link

---

## 🚀 Próximos Pasos (Mejoras Futuras)

### 1. QR Code Generator
```typescript
// Generar QR por organización
const qrData = `http://16.52.17.116/register/${organizacion.slug}`;
<QRCode value={qrData} />
```

### 2. Landing Page por Organización
```
http://16.52.17.116/clinica-abc
  ├── /           → Landing page
  ├── /register   → Registro
  ├── /agendar    → Reserva pública
  └── /servicios  → Servicios públicos
```

### 3. Branding Personalizado
```json
{
  "logo_url": "https://...",
  "primary_color": "#0066cc",
  "welcome_message": "Bienvenido a Clínica ABC",
  "terms_url": "https://..."
}
```

### 4. Pre-llenado de Datos
```
http://16.52.17.116/register/clinica-abc?email=juan@example.com&nombre=Juan
```

### 5. Analytics
- Rastrear origen de registros
- Conversión por canal
- Usuarios por organización

---

## 📝 Notas Técnicas

### Slug de Organización
- Se genera automáticamente al crear organización (basado en nombre)
- Formato: `kebab-case` (todo minúsculas, separado por guiones)
- Debe ser único (validado en DB con índice único)
- Es editable manualmente en Django Admin si es necesario
- Case-insensitive en la URL

### Compatibilidad
- ✅ Compatible con registro genérico (`/register`)
- ✅ Compatible con Magic Link existente
- ✅ No rompe funcionalidad anterior
- ✅ Backward compatible

### Performance
- ✅ Validación de organización en frontend (reduce errores)
- ✅ Login automático (mejor UX)
- ✅ Índice en campo `slug` (búsquedas rápidas)

---

## 🧪 Testing

### Pruebas Realizadas

**Backend:**
```bash
# 1. Registro exitoso con organización
curl -X POST http://localhost:8000/api/register/clinica-abc/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"pass123","first_name":"Test","last_name":"User","has_consented_data_processing":true}'

# 2. Error: organización no existe
curl -X POST http://localhost:8000/api/register/no-existe/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"pass123"}'

# 3. Error: username duplicado
# (Repetir request 1)

# 4. Obtener info pública de organización
curl http://localhost:8000/api/organizacion/organizaciones/clinica-abc/
```

**Frontend:**
```bash
# 1. Acceder a registro por organización
http://localhost:3001/register/clinica-abc

# 2. Acceder a organización que no existe
http://localhost:3001/register/no-existe

# 3. Completar formulario y enviar

# 4. Verificar login automático y redirección
```

### Casos de Prueba

| Caso | Entrada | Resultado Esperado |
|------|---------|-------------------|
| Registro válido | Slug válido + datos correctos | ✅ Usuario creado, login automático |
| Organización no existe | Slug inválido | ❌ Error 404: Organización no encontrada |
| Username duplicado | Username existente | ❌ Error 400: Username ya existe |
| Email duplicado | Email existente | ❌ Error 400: Email ya registrado |
| Sin consentimiento | No marca checkbox | ❌ Error: Debe aceptar términos |
| Registro genérico | URL sin slug | ✅ Registro sin organización |

---

## ✅ Checklist de Implementación

- [x] Backend: Vista de registro por organización
- [x] Backend: Endpoint público de organización
- [x] Backend: URLs configuradas
- [x] Backend: Validaciones implementadas
- [x] Frontend: Ruta con parámetro slug
- [x] Frontend: Componente actualizado
- [x] Frontend: Obtención de nombre de organización
- [x] Frontend: Login automático después del registro
- [x] Frontend: Manejo de errores
- [x] Documentación: Guía de uso
- [x] Documentación: Manual actualizado
- [x] Documentación: Resumen de implementación

---

## 📞 Contacto y Soporte

Para consultas o problemas:
- Ver documentación completa: [REGISTRO_POR_ORGANIZACION.md](REGISTRO_POR_ORGANIZACION.md)
- Manual de usuario: [MANUAL_DE_USO.md](MANUAL_DE_USO.md)
- Roles y permisos: [ROLES_Y_PERMISOS.md](ROLES_Y_PERMISOS.md)

---

**Estado:** ✅ Implementado y Probado
**Versión:** 1.0
**Fecha:** Octubre 2025
