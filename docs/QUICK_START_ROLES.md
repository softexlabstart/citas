# 🚀 Quick Start - Sistema de Roles Multi-Tenant

## Guía Rápida de Uso

---

## 📍 Acceso Rápido

### Para Crear Usuarios con Roles:

1. **Login como Admin/Owner**
2. **Menú lateral** → "Gestión de Usuarios"
3. O ir directo a: `http://tu-dominio/users`

---

## 🎯 Crear tu Primer Usuario

### Ejemplo 1: Colaborador Simple

```
1. Click "Crear Usuario"
2. Datos:
   - Email: ana@ejemplo.com
   - Nombre: Ana
   - Apellido: García
   - Contraseña: (mínimo 8 caracteres)
3. Rol Principal: Click en "🟢 Colaborador"
4. Sede Principal: Selecciona sede del dropdown
5. Click "Crear Usuario"
```

**Resultado**: Ana puede atender citas en su sede

---

### Ejemplo 2: Colaborador que también es Cliente

```
1. Click "Crear Usuario"
2. Datos básicos...
3. Rol Principal: "🟢 Colaborador"
4. Roles Adicionales: ✓ Marca "Cliente"
5. Sede Principal: Selecciona sede
6. Click "Crear Usuario"
```

**Resultado**: Ana puede atender citas Y también agendar citas para ella

---

### Ejemplo 3: Administrador de Sede

```
1. Click "Crear Usuario"
2. Datos básicos...
3. Rol Principal: "🟠 Admin de Sede"
4. Sede Principal: Selecciona una
5. Sedes Administradas: Selecciona 1 o más sedes (REQUERIDO)
6. Click "Crear Usuario"
```

**Resultado**: Usuario con permisos de admin solo en las sedes asignadas

---

### Ejemplo 4: Colaborador Multi-Sede

```
1. Click "Crear Usuario"
2. Datos básicos...
3. Rol Principal: "🟢 Colaborador"
4. Sede Principal: Sede Centro
5. Sedes de Trabajo: Selecciona "Sede Centro" y "Sede Norte"
6. Click "Crear Usuario"
```

**Resultado**: Colaborador que trabaja en 2 sedes diferentes

---

## 🏢 Múltiples Organizaciones (SaaS)

### Si un usuario trabaja en 2+ organizaciones:

```
1. Usuario hace login
2. Ve selector de organización en navbar (icono de edificio)
3. Click en el selector
4. Aparece lista de organizaciones con su rol en cada una
5. Selecciona la organización deseada
6. La app recarga con el contexto de esa organización
```

---

## 🎨 Ver Roles en el Sistema

### En el Navbar:
- **Badge de Rol**: Aparece junto al nombre de usuario
- **Selector de Org**: Solo si tienes 2+ organizaciones

### En el Menú Lateral:
- **Gestión de Usuarios**: Solo para Owners y Admins
- **Clientes**: Para Sede Admins y superiores
- **Reportes**: Para Sede Admins y superiores
- **Marketing**: Para Sede Admins y superiores

---

## 🔑 Roles Disponibles

| Rol | Emoji | Acceso | Uso Típico |
|-----|-------|--------|------------|
| **Propietario** | 👑 | TODO | Dueño del negocio |
| **Administrador** | 🔴 | TODO | Co-administrador |
| **Admin de Sede** | 🟠 | Sedes específicas | Gerente de sucursal |
| **Colaborador** | 🟢 | Su(s) sede(s) + citas | Empleado/Estilista/Médico |
| **Cliente** | 🔵 | Sus citas | Usuario final |

---

## ⚡ Comandos Útiles

### Desarrollo:
```bash
cd frontend
npm start
```

### Build para Producción:
```bash
cd frontend
npm run build
```

### Verificar Backend:
```bash
cd backend
python manage.py check
```

---

## 🐛 Troubleshooting

### Problema: No veo el menú de "Gestión de Usuarios"
**Solución**: Solo owners y admins pueden ver este menú. Verifica tu rol en Django Admin.

### Problema: El selector de organización no aparece
**Solución**: Solo aparece si tienes 2+ organizaciones. Crea otra organización o agrega tu usuario a otra.

### Problema: Error al crear usuario
**Solución**: Verifica:
1. Email único (no existe ya)
2. Contraseña mínimo 8 caracteres
3. Si es Admin de Sede, selecciona al menos 1 sede administrada

### Problema: Usuario creado pero no puede login
**Solución**:
1. Ve a Django Admin
2. Busca el PerfilUsuario
3. Verifica que `is_active = True`
4. Verifica que tenga una organización asignada

---

## 📖 Documentación Completa

- **Backend**: `/backend/SISTEMA_ROLES.md`
- **Frontend**: `/frontend/FRONTEND_ROLES_IMPLEMENTATION.md`

---

## 🎉 ¡Listo!

Tu sistema de roles multi-tenant está completamente configurado y funcionando.

**Próximo paso**: Crea tus primeros usuarios y prueba el sistema.

---

**Fecha**: 2025-10-19
**Versión**: 1.0.0
