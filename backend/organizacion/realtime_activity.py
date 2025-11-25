"""
Panel de Actividad en Tiempo Real
Monitorea actividad del sistema en vivo usando Server-Sent Events (SSE)
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import StreamingHttpResponse
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from organizacion.models import Organizacion
from usuarios.models import User
import json
import time


@staff_member_required
def realtime_activity(request):
    """
    Vista principal del panel de actividad en tiempo real.
    """
    return render(request, 'admin/realtime_activity.html')


@staff_member_required
def activity_stream(request):
    """
    Stream de eventos Server-Sent Events (SSE) para actualizaciones en tiempo real.
    """
    def event_stream():
        """Generador de eventos SSE"""
        while True:
            try:
                # Recopilar métricas en tiempo real
                data = get_realtime_metrics()

                # Enviar datos en formato SSE (debe ser bytes)
                yield f"data: {json.dumps(data)}\n\n".encode('utf-8')

                # Actualizar cada 10 segundos (optimizado, antes era 3)
                time.sleep(10)

            except Exception as e:
                # En caso de error, enviar mensaje de error
                error_data = {'error': str(e)}
                yield f"data: {json.dumps(error_data)}\n\n".encode('utf-8')
                time.sleep(5)

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
    return response


def get_realtime_metrics():
    """
    Obtiene métricas en tiempo real de todas las organizaciones.
    Optimizado para reducir queries a la base de datos.
    """
    now = timezone.now()
    last_minute = now - timedelta(minutes=1)
    last_5_minutes = now - timedelta(minutes=5)
    last_hour = now - timedelta(hours=1)

    metrics = {
        'timestamp': now.isoformat(),
        'global': {
            'users_online': 0,
            'citas_last_minute': 0,
            'citas_last_hour': 0,
            'messages_last_minute': 0,
            'messages_last_hour': 0,
        },
        'organizations': [],
        'recent_activities': []
    }

    # Usuarios activos (últimos 5 minutos basado en last_login)
    users_online = User.objects.filter(
        last_login__gte=last_5_minutes,
        is_active=True
    ).count()
    metrics['global']['users_online'] = users_online

    # Optimización: Cargar organizaciones una sola vez con prefetch de perfiles
    from django.db.models import Prefetch
    from usuarios.models import PerfilUsuario

    organizations = Organizacion.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'perfiles',
            queryset=PerfilUsuario.objects.select_related('usuario').filter(
                usuario__last_login__gte=last_5_minutes,
                usuario__is_active=True
            )
        )
    ).order_by('nombre')

    # Recopilar actividades recientes de todas las orgs en una sola pasada
    recent_activities = []

    # Por cada organización
    for org in organizations:
        try:
            org_data = {
                'id': org.id,
                'nombre': org.nombre,
                'citas_last_minute': 0,
                'citas_last_hour': 0,
                'messages_last_minute': 0,
                'messages_last_hour': 0,
                'users_online': 0,
            }

            # Optimización: Una sola query para todos los counts de citas y mensajes
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_cita" WHERE created_at >= %s) as citas_minute,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_cita" WHERE created_at >= %s) as citas_hour,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_whatsapp_message" WHERE created_at >= %s) as messages_minute,
                        (SELECT COUNT(*) FROM "{org.schema_name}"."citas_whatsapp_message" WHERE created_at >= %s) as messages_hour
                """, [last_minute, last_hour, last_minute, last_hour])

                result = cursor.fetchone()
                org_data['citas_last_minute'] = result[0] if result else 0
                org_data['citas_last_hour'] = result[1] if result else 0
                org_data['messages_last_minute'] = result[2] if result else 0
                org_data['messages_last_hour'] = result[3] if result else 0

            # Usuarios online de esta organización (usar prefetch ya cargado)
            org_data['users_online'] = len(org.perfiles.all())

            # Actualizar métricas globales
            metrics['global']['citas_last_minute'] += org_data['citas_last_minute']
            metrics['global']['citas_last_hour'] += org_data['citas_last_hour']
            metrics['global']['messages_last_minute'] += org_data['messages_last_minute']
            metrics['global']['messages_last_hour'] += org_data['messages_last_hour']

            # Recopilar actividades recientes de esta org (en el mismo loop)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT
                            id,
                            created_at,
                            estado
                        FROM "{org.schema_name}"."citas_cita"
                        ORDER BY created_at DESC
                        LIMIT 5
                    """)

                    for row in cursor.fetchall():
                        cita_id, created_at, estado = row
                        recent_activities.append({
                            'type': 'cita',
                            'org_nombre': org.nombre,
                            'org_id': org.id,
                            'cita_id': cita_id,
                            'timestamp': created_at.isoformat() if created_at else None,
                            'estado': estado,
                        })
            except:
                pass

            # Solo agregar si tiene actividad
            if (org_data['citas_last_hour'] > 0 or
                org_data['messages_last_hour'] > 0 or
                org_data['users_online'] > 0):
                metrics['organizations'].append(org_data)

        except Exception:
            # Si hay error en esta org, continuar con las demás
            continue

    # Ordenar por timestamp y tomar las 10 más recientes
    recent_activities.sort(key=lambda x: x['timestamp'] or '', reverse=True)
    metrics['recent_activities'] = recent_activities[:10]

    return metrics
