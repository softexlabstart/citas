# Funcionalidad: Colaboradores Pueden Crear Citas a Nombre de Clientes

## Resumen

Los colaboradores ahora pueden crear citas para clientes en el sistema. Esto es útil cuando un cliente llama o llega a la sede y el colaborador necesita agendar una cita en su nombre.

## Cambios Implementados

### Backend

#### 1. Nuevo Permiso: `IsColaboradorOrAdmin`
**Archivo**: `backend/citas/permissions.py`

Permite acceso a:
- **Staff/Superusers**: Acceso completo
- **Administradores de Sede**: Acceso completo a sus sedes
- **Colaboradores**: Pueden crear citas a nombre de clientes
- **Usuarios Regulares**: Solo pueden ver/gestionar sus propias citas

#### 2. Modificación de `CitaViewSet`
**Archivo**: `backend/citas/views.py`

- Cambiado permiso de `IsOwnerOrAdminForCita` a `IsColaboradorOrAdmin`
- Modificado `perform_create()` para aceptar parámetro opcional `user_id`
- Los colaboradores, staff y sede admins pueden especificar `user_id` al crear citas

#### 3. Endpoint de Clientes
**Archivo**: `backend/usuarios/urls.py`

Ya existe endpoint: `/api/clients/`
- Los colaboradores pueden listar y buscar clientes
- Útil para seleccionar el cliente al crear una cita

## Cómo Usar (API)

### Crear Cita Como Colaborador

**Endpoint**: `POST /api/citas/citas/`

**Headers**:
```
Authorization: Bearer {token_de_colaborador}
Content-Type: application/json
```

**Body** (crear cita para otro usuario):
```json
{
  "user_id": 5,  // ID del cliente
  "nombre": "Manicura para María",
  "fecha": "2025-10-05T14:30:00Z",
  "servicios_ids": [1, 2],
  "colaboradores_ids": [3],
  "sede_id": 1,
  "estado": "Pendiente"
}
```

**Body** (crear cita para sí mismo):
```json
{
  // No incluir user_id
  "nombre": "Mi propia cita",
  "fecha": "2025-10-05T14:30:00Z",
  "servicios_ids": [1],
  "colaboradores_ids": [3],
  "sede_id": 1,
  "estado": "Pendiente"
}
```

### Buscar Clientes

**Endpoint**: `GET /api/clients/?search={nombre o email}`

**Response**:
```json
[
  {
    "id": 5,
    "username": "maria_lopez",
    "email": "maria@example.com",
    "first_name": "María",
    "last_name": "López",
    "perfil": {
      "telefono": "3001234567"
    }
  }
]
```

## Permisos Detallados

### Crear Citas (POST)

| Tipo de Usuario | user_id NO especificado | user_id especificado |
|-----------------|------------------------|---------------------|
| Usuario Regular | ✅ Cita para sí mismo | ❌ No permitido |
| Colaborador | ✅ Cita para sí mismo | ✅ Cita para cliente |
| Sede Admin | ✅ Cita para sí mismo | ✅ Cita para cliente |
| Staff | ✅ Cita para sí mismo | ✅ Cita para cualquiera |

### Ver Citas (GET)

| Tipo de Usuario | Qué puede ver |
|-----------------|---------------|
| Usuario Regular | Solo sus propias citas |
| Colaborador | Citas donde está asignado + sus propias |
| Sede Admin | Todas las citas de sus sedes |
| Staff | Todas las citas |

### Modificar Citas (PUT/PATCH)

| Tipo de Usuario | Qué puede modificar |
|-----------------|---------------------|
| Usuario Regular | Solo sus propias citas |
| Colaborador | Citas donde está asignado |
| Sede Admin | Citas de sus sedes |
| Staff | Cualquier cita |

## Frontend (Pendiente de Implementar)

Para completar esta funcionalidad, el frontend necesita:

### 1. Vista de Colaborador
- Formulario para crear citas con selector de cliente
- Buscador de clientes (autocomplete)
- Vista de citas asignadas al colaborador

### 2. Componente de Búsqueda de Clientes
```tsx
interface ClientSearchProps {
  onSelectClient: (clientId: number) => void;
}

// Componente que use el endpoint /api/clients/?search=...
```

### 3. Modificación de AppointmentForm
- Agregar campo condicional "Cliente" (solo para colaboradores)
- Si es colaborador: mostrar selector de cliente
- Si es usuario regular: ocultar selector

## Ejemplo de Flujo

1. **Colaborador inicia sesión**
2. **Va a "Crear Cita"**
3. **Busca cliente** por nombre/email
4. **Selecciona cliente** de la lista
5. **Completa formulario** (fecha, servicios, etc.)
6. **Envía cita** con `user_id` del cliente seleccionado
7. **Sistema crea cita** a nombre del cliente
8. **Cliente recibe email** de confirmación

## Testing

### Verificar que Colaborador Puede Crear Cita

```bash
# 1. Obtener token de colaborador
curl -X POST http://16.52.17.116/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "colaborador_usuario", "password": "password"}'

# 2. Listar clientes
curl -X GET http://16.52.17.116/api/clients/ \
  -H "Authorization: Bearer {token}"

# 3. Crear cita para cliente ID 5
curl -X POST http://16.52.17.116/api/citas/citas/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "nombre": "Cita de prueba",
    "fecha": "2025-10-05T14:00:00Z",
    "servicios_ids": [1],
    "colaboradores_ids": [1],
    "sede_id": 1,
    "estado": "Pendiente"
  }'
```

## Notas de Seguridad

- ✅ Solo colaboradores autenticados pueden crear citas para otros
- ✅ Usuario regular NO puede crear citas para otros
- ✅ Colaborador solo puede ver citas donde está asignado
- ✅ Validación de existencia de cliente (user_id)
- ✅ Permisos a nivel de objeto (has_object_permission)

## Próximos Pasos

1. Implementar interfaz frontend para colaboradores
2. Agregar notificaciones cuando colaborador crea cita
3. Dashboard específico para colaboradores con sus citas del día
4. Historial de clientes atendidos por colaborador
5. Métricas de performance de colaboradores

---

**Fecha de implementación**: 2025-10-01
**Versión**: 1.0
