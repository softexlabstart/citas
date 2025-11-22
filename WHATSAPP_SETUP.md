# 📱 Configuración de WhatsApp con Twilio

Guía completa para configurar recordatorios por WhatsApp en el sistema de citas.

## 📋 Tabla de Contenidos

- [Resumen](#resumen)
- [Requisitos](#requisitos)
- [Configuración de Twilio](#configuración-de-twilio)
- [Configuración del Backend](#configuración-del-backend)
- [Configuración de Celery Beat](#configuración-de-celery-beat)
- [Activar WhatsApp por Organización](#activar-whatsapp-por-organización)
- [Testing](#testing)
- [Costos y Facturación](#costos-y-facturación)
- [Troubleshooting](#troubleshooting)

---

## Resumen

El sistema envía notificaciones automáticas por WhatsApp para:

✅ **Confirmación de cita** - Cuando se crea una cita
✅ **Recordatorio 24h** - 24 horas antes de la cita
✅ **Recordatorio 1h** - 1 hora antes de la cita
✅ **Cancelación** - Cuando se cancela una cita

### Arquitectura

```
Usuario crea cita → Django → Celery Task → Twilio API → WhatsApp del cliente
                      ↓
               WhatsAppMessage
                (tracking en BD)
```

---

## Requisitos

- **Cuenta de Twilio** (gratis para testing, pago para producción)
- **Celery** configurado y corriendo
- **Redis** corriendo (para Celery)
- **Python** con `twilio==9.0.4` instalado

---

## Configuración de Twilio

### 1. Crear Cuenta en Twilio

1. Ir a [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Registrarte (gratis, incluye $15 USD de crédito)
3. Verificar tu email y número de teléfono

### 2. Obtener Credenciales

Una vez dentro del dashboard de Twilio:

1. Ve a **Console** → **Account Info**
2. Copia:
   - **Account SID**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Auth Token**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 3. Activar WhatsApp Sandbox (Para Testing)

**IMPORTANTE:** Para testing, usa el **WhatsApp Sandbox** de Twilio (gratis).

1. En Twilio Console, ve a **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Verás un número como: `+1 415 523 8886`
3. Verás un código como: `join <palabra-clave>`
4. Desde tu WhatsApp personal, envía ese mensaje al número de Twilio
5. Recibirás confirmación: "You are all set!"

**Número de Sandbox:** `whatsapp:+14155238886` (ejemplo, verificar en tu consola)

### 4. Para Producción (Opcional, requiere aprobación)

Para usar tu propio número en producción:

1. Ve a **Messaging** → **Senders** → **WhatsApp senders**
2. Click **Request to enable your Twilio numbers for WhatsApp**
3. Completa el proceso de aprobación de Meta (puede tomar 1-2 semanas)
4. Una vez aprobado, tendrás tu propio número

---

## Configuración del Backend

### 1. Instalar Dependencia

```bash
cd backend
pip install twilio==9.0.4
```

O usar requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Variables de Entorno

Agregar al archivo `.env`:

```bash
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

**IMPORTANTE:**
- Para testing, usa el número del Sandbox: `whatsapp:+14155238886`
- Para producción, usa tu número aprobado: `whatsapp:+57300xxxxxxx`

### 3. Aplicar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto creará las tablas:
- `citas_whatsapp_message` - Registro de mensajes enviados
- `citas_whatsapp_reminder_schedule` - Programación de recordatorios

### 4. Verificar Configuración

```bash
python manage.py shell
```

```python
from citas.services.whatsapp_service import whatsapp_service

# Verificar que está configurado
print(whatsapp_service.is_configured())  # Debe ser True

# Ver configuración
print(f"SID: {whatsapp_service.account_sid[:10]}...")
print(f"From: {whatsapp_service.from_number}")
```

---

## Configuración de Celery Beat

Los recordatorios se envían automáticamente mediante **Celery Beat**.

### 1. Configurar Celery Beat Schedule

Editar `backend/core/celery.py` y agregar:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ... otros schedules ...

    # Enviar recordatorios de WhatsApp cada 5 minutos
    'send-whatsapp-reminders': {
        'task': 'citas.tasks_whatsapp.send_scheduled_reminders',
        'schedule': crontab(minute='*/5'),  # Cada 5 minutos
    },

    # Limpiar mensajes antiguos (diario a las 3 AM)
    'cleanup-old-whatsapp-messages': {
        'task': 'citas.tasks_whatsapp.cleanup_old_whatsapp_messages',
        'schedule': crontab(hour=3, minute=0),
    },
}
```

### 2. Iniciar Celery Worker

```bash
# Terminal 1: Worker
celery -A core worker -l info

# Terminal 2: Beat (scheduler)
celery -A core beat -l info
```

### 3. Producción con Supervisord

Ver `CELERY_SETUP.md` para configuración completa de producción.

---

## Activar WhatsApp por Organización

### 1. Desde Django Admin

1. Ir a `/admin/organizacion/organizacion/`
2. Editar una organización
3. Configurar:
   - **whatsapp_enabled**: ✓ (activar)
   - **whatsapp_sender_name**: "Peluquería XYZ" (nombre que aparecerá)
   - **whatsapp_reminder_24h_enabled**: ✓
   - **whatsapp_reminder_1h_enabled**: ✓
   - **whatsapp_confirmation_enabled**: ✓
   - **whatsapp_cancellation_enabled**: ✓
4. Guardar

### 2. Desde Python/Shell

```python
from organizacion.models import Organizacion

org = Organizacion.objects.get(nombre="Mi Negocio")
org.whatsapp_enabled = True
org.whatsapp_sender_name = "Mi Negocio"
org.whatsapp_reminder_24h_enabled = True
org.whatsapp_reminder_1h_enabled = True
org.whatsapp_confirmation_enabled = True
org.whatsapp_cancellation_enabled = True
org.save()
```

---

## Testing

### Prueba Manual

#### 1. Crear una Cita de Prueba

```python
from citas.models import Cita
from organizacion.models import Sede
from django.utils import timezone
from datetime import timedelta

sede = Sede.objects.first()

# Crear cita para dentro de 2 horas
cita = Cita.objects.create(
    nombre="Juan Pérez",
    telefono_cliente="+573001234567",  # TU número de WhatsApp
    email_cliente="test@example.com",
    fecha=timezone.now() + timedelta(hours=2),
    sede=sede,
    estado="Confirmada"
)

# Agregar servicios
cita.servicios.add(sede.organizacion.servicios.first())
```

#### 2. Enviar Confirmación Manual

```python
from citas.tasks_whatsapp import send_whatsapp_confirmation

# Enviar ahora (síncrono)
send_whatsapp_confirmation(cita.id)

# O encolar tarea (asíncrono)
send_whatsapp_confirmation.delay(cita.id)
```

#### 3. Verificar en BD

```python
from citas.models_whatsapp import WhatsAppMessage

# Ver mensajes enviados
WhatsAppMessage.objects.all()

# Ver último mensaje
last = WhatsAppMessage.objects.last()
print(f"Estado: {last.status}")
print(f"SID: {last.twilio_sid}")
print(f"Mensaje:\n{last.message_body}")
```

#### 4. Verificar Recordatorios Programados

```python
from citas.models_whatsapp import WhatsAppReminderSchedule

# Ver recordatorios pendientes
WhatsAppReminderSchedule.objects.filter(is_sent=False)
```

### Comando de Testing

```bash
# Ver qué se enviaría sin enviar
python manage.py send_whatsapp_reminders --dry-run

# Enviar recordatorios pendientes
python manage.py send_whatsapp_reminders
```

---

## Costos y Facturación

### Precios de Twilio (Aproximados)

**WhatsApp Business - Conversaciones:**
- Conversación iniciada por negocio: **~$0.005 USD**
- Mensaje dentro de ventana de 24h: **Gratis**

**Colombia (ejemplo):**
- Mensaje saliente: **$0.0042 USD**
- 1000 mensajes = **~$4.20 USD**

### Cálculo de Costos

```python
# Ejemplo: 100 clientes/mes, 3 mensajes por cita

Mensajes por cliente:
- 1 confirmación
- 1 recordatorio 24h
- 1 recordatorio 1h
Total: 3 mensajes

Costo mensual:
100 clientes × 3 mensajes × $0.0042 = $1.26 USD
```

### Monitoreo de Costos

```python
from citas.models_whatsapp import WhatsAppMessage
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone

# Mensajes enviados último mes
month_ago = timezone.now() - timedelta(days=30)
sent_count = WhatsAppMessage.objects.filter(
    created_at__gte=month_ago,
    status='sent'
).count()

print(f"Mensajes enviados: {sent_count}")
print(f"Costo estimado: ${sent_count * 0.0042:.2f} USD")
```

---

## Troubleshooting

### Problema: "Twilio no está configurado"

**Síntoma:** Logs muestran "Twilio WhatsApp no configurado correctamente"

**Solución:**
1. Verificar que `.env` tiene las 3 variables:
   ```bash
   TWILIO_ACCOUNT_SID=AC...
   TWILIO_AUTH_TOKEN=...
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```
2. Reiniciar Django/Celery después de agregar variables

### Problema: Error 63016 - "From number not in sandbox"

**Síntoma:** Twilio error code 63016

**Solución:**
1. El número de destino debe unirse al Sandbox primero
2. Desde WhatsApp, enviar `join <código>` al número de Twilio
3. Para producción, solicitar aprobación de Meta

### Problema: Error 21211 - "Invalid 'To' Phone Number"

**Síntoma:** Formato de número inválido

**Solución:**
1. Asegurarse que el número incluye código de país: `+573001234567`
2. Sin espacios ni caracteres especiales
3. Formato correcto: `whatsapp:+573001234567`

### Problema: Mensajes no se envían automáticamente

**Síntoma:** Los recordatorios no llegan

**Solución:**
1. Verificar que Celery Beat está corriendo:
   ```bash
   ps aux | grep celery
   ```
2. Ver logs de Celery:
   ```bash
   tail -f celery.log
   ```
3. Verificar que la organización tiene `whatsapp_enabled=True`
4. Verificar que la cita tiene `telefono_cliente`

### Problema: Mensajes quedan en "pending"

**Síntoma:** `status='pending'` en BD

**Solución:**
1. Ver `error_message` en el registro de WhatsAppMessage
2. Verificar crédito en cuenta de Twilio
3. Verificar que el número de destino es válido

---

## Logs y Monitoreo

### Ver Logs de WhatsApp

```bash
# Filtrar logs de WhatsApp
tail -f logs/django.log | grep "\[WhatsApp\]"
```

### Dashboard de Admin

Crear vista en Django Admin para monitorear:

```python
# admin.py
from django.contrib import admin
from .models_whatsapp import WhatsAppMessage, WhatsAppReminderSchedule

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'message_type', 'recipient_name', 'status', 'created_at']
    list_filter = ['status', 'message_type', 'created_at']
    search_fields = ['recipient_name', 'recipient_phone']
    readonly_fields = ['twilio_sid', 'created_at', 'sent_at']

@admin.register(WhatsAppReminderSchedule)
class WhatsAppReminderScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'cita', 'reminder_type', 'scheduled_time', 'is_sent']
    list_filter = ['reminder_type', 'is_sent']
```

---

## Próximos Pasos (Opcionales)

1. **Templates Personalizados:** Permitir que cada organización personalice los mensajes
2. **Webhooks de Twilio:** Recibir confirmaciones de entrega y lectura
3. **BYOA (Bring Your Own Account):** Permitir que organizaciones usen su propia cuenta Twilio
4. **Analytics Dashboard:** Dashboard visual de estadísticas de mensajes
5. **A/B Testing:** Probar diferentes mensajes y medir engagement

---

## Referencias

- [Twilio WhatsApp API Docs](https://www.twilio.com/docs/whatsapp)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [WhatsApp Business Policy](https://www.whatsapp.com/legal/business-policy)
- [Celery Beat Documentation](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)

---

¿Preguntas? Revisa la documentación o contacta al equipo de desarrollo.
