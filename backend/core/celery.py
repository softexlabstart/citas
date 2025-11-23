import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Importar explícitamente las tareas de WhatsApp
app.autodiscover_tasks(['citas'], related_name='tasks_whatsapp')

# Configuración de tareas periódicas (Celery Beat)
app.conf.beat_schedule = {
    # Enviar recordatorios de WhatsApp cada 5 minutos
    'send-whatsapp-reminders': {
        'task': 'citas.tasks_whatsapp.send_scheduled_reminders',
        'schedule': crontab(minute='*/5'),  # Cada 5 minutos
    },

    # Limpiar mensajes antiguos de WhatsApp (diario a las 3 AM)
    'cleanup-old-whatsapp-messages': {
        'task': 'citas.tasks_whatsapp.cleanup_old_whatsapp_messages',
        'schedule': crontab(hour=3, minute=0),  # Todos los días a las 3:00 AM
    },
}
