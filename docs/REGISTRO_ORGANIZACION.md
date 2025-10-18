# Registro de Usuarios por Organización

## 📋 Descripción

Se ha implementado un sistema de **registro por slug de organización** que permite a cada organización tener su propia URL de registro personalizada. Esto asegura que los nuevos usuarios se registren automáticamente en la organización correcta.

---

## 🎯 Problema Resuelto

**Antes:**
- Los usuarios se registraban sin organización asignada
- No había forma automática de saber a qué organización pertenecían
- Requería asignación manual por parte del administrador

**Ahora:**
- Cada organización tiene su propia URL de registro
- Los usuarios se asocian automáticamente a la organización correcta
- No requiere intervención manual del administrador

---

## 🔗 URLs de Registro

### Formato de URL

```
http://tu-dominio.com/register/{slug-organizacion}
```

### Ejemplos

| Organización | Slug | URL de Registro |
|--------------|------|-----------------|
| Clínica ABC | `clinica-abc` | `http://16.52.17.116/register/clinica-abc` |
| Salón Bella | `salon-bella` | `http://16.52.17.116/register/salon-bella` |
| Taller Express | `taller-express` | `http://16.52.17.116/register/taller-express` |

---

## 🚀 Cómo Usar

### 1. Obtener el Slug de tu Organización

**Opción A: Desde Django Admin**
1. Accede al panel de administración: `http://tu-dominio.com/admin`
2. Ve a "Organizaciones"
3. Encuentra tu organización
4. Copia el valor del campo **"Slug"**

**Opción B: Desde la API**
```bash
GET /api/organizacion/organizaciones/{slug}/
```

**Ejemplo:**
```bash
curl http://16.52.17.116/api/organizacion/organizaciones/clinica-abc/
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Clínica ABC",
  "slug": "clinica-abc"
}
```

### 2. Compartir el Link de Registro

Comparte el link con tus futuros usuarios:

```
http://16.52.17.116/register/clinica-abc
```

### 3. Proceso de Registro del Usuario

1. **El usuario accede al link personalizado**
   - URL: `http://16.52.17.116/register/clinica-abc`

2. **Se muestra el formulario de registro con el nombre de la organización**
   - Título: "Registro - CLÍNICA ABC"

3. **El usuario completa:**
   - Nombre de usuario
   - Contraseña
   - Email
   - Nombre
   - Apellido
   - Acepta términos y condiciones

4. **Al enviar:**
   - El usuario se crea automáticamente
   - Se asocia a la organización "Clínica ABC"
   - Recibe tokens JWT (login automático)
   - Es redirigido al dashboard

---

## 🛠️ Implementación Técnica

### Backend

**Endpoint de Registro:**
```
POST /api/register/{organizacion_slug}/
```

**Request Body:**
```json
{
  "username": "juan.perez",
  "password": "contraseña123",
  "email": "juan@example.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "has_consented_data_processing": true
}
```

**Response (Éxito):**
```json
{
  "message": "Registro exitoso en Clínica ABC",
  "user": {
    "id": 15,
    "username": "juan.perez",
    "email": "juan@example.com",
    "first_name": "Juan",
    "last_name": "Pérez"
  },
  "organizacion": {
    "id": 1,
    "nombre": "Clínica ABC",
    "slug": "clinica-abc"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Response (Error - Organización no existe):**
```json
{
  "error": "Organización no encontrada. Verifica el enlace de registro."
}
```

**Response (Error - Username duplicado):**
```json
{
  "error": "El nombre de usuario ya existe"
}
```

### Frontend

**Rutas:**
```typescript
// App.tsx
<Route path="/register" element={<RegisterPage />} />
<Route path="/register/:organizacionSlug" element={<RegisterPage />} />
```

**Componente RegisterPage:**
```typescript
const { organizacionSlug } = useParams<{ organizacionSlug?: string }>();

useEffect(() => {
  if (organizacionSlug) {
    // Obtener nombre de la organización
    api.get(`/api/organizacion/organizaciones/${organizacionSlug}/`)
      .then(res => setOrganizacionNombre(res.data.nombre));
  }
}, [organizacionSlug]);

const handleSubmit = async (e) => {
  if (organizacionSlug) {
    // Registro con organización
    const response = await api.post(`/api/register/${organizacionSlug}/`, userData);
    // Guardar tokens y redirigir
    localStorage.setItem('access_token', response.data.tokens.access);
    navigate('/');
  } else {
    // Registro genérico (sin organización)
    await register(userData);
    navigate('/login');
  }
};
```

---

## 📊 Validaciones

### Backend

✅ **Validaciones implementadas:**
- El slug de organización existe
- Username no duplicado
- Email no duplicado
- Campos requeridos (username, email, password)
- Organización válida antes de crear usuario

❌ **Si falla alguna validación:**
- No se crea el usuario
- Se devuelve error específico
- Frontend muestra mensaje de error

### Frontend

✅ **Validaciones implementadas:**
- Verificación de organización al cargar (useEffect)
- Mostrar error si organización no existe
- Mostrar nombre real de la organización
- Validación de consentimiento de datos
- Campos requeridos del formulario

---

## 🔐 Seguridad

### Permisos
- **Endpoint público:** `AllowAny` - cualquiera puede registrarse
- **Validación multi-tenant:** El usuario se asocia solo a la organización del slug
- **Tokens JWT:** Login automático después del registro

### Mejores Prácticas
1. ✅ Slug único por organización (índice en DB)
2. ✅ Validación de organización antes de crear usuario
3. ✅ Mensajes de error genéricos para no revelar info sensible
4. ✅ Login automático con JWT después del registro
5. ✅ HTTPS obligatorio en producción

---

## 🎨 Personalización (Futuras Mejoras)

### Branding por Organización

```typescript
// Obtener configuración visual de la organización
const response = await api.get(`/api/organizacion/organizaciones/${slug}/`);

// Aplicar:
- Logo de la organización
- Colores personalizados
- Mensaje de bienvenida
- Términos y condiciones específicos
```

### Ejemplo de configuración:
```json
{
  "id": 1,
  "nombre": "Clínica ABC",
  "slug": "clinica-abc",
  "logo_url": "https://...",
  "primary_color": "#0066cc",
  "welcome_message": "Bienvenido a Clínica ABC"
}
```

---

## 📋 Checklist de Uso

### Para Administradores de Organización

- [ ] Acceder al admin de Django
- [ ] Ir a "Organizaciones"
- [ ] Copiar el **slug** de tu organización
- [ ] Construir URL: `http://tu-dominio.com/register/{slug}`
- [ ] Compartir link con nuevos usuarios
- [ ] Probar el registro con un usuario de prueba

### Para Usuarios Finales

- [ ] Recibir link de registro de la organización
- [ ] Acceder al link (ej: `http://16.52.17.116/register/clinica-abc`)
- [ ] Verificar que aparece el nombre de la organización
- [ ] Completar formulario de registro
- [ ] Aceptar términos y condiciones
- [ ] Hacer clic en "Registrar"
- [ ] Automáticamente estarás logueado

---

## 🐛 Troubleshooting

### Problema: "Organización no encontrada"

**Causa:** El slug no existe en la base de datos

**Solución:**
1. Verificar que la organización existe en Django Admin
2. Verificar que el slug es correcto (case-sensitive)
3. Comprobar URL: `/api/organizacion/organizaciones/{slug}/`

### Problema: "El usuario ya existe"

**Causa:** El username ya está registrado

**Solución:**
1. Elegir un username diferente
2. Si el usuario ya existe, usar `/login` en vez de `/register`

### Problema: No se asigna la organización

**Causa:** Se está usando la URL genérica `/register` sin slug

**Solución:**
1. Usar siempre la URL con slug: `/register/{slug}`
2. Compartir el link completo con el slug

### Problema: Error 500 al registrar

**Causa:** Error en el servidor

**Solución:**
1. Verificar logs del backend
2. Verificar que la base de datos está activa
3. Verificar que el modelo `PerfilUsuario` existe

---

## 🔄 Comparación con Métodos Anteriores

| Método | Ventajas | Desventajas |
|--------|----------|-------------|
| **URL con Slug** (Actual) | ✅ Automático<br>✅ Sin errores<br>✅ Profesional<br>✅ Escalable | Requiere compartir link específico |
| **Selector en Formulario** | ✅ Una sola URL | ❌ Usuario debe elegir<br>❌ Puede confundirse |
| **Solo Magic Link** | ✅ Sin contraseña | ❌ No permite auto-registro<br>❌ Requiere admin |
| **Registro genérico** | ✅ Simple | ❌ No asigna organización<br>❌ Requiere config manual |

---

## 📞 Ejemplos de Uso Real

### Clínica Médica
```
URL: http://16.52.17.116/register/clinica-salud-total

Compartir vía:
- Email a pacientes nuevos
- WhatsApp Business
- Código QR en recepción
- Redes sociales
```

### Salón de Belleza
```
URL: http://16.52.17.116/register/salon-bella-express

Compartir vía:
- Instagram bio link
- Tarjetas de presentación
- Página web del salón
- Google My Business
```

### Taller Mecánico
```
URL: http://16.52.17.116/register/taller-automotriz-garcia

Compartir vía:
- Factura impresa (código QR)
- Google Maps
- Email de seguimiento
- SMS a clientes
```

---

## 🚀 Siguientes Pasos

### Mejoras Pendientes

1. **QR Code Generator**
   - Generar QR automático por organización
   - Descargar como imagen
   - Imprimir para punto físico

2. **Landing Page por Organización**
   - `/{slug}` → Landing page pública
   - `/{slug}/register` → Registro
   - `/{slug}/agendar` → Reserva

3. **Branding Personalizado**
   - Logo de organización
   - Colores custom
   - Mensaje de bienvenida

4. **Analytics**
   - Rastrear origen de registros
   - Conversión por canal
   - Usuarios por organización

---

## 📝 Notas Adicionales

- El slug se genera automáticamente al crear una organización (basado en el nombre)
- Puedes editar el slug manualmente en Django Admin si es necesario
- El slug debe ser único (validado por la base de datos)
- El slug es case-insensitive en la URL
- Formato recomendado: `kebab-case` (todo minúsculas, separado por guiones)

---

**Versión:** 1.0
**Fecha:** Octubre 2025
**Autor:** Sistema de Gestión de Citas
