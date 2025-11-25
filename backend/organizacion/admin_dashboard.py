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
    # Optimización: Usar annotate para obtener counts en una sola query
    organizations = Organizacion.objects.annotate(
        users_count=Count('perfiles__id', filter=Q(perfiles__usuario__is_active=True), distinct=True),
        inactive_users_count=Count('perfiles__id', filter=Q(perfiles__usuario__is_active=False), distinct=True),
        active_users_7d=Count('perfiles__id', filter=Q(perfiles__usuario__last_login__gte=last_7_days), distinct=True),
        sedes_count=Count('sedes__id', distinct=True)
    ).order_by('-created_at')

    organizations_data = []

    for org in organizations:
        try:
            # Estadísticas de citas y mensajes WhatsApp en UNA SOLA query por org
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_cita" WHERE created_at >= %s) as citas_7d,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_whatsapp_message" WHERE created_at >= %s) as messages_7d,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_whatsapp_message" WHERE created_at >= %s AND status = 'failed') as failed_7d
                """, [last_7_days, last_7_days, last_7_days])

                result = cursor.fetchone()
                citas_7d = result[0] if result else 0
                messages_7d = result[1] if result else 0
                failed_7d = result[2] if result else 0

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
                'users_count': org.users_count,
                'inactive_users_count': org.inactive_users_count,
                'active_users_7d': org.active_users_7d,
                'sedes_count': org.sedes_count,
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
    # Optimización: Obtener errores de todas las orgs en un batch
    recent_errors = []

    # Construir una sola query UNION ALL para todos los schemas
    union_queries = []
    params = []

    for org in organizations:
        union_queries.append(f"""
            SELECT
                '{org.nombre}' as org_name,
                {org.id} as org_id,
                id,
                recipient_name,
                recipient_phone,
                message_type,
                error_message,
                created_at
            FROM "{org.schema_name}"."citas_whatsapp_message"
            WHERE status = 'failed'
            AND created_at >= %s
        """)
        params.append(last_7_days)

    if union_queries:
        try:
            with connection.cursor() as cursor:
                full_query = " UNION ALL ".join(union_queries) + " ORDER BY created_at DESC LIMIT 20"
                cursor.execute(full_query, params)

                for row in cursor.fetchall():
                    recent_errors.append({
                        'org_name': row[0],
                        'org_id': row[1],
                        'message_id': row[2],
                        'recipient_name': row[3],
                        'recipient_phone': row[4],
                        'message_type': row[5],
                        'error_message': row[6],
                        'created_at': row[7],
                    })
        except Exception as e:
            logger.error(f"Error fetching recent errors: {str(e)}")

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
