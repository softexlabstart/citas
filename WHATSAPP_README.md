# 📱 Sistema de Recordatorios por WhatsApp

## ✅ Implementación Completa

El sistema de notificaciones por WhatsApp ha sido completamente implementado y está listo para usar.

---

## 🎯 ¿Qué se envía automáticamente?

### 1. **Confirmación de Cita** ✉️
**Cuándo:** Inmediatamente al crear una cita
**Contenido:**
```
🔔 [Nombre del Negocio]

¡Hola Juan!

Tu cita ha sido confirmada:

📅 Fecha: 25/11/2025 a las 10:00
📍 Sede: Sede Principal
💼 Servicios: Corte de cabello, Barba

Te esperamos 10 minutos antes de tu cita.
```

### 2. **Recordatorio 24 Horas** ⏰
**Cuándo:** 24 horas antes de la cita
**Contenido:**
```
⏰ Recordatorio - [Nombre del Negocio]

Hola Juan,

Te recordamos que mañana tienes tu cita:

📅 Fecha: 25/11/2025 a las 10:00
📍 Sede: Sede Principal

Nos vemos mañana. ¡No faltes! 😊
```

### 3. **Recordatorio 1 Hora** 🔔
**Cuándo:** 1 hora antes de la cita
**Contenido:**
```
🔔 Recordatorio - [Nombre del Negocio]

Hola Juan,

Tu cita es en 1 hora:

🕐 Hora: 10:00
📍 Sede: Sede Principal

Te esperamos. Por favor llega a tiempo. ⏰
```

### 4. **Cancelación** ❌
**Cuándo:** Al cancelar una cita
**Contenido:**
```
❌ Cancelación - [Nombre del Negocio]

Hola Juan,

Tu cita ha sido cancelada:

📅 Fecha que tenías: 25/11/2025 a las 10:00
📍 Sede: Sede Principal

Si deseas reagendar, por favor contáctanos.
```

---

## 📂 Archivos Creados

### Backend
```
backend/
├── organizacion/
│   └── models.py (modificado - campos WhatsApp)
├── citas/
│   ├── models_whatsapp.py (NUEVO)
│   │   ├── WhatsAppMessage
│   │   └── WhatsAppReminderSchedule
│   ├── services/
│   │   └── whatsapp_service.py (NUEVO)
│   ├── tasks_whatsapp.py (NUEVO)
│   ├── admin_whatsapp.py (NUEVO)
│   ├── views.py (modificado - integración WhatsApp)
│   └── management/commands/
│       └── send_whatsapp_reminders.py (NUEVO)
├── core/
│   └── celery.py (modificado - Celery Beat)
└── requirements.txt (modificado - twilio added)
```

### Documentación
```
├── WHATSAPP_SETUP.md (NUEVO - Guía completa)
└── WHATSAPP_README.md (NUEVO - Este archivo)
```

---

## 🚀 Quick Start

### 1. Instalar Dependencias

```bash
cd backend
pip install twilio==9.0.4
```

### 2. Configurar Twilio

Agregar al `.env`:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### 3. Aplicar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Iniciar Celery

```bash
# Terminal 1: Worker
celery -A core worker -l info

# Terminal 2: Beat (para recordatorios automáticos)
celery -A core beat -l info
```

### 5. Activar WhatsApp en una Organización

Desde Django Admin:

1. Ir a `Organizaciones`
2. Editar una organización
3. Marcar `whatsapp_enabled = ✓`
4. Configurar `whatsapp_sender_name = "Mi Negocio"`
5. Guardar

---

## 🔧 Configuración por Organización

Cada organización puede controlar:

| Campo | Descripción | Default |
|-------|-------------|---------|
| `whatsapp_enabled` | Activar/desactivar WhatsApp | `False` |
| `whatsapp_sender_name` | Nombre que aparece en mensajes | Nombre de org |
| `whatsapp_reminder_24h_enabled` | Recordatorio 24h antes | `True` |
| `whatsapp_reminder_1h_enabled` | Recordatorio 1h antes | `True` |
| `whatsapp_confirmation_enabled` | Confirmación al crear | `True` |
| `whatsapp_cancellation_enabled` | Notificación al cancelar | `True` |

---

## 📊 Monitoreo

### Ver Mensajes Enviados

**Desde Django Admin:**
`/admin/citas/whatsappmessage/`

**Desde Python:**
```python
from citas.models_whatsapp import WhatsAppMessage

# Últimos 10 mensajes
WhatsAppMessage.objects.all()[:10]

# Mensajes fallidos
WhatsAppMessage.objects.filter(status='failed')

# Mensajes de hoy
from django.utils import timezone
from datetime import timedelta
today = timezone.now() - timedelta(days=1)
WhatsAppMessage.objects.filter(created_at__gte=today)
```

### Ver Recordatorios Programados

**Desde Django Admin:**
`/admin/citas/whatsappreminderschedule/`

**Desde Python:**
```python
from citas.models_whatsapp import WhatsAppReminderSchedule

# Recordatorios pendientes
WhatsAppReminderSchedule.objects.filter(is_sent=False)

# Próximos 20 recordatorios
WhatsAppReminderSchedule.objects.filter(is_sent=False)[:20]
```

---

## 🧪 Testing

### Prueba Manual Rápida

```python
from citas.models import Cita
from organizacion.models import Sede
from django.utils import timezone
from datetime import timedelta

# 1. Activar WhatsApp en tu organización
from organizacion.models import Organizacion
org = Organizacion.objects.first()
org.whatsapp_enabled = True
org.whatsapp_sender_name = "Mi Negocio"
org.save()

# 2. Crear una cita de prueba
sede = Sede.objects.first()
cita = Cita.objects.create(
    nombre="Juan Pérez",
    telefono_cliente="+573001234567",  # TU número
    email_cliente="test@example.com",
    fecha=timezone.now() + timedelta(hours=26),  # En 26 horas
    sede=sede,
    estado="Confirmada"
)
cita.servicios.add(sede.organizacion.servicios.first())

# 3. Verificar que se programaron los recordatorios
from citas.models_whatsapp import WhatsAppReminderSchedule
WhatsAppReminderSchedule.objects.filter(cita=cita)

# 4. Verificar mensaje de confirmación
from citas.models_whatsapp import WhatsAppMessage
WhatsAppMessage.objects.filter(cita=cita)
```

### Enviar Recordatorios Manualmente

```bash
# Ver qué se enviaría
python manage.py send_whatsapp_reminders --dry-run

# Enviar recordatorios pendientes
python manage.py send_whatsapp_reminders
```

---

## 💰 Costos Estimados

**Twilio WhatsApp (Colombia):**
- ~$0.0042 USD por mensaje saliente
- 100 citas/mes × 3 mensajes = **~$1.26 USD/mes**
- 1000 citas/mes × 3 mensajes = **~$12.60 USD/mes**

**Cuenta de prueba:** Twilio da $15 USD gratis al registrarte.

---

## 🔍 Logs

Todos los eventos se registran con el prefijo `[WhatsApp]`:

```bash
# Ver logs de WhatsApp
tail -f logs/django.log | grep "\[WhatsApp\]"

# Ejemplos de logs:
[WhatsApp] Enviando confirmación para cita #123
[WhatsApp] Confirmación enviada exitosamente para cita #123
[WhatsApp] Recordatorio 24h programado para cita #123
[WhatsApp] Tarea de recordatorios completada: 5 enviados, 0 fallidos
```

---

## 🐛 Troubleshooting

### Mensajes no se envían

1. **Verificar Celery está corriendo:**
   ```bash
   ps aux | grep celery
   ```

2. **Verificar configuración Twilio:**
   ```python
   from citas.services.whatsapp_service import whatsapp_service
   print(whatsapp_service.is_configured())  # Debe ser True
   ```

3. **Verificar que la organización tiene WhatsApp habilitado:**
   ```python
   org = Organizacion.objects.get(nombre="Mi Negocio")
   print(org.whatsapp_enabled)  # Debe ser True
   ```

4. **Verificar que la cita tiene teléfono:**
   ```python
   cita = Cita.objects.get(id=123)
   print(cita.telefono_cliente)  # Debe tener un número
   ```

### Error: "From number not in sandbox"

El número de destino debe unirse al Sandbox de Twilio:
1. Desde WhatsApp, enviar `join <código>` al +14155238886
2. Esperar confirmación

### Mensajes quedan en "pending"

Verificar:
1. Crédito en cuenta de Twilio
2. El error en `WhatsAppMessage.error_message`
3. Logs de Celery

---

## 📈 Próximos Pasos (Opcional)

- [ ] **Templates personalizados** por organización
- [ ] **Webhooks de Twilio** para confirmaciones de lectura
- [ ] **Dashboard de analytics** de mensajes
- [ ] **BYOA** - Permitir cuentas propias de Twilio
- [ ] **A/B testing** de mensajes
- [ ] **Reportes de engagement**

---

## 📞 Contacto de Soporte

Para dudas o problemas:
1. Revisar `WHATSAPP_SETUP.md` (guía completa)
2. Ver logs: `tail -f logs/django.log | grep WhatsApp`
3. Verificar Django Admin: `/admin/citas/whatsappmessage/`

---

**¡El sistema está listo para usar! 🎉**

Simplemente activa WhatsApp en la organización deseada y las notificaciones comenzarán a enviarse automáticamente.
