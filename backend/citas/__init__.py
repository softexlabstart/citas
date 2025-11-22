# Asegurar que Celery registre las tareas de WhatsApp
default_app_config = 'citas.apps.CitasConfig'

# Importar tareas para que Celery las registre
from . import tasks_whatsapp  # noqa
