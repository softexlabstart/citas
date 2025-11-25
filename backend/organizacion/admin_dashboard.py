"""
Dashboard personalizado para el panel de administración.
Vista central para administradores que muestra métricas de todas las organizaciones.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
import logging

from organizacion.models import Organizacion
from usuarios.models import User
from citas.models_whatsapp import WhatsAppMessage

logger = logging.getLogger(__name__)


@staff_member_required
def admin_dashboard(request):
    """
    Dashboard principal para administradores.
    Muestra resumen de todas las organizaciones y métricas del sistema.
    """

    # Período de análisis
    today = timezone.now()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)

    # ===== MÉTRICAS GENERALES =====
    total_organizations = Organizacion.objects.count()
    total_users = User.objects.filter(is_active=True).count()

    # ===== ESTADÍSTICAS DE ORGANIZACIONES =====
    organizations_data = []

    for org in Organizacion.objects.all().order_by('-created_at'):
        try:
            # Contar usuarios de esta organización
            users_count = org.perfiles.filter(usuario__is_active=True).count()
            inactive_users_count = org.perfiles.filter(usuario__is_active=False).count()

            # Usuarios activos en los últimos 7 días
            active_users_7d = org.perfiles.filter(
                usuario__last_login__gte=last_7_days
            ).count()

            # Contar sedes
            sedes_count = org.sedes.count()

            # Estadísticas de citas (últimos 7 días) - usando SQL raw
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_cita"
                    WHERE created_at >= %s
                """, [last_7_days])
                citas_7d = cursor.fetchone()[0]

            # Estadísticas de WhatsApp (últimos 7 días)
            with connection.cursor() as cursor:
                # Total mensajes
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_whatsapp_message"
                    WHERE created_at >= %s
                """, [last_7_days])
                messages_7d = cursor.fetchone()[0]

                # Mensajes fallidos
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_whatsapp_message"
                    WHERE created_at >= %s
                    AND status = 'failed'
                """, [last_7_days])
                failed_7d = cursor.fetchone()[0]

            # Calcular tasa de error
            error_rate = (failed_7d / messages_7d * 100) if messages_7d > 0 else 0

            # Determinar estado de salud
            if error_rate > 20:
                health_status = 'critical'
                health_label = 'Crítico'
            elif error_rate > 10:
                health_status = 'warning'
                health_label = 'Advertencia'
            else:
                health_status = 'healthy'
                health_label = 'Saludable'

            organizations_data.append({
                'id': org.id,
                'nombre': org.nombre,
                'schema': org.schema_name,
                'users_count': users_count,
                'inactive_users_count': inactive_users_count,
                'active_users_7d': active_users_7d,
                'sedes_count': sedes_count,
                'citas_7d': citas_7d,
                'messages_7d': messages_7d,
                'failed_7d': failed_7d,
                'error_rate': round(error_rate, 1),
                'health_status': health_status,
                'health_label': health_label,
                'created_at': org.created_at,
            })

        except Exception as e:
            logger.error(f"Error getting stats for org {org.nombre}: {str(e)}")
            organizations_data.append({
                'id': org.id,
                'nombre': org.nombre,
                'schema': org.schema_name,
                'users_count': 0,
                'sedes_count': 0,
                'citas_7d': 0,
                'messages_7d': 0,
                'failed_7d': 0,
                'error_rate': 0,
                'health_status': 'unknown',
                'health_label': 'Desconocido',
                'created_at': org.created_at,
                'error': str(e)
            })

    # ===== MÉTRICAS DEL SISTEMA (últimos 7 días) =====
    total_citas_7d = sum(org['citas_7d'] for org in organizations_data)
    total_messages_7d = sum(org['messages_7d'] for org in organizations_data)
    total_failed_7d = sum(org['failed_7d'] for org in organizations_data)

    system_error_rate = (total_failed_7d / total_messages_7d * 100) if total_messages_7d > 0 else 0

    # ===== ALERTAS Y PROBLEMAS =====
    critical_orgs = [org for org in organizations_data if org['health_status'] == 'critical']
    warning_orgs = [org for org in organizations_data if org['health_status'] == 'warning']

    # ===== ERRORES RECIENTES =====
    recent_errors = []

    for org in Organizacion.objects.all():
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT
                        id,
                        recipient_name,
                        recipient_phone,
                        message_type,
                        error_message,
                        created_at
                    FROM "{org.schema_name}"."citas_whatsapp_message"
                    WHERE status = 'failed'
                    AND created_at >= %s
                    ORDER BY created_at DESC
                    LIMIT 5
                """, [last_7_days])

                for row in cursor.fetchall():
                    recent_errors.append({
                        'org_name': org.nombre,
                        'org_id': org.id,
                        'message_id': row[0],
                        'recipient_name': row[1],
                        'recipient_phone': row[2],
                        'message_type': row[3],
                        'error_message': row[4],
                        'created_at': row[5],
                    })
        except Exception:
            pass

    # Ordenar errores por fecha (más reciente primero)
    recent_errors.sort(key=lambda x: x['created_at'], reverse=True)
    recent_errors = recent_errors[:20]  # Mostrar solo los últimos 20

    # ===== ACTIVIDAD RECIENTE =====
    recent_users = User.objects.filter(
        date_joined__gte=last_7_days
    ).order_by('-date_joined')[:10]

    context = {
        # Métricas generales
        'total_organizations': total_organizations,
        'total_users': total_users,
        'total_citas_7d': total_citas_7d,
        'total_messages_7d': total_messages_7d,
        'total_failed_7d': total_failed_7d,
        'system_error_rate': round(system_error_rate, 1),

        # Datos de organizaciones
        'organizations_data': organizations_data,
        'critical_orgs': critical_orgs,
        'warning_orgs': warning_orgs,

        # Errores y actividad
        'recent_errors': recent_errors,
        'recent_users': recent_users,

        # Período
        'period': '7 días',
    }

    return render(request, 'admin/dashboard.html', context)
