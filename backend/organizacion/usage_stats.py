"""
Panel de Estadísticas de Uso por Organización
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from organizacion.models import Organizacion
from usuarios.models import User
import os


@staff_member_required
def usage_statistics(request):
    """
    Vista para ver estadísticas de uso detalladas por organización.
    """

    # Período de análisis
    today = timezone.now()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)

    # Optimización: Usar annotate para obtener todos los counts en una sola query
    organizations = Organizacion.objects.annotate(
        total_users=Count('perfiles__id', distinct=True),
        active_users=Count('perfiles__id', filter=Q(perfiles__usuario__is_active=True), distinct=True),
        inactive_users=Count('perfiles__id', filter=Q(perfiles__usuario__is_active=False), distinct=True),
        recently_active=Count('perfiles__id', filter=Q(perfiles__usuario__last_login__gte=last_7_days), distinct=True),
        never_logged_in=Count('perfiles__id', filter=Q(perfiles__usuario__last_login__isnull=True), distinct=True),
        sedes_count=Count('sedes__id', distinct=True)
    ).order_by('-created_at')

    organizations_stats = []

    for org in organizations:
        try:
            # Usar los valores anotados directamente
            total_users = org.total_users
            active_users = org.active_users
            inactive_users = org.inactive_users
            recently_active = org.recently_active
            never_logged_in = org.never_logged_in

            # ===== CITAS Y MENSAJES =====
            # Optimización: Una sola query para obtener todos los counts de citas y mensajes
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_cita" WHERE created_at >= %s) as citas_7d,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_cita" WHERE created_at >= %s) as citas_30d,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_cita") as citas_total,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_whatsapp_message" WHERE created_at >= %s) as messages_7d,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_whatsapp_message" WHERE created_at >= %s) as messages_30d,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_whatsapp_message") as messages_total
                """, [last_7_days, last_30_days, last_7_days, last_30_days])

                result = cursor.fetchone()
                citas_7d = result[0] if result else 0
                citas_30d = result[1] if result else 0
                citas_total = result[2] if result else 0
                messages_7d = result[3] if result else 0
                messages_30d = result[4] if result else 0
                messages_total = result[5] if result else 0

            # ===== STORAGE =====
            # Tamaño de logos y archivos
            storage_mb = 0
            if org.logo:
                try:
                    storage_mb = os.path.getsize(org.logo.path) / (1024 * 1024)
                except:
                    pass

            # ===== ENGAGEMENT =====
            # Calcular tasa de engagement (usuarios activos vs total)
            engagement_rate = (recently_active / total_users * 100) if total_users > 0 else 0

            # Promedio de citas por día (últimos 7 días)
            avg_citas_per_day = citas_7d / 7 if citas_7d > 0 else 0

            # Promedio de mensajes por día (últimos 7 días)
            avg_messages_per_day = messages_7d / 7 if messages_7d > 0 else 0

            organizations_stats.append({
                'id': org.id,
                'nombre': org.nombre,
                'created_at': org.created_at,

                # Usuarios
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'recently_active': recently_active,
                'never_logged_in': never_logged_in,
                'engagement_rate': round(engagement_rate, 1),

                # Citas
                'citas_7d': citas_7d,
                'citas_30d': citas_30d,
                'citas_total': citas_total,
                'avg_citas_per_day': round(avg_citas_per_day, 1),

                # Mensajes
                'messages_7d': messages_7d,
                'messages_30d': messages_30d,
                'messages_total': messages_total,
                'avg_messages_per_day': round(avg_messages_per_day, 1),

                # Storage
                'storage_mb': round(storage_mb, 2),

                # Sedes
                'sedes_count': org.sedes_count,
            })

        except Exception as e:
            # Si hay error, agregar con valores en 0
            organizations_stats.append({
                'id': org.id,
                'nombre': org.nombre,
                'created_at': org.created_at,
                'error': str(e),
                'total_users': 0,
                'active_users': 0,
                'inactive_users': 0,
                'recently_active': 0,
                'never_logged_in': 0,
                'engagement_rate': 0,
                'citas_7d': 0,
                'citas_30d': 0,
                'citas_total': 0,
                'avg_citas_per_day': 0,
                'messages_7d': 0,
                'messages_30d': 0,
                'messages_total': 0,
                'avg_messages_per_day': 0,
                'storage_mb': 0,
                'sedes_count': 0,
            })

    # Ordenar por actividad (citas en últimos 7 días)
    organizations_stats.sort(key=lambda x: x['citas_7d'], reverse=True)

    # Estadísticas globales
    total_citas_7d = sum(org['citas_7d'] for org in organizations_stats)
    total_messages_7d = sum(org['messages_7d'] for org in organizations_stats)
    total_active_users = sum(org['active_users'] for org in organizations_stats)

    context = {
        'organizations_stats': organizations_stats,
        'total_citas_7d': total_citas_7d,
        'total_messages_7d': total_messages_7d,
        'total_active_users': total_active_users,
    }

    return render(request, 'admin/usage_statistics.html', context)
