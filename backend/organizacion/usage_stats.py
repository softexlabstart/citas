"""
Panel de Estadísticas de Uso por Organización
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import connection
from django.utils import timezone
from datetime import timedelta
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

    organizations_stats = []

    for org in Organizacion.objects.all().order_by('-created_at'):
        try:
            # ===== USUARIOS =====
            total_users = org.perfiles.count()
            active_users = org.perfiles.filter(usuario__is_active=True).count()
            inactive_users = org.perfiles.filter(usuario__is_active=False).count()

            # Usuarios que han iniciado sesión en últimos 7 días
            recently_active = org.perfiles.filter(
                usuario__last_login__gte=last_7_days
            ).count()

            # Usuarios que nunca han iniciado sesión
            never_logged_in = org.perfiles.filter(
                usuario__last_login__isnull=True
            ).count()

            # ===== CITAS =====
            with connection.cursor() as cursor:
                # Total citas (últimos 30 días)
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_cita"
                    WHERE created_at >= %s
                """, [last_30_days])
                result = cursor.fetchone()
                citas_30d = result[0] if result else 0

                # Total citas (últimos 7 días)
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_cita"
                    WHERE created_at >= %s
                """, [last_7_days])
                result = cursor.fetchone()
                citas_7d = result[0] if result else 0

                # Total citas (all time)
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_cita"
                """)
                result = cursor.fetchone()
                citas_total = result[0] if result else 0

            # ===== MENSAJES WHATSAPP =====
            with connection.cursor() as cursor:
                # Total mensajes (últimos 30 días)
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_whatsapp_message"
                    WHERE created_at >= %s
                """, [last_30_days])
                result = cursor.fetchone()
                messages_30d = result[0] if result else 0

                # Total mensajes (últimos 7 días)
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_whatsapp_message"
                    WHERE created_at >= %s
                """, [last_7_days])
                result = cursor.fetchone()
                messages_7d = result[0] if result else 0

                # Total mensajes (all time)
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{org.schema_name}"."citas_whatsapp_message"
                """)
                result = cursor.fetchone()
                messages_total = result[0] if result else 0

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
                'sedes_count': org.sedes.count(),
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
