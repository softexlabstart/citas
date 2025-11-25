"""
Panel de Salud del Sistema - Health Check
Verifica el estado de servicios externos, conectividad y recursos.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import connection, connections
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import psutil
import os

from organizacion.models import Organizacion

logger = logging.getLogger(__name__)


def check_database():
    """Verifica conectividad y estado de la base de datos"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        # Obtener estadísticas de conexiones
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT count(*)
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            active_connections = cursor.fetchone()[0]

        return {
            'status': 'healthy',
            'message': 'Base de datos conectada',
            'active_connections': active_connections,
            'database': settings.DATABASES['default']['NAME'],
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error de conexión: {str(e)}',
            'active_connections': 0,
        }


def check_twilio():
    """Verifica conectividad con Twilio"""
    try:
        from twilio.rest import Client

        # Verificar que las credenciales existen
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

        if not account_sid or not auth_token:
            return {
                'status': 'warning',
                'message': 'Credenciales de Twilio no configuradas',
                'account_sid': None,
            }

        # Intentar conectar
        client = Client(account_sid, auth_token)
        account = client.api.accounts(account_sid).fetch()

        return {
            'status': 'healthy',
            'message': 'Conectado a Twilio',
            'account_sid': account_sid[:8] + '...',
            'account_status': account.status,
        }
    except Exception as e:
        logger.error(f"Twilio health check failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error de conexión: {str(e)}',
            'account_sid': None,
        }


def check_migrations():
    """Verifica estado de migraciones por tenant"""
    results = []

    for org in Organizacion.objects.all():
        try:
            with connection.cursor() as cursor:
                # Cambiar al schema del tenant
                cursor.execute(f"SET search_path TO {org.schema_name}")

                # Verificar si existen las tablas principales
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_name = 'citas_cita'
                    )
                """, [org.schema_name])
                citas_exists = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_name = 'citas_whatsapp_message'
                    )
                """, [org.schema_name])
                whatsapp_exists = cursor.fetchone()[0]

                if citas_exists and whatsapp_exists:
                    status = 'healthy'
                    message = 'Todas las tablas existen'
                elif citas_exists or whatsapp_exists:
                    status = 'warning'
                    message = 'Algunas tablas faltan'
                else:
                    status = 'error'
                    message = 'Tablas principales no existen'

                results.append({
                    'org_name': org.nombre,
                    'org_id': org.id,
                    'schema': org.schema_name,
                    'status': status,
                    'message': message,
                    'citas_table': citas_exists,
                    'whatsapp_table': whatsapp_exists,
                })
        except Exception as e:
            logger.error(f"Migration check failed for {org.nombre}: {str(e)}")
            results.append({
                'org_name': org.nombre,
                'org_id': org.id,
                'schema': org.schema_name,
                'status': 'error',
                'message': str(e),
                'citas_table': False,
                'whatsapp_table': False,
            })

    return results


def check_disk_space():
    """Verifica espacio en disco"""
    try:
        disk = psutil.disk_usage('/')

        percent_used = disk.percent

        if percent_used > 90:
            status = 'critical'
            message = 'Espacio en disco crítico'
        elif percent_used > 75:
            status = 'warning'
            message = 'Espacio en disco bajo'
        else:
            status = 'healthy'
            message = 'Espacio en disco OK'

        return {
            'status': status,
            'message': message,
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'percent_used': percent_used,
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error al verificar disco: {str(e)}',
            'percent_used': 0,
        }


def check_memory():
    """Verifica uso de memoria"""
    try:
        memory = psutil.virtual_memory()

        percent_used = memory.percent

        if percent_used > 90:
            status = 'critical'
            message = 'Memoria crítica'
        elif percent_used > 75:
            status = 'warning'
            message = 'Memoria alta'
        else:
            status = 'healthy'
            message = 'Memoria OK'

        return {
            'status': status,
            'message': message,
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'percent_used': percent_used,
        }
    except Exception as e:
        logger.error(f"Memory check failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error al verificar memoria: {str(e)}',
            'percent_used': 0,
        }


def check_webhook_connectivity():
    """Verifica que la URL del webhook sea accesible"""
    try:
        webhook_url = f"{settings.FRONTEND_URL}/api/citas/whatsapp-webhook/"

        # Verificar que la URL esté configurada
        if not settings.FRONTEND_URL:
            return {
                'status': 'warning',
                'message': 'FRONTEND_URL no configurada',
                'url': None,
            }

        return {
            'status': 'healthy',
            'message': 'Webhook URL configurada',
            'url': webhook_url,
        }
    except Exception as e:
        logger.error(f"Webhook check failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error: {str(e)}',
            'url': None,
        }


@staff_member_required
def system_health(request):
    """
    Panel de salud del sistema.
    Muestra el estado de todos los componentes y servicios.
    """

    # Ejecutar todos los health checks
    db_health = check_database()
    twilio_health = check_twilio()
    disk_health = check_disk_space()
    memory_health = check_memory()
    webhook_health = check_webhook_connectivity()
    migration_status = check_migrations()

    # Calcular estado general del sistema
    critical_checks = [
        db_health['status'] == 'error',
        twilio_health['status'] == 'error',
        disk_health['status'] == 'critical',
        memory_health['status'] == 'critical',
    ]

    warning_checks = [
        db_health['status'] == 'warning',
        twilio_health['status'] == 'warning',
        disk_health['status'] == 'warning',
        memory_health['status'] == 'warning',
        webhook_health['status'] == 'warning',
    ]

    if any(critical_checks):
        overall_status = 'critical'
        overall_message = 'Sistema con problemas críticos'
    elif any(warning_checks):
        overall_status = 'warning'
        overall_message = 'Sistema funcionando con advertencias'
    else:
        overall_status = 'healthy'
        overall_message = 'Todos los sistemas operativos'

    # Contar problemas en migraciones
    migration_errors = sum(1 for m in migration_status if m['status'] == 'error')
    migration_warnings = sum(1 for m in migration_status if m['status'] == 'warning')

    context = {
        'overall_status': overall_status,
        'overall_message': overall_message,
        'db_health': db_health,
        'twilio_health': twilio_health,
        'disk_health': disk_health,
        'memory_health': memory_health,
        'webhook_health': webhook_health,
        'migration_status': migration_status,
        'migration_errors': migration_errors,
        'migration_warnings': migration_warnings,
        'checked_at': timezone.now(),
    }

    return render(request, 'admin/health_check.html', context)
