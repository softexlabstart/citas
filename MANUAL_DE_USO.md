# Manual de Uso Funcional - Sistema de Gestión de Citas

## Índice
1. [Introducción](#introducción)
2. [Roles de Usuario](#roles-de-usuario)
3. [Acceso al Sistema](#acceso-al-sistema)
4. [Panel de Usuario Cliente](#panel-de-usuario-cliente)
5. [Panel de Colaborador](#panel-de-colaborador)
6. [Panel de Administrador de Sede](#panel-de-administrador-de-sede)
7. [Panel de Superusuario](#panel-de-superusuario)
8. [Gestión de Citas](#gestión-de-citas)
9. [Generación de Informes](#generación-de-informes)
10. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El Sistema de Gestión de Citas es una plataforma multi-tenant (multi-organización) que permite a diferentes tipos de negocios gestionar sus citas, servicios, colaboradores y clientes de manera eficiente.

### Características Principales
- ✅ Sistema multi-organizacional (cada organización tiene sus propios datos aislados)
- ✅ Gestión de múltiples sedes por organización
- ✅ Roles diferenciados con permisos específicos
- ✅ Agendamiento de citas con confirmación
- ✅ Gestión de disponibilidad de colaboradores
- ✅ Bloqueo de horarios para eventos especiales
- ✅ Generación de informes y reportes
- ✅ Notificaciones por correo electrónico
- ✅ Reservas anónimas (sin necesidad de registrarse)
- ✅ Interfaz en español con internacionalización

---

## Roles de Usuario

El sistema define **4 roles principales** con permisos diferenciados:

### 1. 👤 Cliente
**¿Quién es?** Usuario final que agenda citas para recibir servicios.

**¿Qué puede hacer?**
- ✅ Registrarse e iniciar sesión
- ✅ Ver servicios disponibles
- ✅ Agendar citas para sí mismo
- ✅ Ver su historial de citas
- ✅ Reprogramar sus citas
- ✅ Cancelar sus citas
- ❌ NO puede ver citas de otros usuarios
- ❌ NO puede acceder al panel de administración

**Casos de uso:**
- Paciente que agenda cita médica
- Cliente de salón de belleza
- Usuario que reserva servicios en general

---

### 2. 👨‍💼 Colaborador
**¿Quién es?** Profesional que ofrece servicios (médico, estilista, mecánico, etc.)

**¿Qué puede hacer?**
- ✅ Ver todas las citas asignadas a él
- ✅ Crear citas a nombre de clientes de su organización
- ✅ Marcar asistencia de clientes (Asistió / No Asistió)
- ✅ Ver clientes de su organización
- ✅ Ver servicios de su organización
- ✅ Ver otros colaboradores de su organización (para coordinación)
- ❌ NO puede ver citas de otros colaboradores
- ❌ NO puede gestionar configuraciones
- ❌ NO puede acceder al panel de administración de Django

**Restricciones multi-tenant:**
- Solo puede crear citas para clientes de su organización
- Solo puede crear citas para su sede asignada
- Solo ve datos de su organización

---

### 3. 🏢 Administrador de Sede
**¿Quién es?** Gerente o supervisor de una o más sucursales.

**¿Qué puede hacer?**
- ✅ Acceso al panel de administración del frontend
- ✅ Ver y gestionar **todas las citas** de sus sedes
- ✅ Crear, editar y eliminar servicios de sus sedes
- ✅ Gestionar colaboradores de sus sedes
- ✅ Ver todos los clientes de su organización
- ✅ Crear bloqueos de horarios
- ✅ Generar informes de sus sedes
- ✅ Acceder a módulo de marketing
- ❌ NO puede ver datos de otras organizaciones
- ❌ NO puede acceder al panel de administración de Django

**Restricciones multi-tenant:**
- Solo ve datos de la organización a la que pertenece
- Solo puede administrar las sedes asignadas explícitamente

---

### 4. 👑 Superusuario (Super Admin)
**¿Quién es?** Administrador del sistema completo.

**¿Qué puede hacer?**
- ✅ Acceso total al panel de administración de Django
- ✅ Acceso total al frontend
- ✅ Ver y gestionar datos de **TODAS** las organizaciones
- ✅ Crear, editar y eliminar cualquier recurso
- ✅ Sin restricciones multi-tenant
- ✅ Gestionar organizaciones y sedes

**Casos de uso:**
- Soporte técnico de nivel superior
- Administrador del sistema
- Gestión de múltiples organizaciones

---

## Acceso al Sistema

### Registro de Nuevo Usuario

1. **Accede a la aplicación:** `http://localhost:3001` (o la URL de producción)
2. **Haz clic en "Registrarse"**
3. **Completa el formulario:**
   - Nombre de usuario
   - Correo electrónico
   - Contraseña
   - Confirmación de contraseña
   - Datos opcionales: teléfono, ciudad, barrio, género, fecha de nacimiento
4. **Acepta el procesamiento de datos** (GDPR)
5. **Haz clic en "Registrarse"**

### Inicio de Sesión

1. **Accede a la aplicación**
2. **Haz clic en "Iniciar Sesión"**
3. **Ingresa tus credenciales:**
   - Nombre de usuario
   - Contraseña
4. **Haz clic en "Ingresar"**

### Magic Link (Enlace Mágico)

El sistema soporta autenticación sin contraseña mediante enlaces mágicos:

1. El administrador puede generar un enlace de acceso temporal
2. El enlace es válido por **15 minutos**
3. Al hacer clic en el enlace, el usuario accede sin contraseña
4. Ideal para invitados o acceso rápido

---

## Panel de Usuario Cliente

### Dashboard

Al iniciar sesión como cliente, verás:

- **Próxima Cita:** Información de tu próxima cita programada
- **Acceso rápido a:**
  - Agendar nueva cita
  - Ver historial de citas

### Agendar Nueva Cita

#### Opción 1: Con Usuario Registrado

1. **Navega a "Nueva Cita"**
2. **Selecciona la sede** donde deseas recibir el servicio
3. **Selecciona el servicio o servicios** que deseas
4. **Selecciona el colaborador** (opcional - el sistema puede asignar automáticamente)
5. **Consulta disponibilidad:**
   - El sistema muestra los horarios disponibles
   - Puedes buscar la "Próxima Cita Disponible" automáticamente
6. **Selecciona fecha y hora**
7. **Agrega un comentario** (opcional)
8. **Confirma la cita**
9. **Recibirás un correo de confirmación**

#### Opción 2: Reserva Anónima (Sin Registro)

1. **Accede a la página de reserva pública** (con slug de organización)
2. **Completa los datos:**
   - Nombre
   - Email
   - Teléfono
   - Sede
   - Servicio(s)
   - Colaborador
   - Fecha y hora
3. **Confirma la reserva**
4. **Recibirás un correo de confirmación** al email proporcionado

### Ver Mis Citas

1. **Navega a "Mis Citas"**
2. **Visualización disponible:**
   - **Vista de Tabla:** Lista filtrable de citas
   - **Vista de Calendario:** Calendario interactivo
3. **Filtros disponibles:**
   - Por estado: Pendiente, Confirmada, Cancelada, Asistió, No Asistió
   - Por búsqueda de nombre

### Reprogramar una Cita

1. **Ve a "Mis Citas"**
2. **Selecciona la cita** que deseas reprogramar
3. **Haz clic en "Editar" o "Reprogramar"**
4. **Selecciona nueva fecha y hora**
5. **Guarda los cambios**
6. **Recibirás un correo de notificación** de reprogramación

⚠️ **Importante:** No puedes modificar citas con estado "Cancelada"

### Cancelar una Cita

1. **Ve a "Mis Citas"**
2. **Selecciona la cita** que deseas cancelar
3. **Haz clic en "Cancelar Cita"**
4. **Confirma la cancelación**
5. El estado de la cita cambia a **"Cancelada"**
6. **Recibirás un correo de confirmación** de cancelación

⚠️ **Importante:** Las citas canceladas no se eliminan, solo cambian de estado

---

## Panel de Colaborador

### Dashboard

Al iniciar sesión como colaborador, verás:

- **Citas de Hoy:** Cantidad de citas programadas para hoy
- **Próximas Citas:** Lista de tus próximas 5 citas

### Ver Mis Citas Asignadas

1. **Navega a "Mis Citas"** o **"Citas Asignadas"**
2. **Visualización:**
   - Solo verás citas donde estás asignado como colaborador
   - Vista de tabla y calendario disponibles
3. **Filtros:**
   - Por estado
   - Por rango de fechas

### Crear Cita a Nombre de un Cliente

Como colaborador, puedes agendar citas para clientes de tu organización:

1. **Navega a "Nueva Cita"**
2. **Selecciona el cliente** (solo verás clientes de tu organización)
   - Si el cliente no existe, deberás solicitarle que se registre primero
3. **Selecciona servicios**
4. **Selecciona tu sede** (solo tu sede asignada)
5. **Selecciona fecha y hora disponible**
6. **Crea la cita**

⚠️ **Restricciones:**
- Solo puedes crear citas para **tu sede**
- Solo puedes crear citas para **clientes de tu organización**
- El sistema validará estas restricciones automáticamente

### Marcar Asistencia

1. **Ve a la cita correspondiente**
2. **Haz clic en "Marcar Asistencia"**
3. **Selecciona:**
   - ✅ **Asistió:** Cliente se presentó a la cita
   - ❌ **No Asistió:** Cliente no se presentó
4. **Agrega un comentario** (opcional)
5. **Guarda**

El estado de la cita cambia automáticamente a "Asistió" o "No Asistió"

### Ver Clientes

1. **Navega a "Clientes"**
2. **Verás todos los clientes de tu organización**
3. **Puedes:**
   - Buscar por nombre, email o teléfono
   - Ver historial de citas del cliente
   - Crear nueva cita para el cliente

---

## Panel de Administrador de Sede

### Dashboard

Al iniciar sesión como administrador de sede, verás:

- **Citas de Hoy:** Total de citas en tus sedes hoy
- **Pendientes de Confirmación:** Citas que requieren confirmación
- **Ingresos del Mes:** Total de ingresos generados este mes (solo citas con estado "Asistió")
- **Próximas Citas:** Lista de próximas 5 citas

### Gestión de Citas

#### Ver Todas las Citas

1. **Navega a "Citas"**
2. **Visualización:**
   - Todas las citas de **todas tus sedes administradas**
   - Vista de tabla y calendario
3. **Filtros:**
   - Por estado
   - Por sede
   - Por colaborador
   - Por servicio
   - Por rango de fechas
   - Búsqueda por nombre de cliente

#### Confirmar Citas Pendientes

1. **Ve a "Citas Pendientes"** o filtra por estado "Pendiente"
2. **Selecciona la cita**
3. **Haz clic en "Confirmar"**
4. El estado cambia a **"Confirmada"**
5. Se envía un correo de confirmación al cliente

### Gestión de Servicios

#### Crear Nuevo Servicio

1. **Navega a "Servicios"**
2. **Haz clic en "Nuevo Servicio"**
3. **Completa:**
   - Nombre del servicio
   - Descripción
   - Duración estimada (en minutos)
   - Precio
   - Sede asociada
   - Metadata adicional (opcional - formato JSON)
4. **Guarda**

#### Editar Servicio

1. **Ve a "Servicios"**
2. **Selecciona el servicio**
3. **Haz clic en "Editar"**
4. **Modifica los campos necesarios**
5. **Guarda**

#### Eliminar Servicio

1. **Ve a "Servicios"**
2. **Selecciona el servicio**
3. **Haz clic en "Eliminar"**
4. **Confirma la eliminación**

⚠️ **Importante:** Solo puedes gestionar servicios de tus sedes administradas

### Gestión de Colaboradores

#### Crear Nuevo Colaborador

1. **Navega a "Colaboradores"**
2. **Haz clic en "Nuevo Colaborador"**
3. **Completa:**
   - Nombre
   - Email
   - Usuario del sistema (opcional - si el colaborador también es usuario)
   - Sede
   - Servicios que ofrece
   - Descripción
   - Metadata adicional (opcional)
4. **Guarda**

#### Asignar Horarios a Colaborador

1. **Ve a "Colaboradores"**
2. **Selecciona el colaborador**
3. **Ve a "Horarios"**
4. **Agrega horarios:**
   - Día de la semana
   - Hora de inicio
   - Hora de fin
5. **Guarda**

Ejemplo:
- Lunes: 09:00 - 13:00
- Lunes: 14:00 - 18:00
- Martes: 09:00 - 13:00

#### Crear Bloqueos de Horarios

Para eventos especiales, almuerzos, reuniones, etc:

1. **Navega a "Bloqueos"**
2. **Haz clic en "Nuevo Bloqueo"**
3. **Completa:**
   - Colaborador
   - Motivo (ej: "Almuerzo", "Reunión", "Cita personal")
   - Fecha y hora de inicio
   - Fecha y hora de fin
4. **Guarda**

Durante el bloqueo, el colaborador **NO** aparecerá como disponible para citas.

### Gestión de Clientes

1. **Navega a "Clientes"**
2. **Verás todos los clientes de tu organización**
3. **Funcionalidades:**
   - Ver historial completo de citas
   - Ver datos de contacto
   - Crear nueva cita para el cliente
   - Filtrar por sede

### Módulo de Marketing

1. **Navega a "Marketing"**
2. **Funcionalidades disponibles:**
   - Campañas de email
   - Análisis de clientes
   - Segmentación

*(Consulta documentación específica de marketing para más detalles)*

---

## Panel de Superusuario

### Acceso al Panel de Administración de Django

1. **Accede a:** `http://localhost:8000/admin` (o URL de producción)
2. **Inicia sesión** con credenciales de superusuario
3. **Panel completo de Django disponible**

### Gestión de Organizaciones

#### Crear Nueva Organización

**Opción 1: Desde Django Admin**

1. **Ve a "Organizaciones"**
2. **Haz clic en "Agregar Organización"**
3. **Completa:**
   - Nombre
   - Slug (identificador único URL-friendly)
   - Configuraciones adicionales
4. **Guarda**

**Opción 2: Desde API (para superadmin)**

```bash
POST /api/organizacion/crear/
{
  "nombre": "Mi Clínica",
  "slug": "mi-clinica"
}
```

### Gestión de Sedes

#### Crear Nueva Sede

1. **Ve a "Sedes" en Django Admin**
2. **Haz clic en "Agregar Sede"**
3. **Completa:**
   - Nombre
   - Dirección
   - Teléfono
   - Email
   - Organización (selecciona la organización dueña)
4. **Guarda**

### Asignar Roles a Usuarios

#### Asignar Administrador de Sede

1. **Ve a "Perfiles de Usuario"**
2. **Selecciona el usuario**
3. **En "Sedes Administradas":**
   - Selecciona una o más sedes
4. **En "Organización":**
   - Asigna la organización correspondiente
5. **Guarda**

#### Asignar Colaborador

1. **Ve a "Colaboradores"**
2. **Crea nuevo colaborador** o **edita existente**
3. **En "Usuario":**
   - Vincula el usuario del sistema
4. **Completa datos:**
   - Nombre
   - Email
   - Sede
   - Servicios
5. **Guarda**

### Ver Datos de Todas las Organizaciones

Como superusuario, tienes acceso completo a todos los datos sin restricciones multi-tenant:

- **Todas las citas** de todas las organizaciones
- **Todos los servicios** de todas las organizaciones
- **Todos los colaboradores** de todas las organizaciones
- **Todos los clientes** de todas las organizaciones

---

## Gestión de Citas

### Estados de una Cita

| Estado | Descripción | ¿Cuándo se usa? |
|--------|-------------|-----------------|
| **Pendiente** | Cita creada pero no confirmada | Estado inicial al crear |
| **Confirmada** | Cita confirmada por el cliente o admin | Después de confirmar |
| **Cancelada** | Cita cancelada | Cuando se cancela |
| **Asistió** | Cliente se presentó a la cita | Marcado por colaborador |
| **No Asistió** | Cliente no se presentó | Marcado por colaborador |

### Ciclo de Vida de una Cita

```
[CREACIÓN] → Pendiente
    ↓
[CONFIRMACIÓN] → Confirmada
    ↓
[DÍA DE LA CITA]
    ↓
[COLABORADOR MARCA ASISTENCIA]
    ↓
Asistió o No Asistió

*En cualquier momento puede → Cancelada
```

### Consulta de Disponibilidad

#### Buscar Horarios Disponibles

**Endpoint API:**
```
GET /api/citas/disponibilidad/
?fecha=2025-01-15
&recurso_id=5
&sede_id=1
&servicio_ids=3,7
```

**Respuesta:**
```json
{
  "disponibilidad": [
    "09:00",
    "09:30",
    "10:00",
    "11:00"
  ]
}
```

#### Buscar Próxima Cita Disponible

**Endpoint API:**
```
GET /api/citas/next-availability/
?servicio_ids=3,7
&sede_id=1
```

**Respuesta:**
```json
{
  "next_slots": [
    {
      "colaborador_id": 5,
      "colaborador_nombre": "Dr. Juan Pérez",
      "fecha": "2025-01-15",
      "hora": "10:00"
    }
  ]
}
```

### Validaciones de Sistema

#### Al Crear una Cita

El sistema valida automáticamente:

✅ **Disponibilidad del colaborador:**
- Verifica que el colaborador tenga horario configurado para ese día
- Verifica que no tenga otra cita en ese horario
- Verifica que no tenga bloqueos activos

✅ **Duración de servicios:**
- Calcula la duración total de todos los servicios
- Verifica que haya tiempo suficiente

✅ **Permisos multi-tenant:**
- Colaboradores solo pueden crear citas para su sede y organización
- Admins solo para sus sedes administradas

❌ **La cita NO se crea si:**
- El horario ya está ocupado
- El colaborador está bloqueado
- El colaborador no tiene horario ese día
- No hay permisos suficientes

### Notificaciones por Email

El sistema envía emails automáticos en los siguientes casos:

📧 **Confirmación de Cita:**
- Al crear una nueva cita

📧 **Reprogramación:**
- Al cambiar la fecha/hora de una cita

📧 **Cancelación:**
- Al cancelar una cita

📧 **Recordatorios:**
- Se pueden enviar recordatorios para las citas del día siguiente
- Ejecutando el comando: `python manage.py send_reminders`

⚠️ **Configuración necesaria:**
Debes configurar las variables de entorno SMTP en el archivo `.env`:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña
EMAIL_USE_TLS=True
```

---

## Generación de Informes

### Informe de Citas

**Acceso:**
- Administradores de Sede y Superusuarios

**Endpoint API:**
```
GET /api/citas/reports/appointments/
?start_date=2025-01-01
&end_date=2025-01-31
&servicio_ids=3,7 (opcional)
&colaborador_id=5 (opcional)
&estado=Confirmada (opcional)
&export=json o csv
```

**Formato JSON (Resumen):**
```json
{
  "report": [
    { "estado": "Pendiente", "count": 15 },
    { "estado": "Confirmada", "count": 45 },
    { "estado": "Cancelada", "count": 5 },
    { "estado": "Asistio", "count": 120 },
    { "estado": "No Asistio", "count": 8 }
  ],
  "total_revenue": 1500000
}
```

**Formato CSV (Detallado):**
Descarga un archivo CSV con todas las citas:
- ID
- Nombre del cliente
- Fecha
- Servicios
- Sede
- Estado
- Confirmado
- Usuario

### Informe por Sede

**Acceso:**
- Administradores de Sede y Superusuarios

**Endpoint API:**
```
GET /api/citas/reports/sede/
?start_date=2025-01-01
&end_date=2025-01-31
&sede_id=2 (opcional)
&servicio_ids=3,7 (opcional)
&colaborador_id=5 (opcional)
&estado=Confirmada (opcional)
```

**Respuesta:**
```json
{
  "reporte_por_sede": [
    {
      "sede_id": 1,
      "sede_nombre": "Sede Centro",
      "total_citas": 193,
      "estados": [
        { "estado": "Pendiente", "count": 15 },
        { "estado": "Confirmada", "count": 45 },
        ...
      ],
      "ingresos": 750000
    }
  ],
  "resumen_servicios": [
    { "servicios__nombre": "Corte de Cabello", "count": 45 },
    { "servicios__nombre": "Manicura", "count": 30 }
  ],
  "resumen_recursos": [
    { "colaboradores__nombre": "María López", "count": 60 },
    { "colaboradores__nombre": "Juan Pérez", "count": 50 }
  ],
  "ingresos_totales": 1500000
}
```

### Exportar Informes

**Desde el Frontend:**

1. **Ve a "Informes"**
2. **Selecciona filtros:**
   - Rango de fechas
   - Sede (opcional)
   - Servicio (opcional)
   - Colaborador (opcional)
   - Estado (opcional)
3. **Selecciona formato:**
   - JSON (resumen estadístico)
   - CSV (detalle completo)
4. **Haz clic en "Generar Informe"**
5. **Descarga el archivo** (si es CSV)

---

## Preguntas Frecuentes

### Generales

**P: ¿Qué es multi-tenant?**
R: El sistema permite que múltiples organizaciones independientes usen la misma plataforma, con sus datos completamente aislados. Cada organización solo ve sus propios datos.

**P: ¿Puedo tener múltiples sedes?**
R: Sí, una organización puede tener múltiples sedes. Los administradores pueden gestionar una o varias sedes.

**P: ¿Los usuarios pueden pertenecer a varias organizaciones?**
R: Sí, el sistema permite que un usuario tenga perfiles en múltiples organizaciones (función experimental).

### Para Clientes

**P: ¿Necesito registrarme para agendar una cita?**
R: No necesariamente. El sistema permite reservas anónimas proporcionando nombre, email y teléfono.

**P: ¿Puedo cambiar la fecha de mi cita?**
R: Sí, puedes reprogramar tus citas siempre que no estén canceladas.

**P: ¿Cómo cancelo una cita?**
R: Ve a "Mis Citas", selecciona la cita y haz clic en "Cancelar". La cita cambia a estado "Cancelada".

**P: ¿Recibiré confirmación por email?**
R: Sí, recibirás emails de confirmación al crear, reprogramar o cancelar citas.

### Para Colaboradores

**P: ¿Puedo ver citas de otros colaboradores?**
R: No, solo ves las citas asignadas a ti.

**P: ¿Puedo crear citas para cualquier cliente?**
R: Solo para clientes de tu organización y en tu sede asignada.

**P: ¿Cómo marco que un cliente asistió?**
R: Accede a la cita y usa la opción "Marcar Asistencia", seleccionando "Asistió" o "No Asistió".

### Para Administradores

**P: ¿Puedo gestionar varias sedes?**
R: Sí, puedes tener múltiples sedes asignadas y verás datos de todas ellas.

**P: ¿Cómo bloqueo un horario?**
R: Ve a "Bloqueos", crea uno nuevo indicando colaborador, motivo, fecha de inicio y fin.

**P: ¿Cómo veo los ingresos generados?**
R: En el Dashboard verás los ingresos del mes actual. También puedes generar informes personalizados por rango de fechas.

**P: ¿Puedo exportar reportes?**
R: Sí, los informes se pueden exportar en formato CSV (detallado) o JSON (resumen).

### Técnicas

**P: ¿Cómo se calcula la disponibilidad?**
R: El sistema verifica:
1. Horarios configurados del colaborador
2. Citas ya agendadas
3. Bloqueos activos
4. Duración de los servicios

**P: ¿Los datos están encriptados?**
R: Las contraseñas se almacenan con hash seguro. La comunicación debe usar HTTPS en producción.

**P: ¿Hay límite de citas?**
R: No hay límite técnico, pero se recomienda paginación para grandes volúmenes.

**P: ¿Se pueden automatizar recordatorios?**
R: Sí, configurando un cron job para ejecutar:
```bash
python manage.py send_reminders
```

---

## Soporte y Contacto

Para soporte técnico o preguntas adicionales:

- **Documentación técnica:** Ver archivos README.md, ROLES_Y_PERMISOS.md, MULTITENANCY_README.md
- **Panel de administración:** Accede al panel de Django para gestión avanzada
- **Logs del sistema:** Revisa `server.log` para diagnóstico de errores

---

## Glosario

**Organización:** Entidad principal multi-tenant (ej: "Clínica ABC")

**Sede:** Sucursal o ubicación física de una organización (ej: "Sede Norte")

**Colaborador:** Profesional que ofrece servicios (ej: médico, estilista)

**Servicio:** Tipo de atención ofrecida (ej: "Consulta General", "Corte de Cabello")

**Cita:** Reserva de un cliente para recibir uno o más servicios

**Bloqueo:** Período de tiempo donde un colaborador no está disponible

**Horario:** Configuración de días y horas laborales de un colaborador

**Slug:** Identificador URL-friendly de una organización (ej: "clinica-abc")

---

**Versión del Manual:** 1.0
**Fecha:** Octubre 2025
**Sistema:** Gestión de Citas Multi-Tenant
