"""
Vistas para reportes y estadísticas de WhatsApp.
Filtradas por organización (multi-tenant).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
import logging

from .models_whatsapp import WhatsAppMessage
from .permissions import IsAdminOrSedeAdminOrReadOnly
from usuarios.utils import get_perfil_or_first

logger = logging.getLogger(__name__)


class WhatsAppReportsViewSet(viewsets.ViewSet):
    """
    ViewSet para reportes de WhatsApp filtrados por organización.

    MULTI-TENANT: Cada organización solo ve sus propios datos.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSedeAdminOrReadOnly]

    def get_user_organization(self, request):
        """Obtiene la organización del usuario autenticado"""
        if request.user.is_superuser:
            return None  # Superuser ve todas las organizaciones

        perfil = get_perfil_or_first(request.user)
        if perfil and perfil.organizacion:
            return perfil.organizacion

        return None

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Resumen general de mensajes de WhatsApp.

        GET /api/citas/whatsapp-reports/summary/
        Query params:
            - days: Número de días hacia atrás (default: 30)
        """
        org = self.get_user_organization(request)
        days = int(request.query_params.get('days', 30))

        # Fecha de inicio
        start_date = timezone.now() - timedelta(days=days)

        # Query base
        queryset = WhatsAppMessage.objects.filter(created_at__gte=start_date)

        # MULTI-TENANT: Filtrar por organización
        if org:
            queryset = queryset.filter(organizacion=org)

        # Estadísticas generales
        total_messages = queryset.count()

        stats_by_status = queryset.values('status').annotate(count=Count('id'))

        stats_by_type = queryset.values('message_type').annotate(count=Count('id'))

        # Tasa de entrega
        delivered = queryset.filter(status='delivered').count()
        delivery_rate = (delivered / total_messages * 100) if total_messages > 0 else 0

        # Mensajes fallidos
        failed = queryset.filter(status='failed').count()
        failed_rate = (failed / total_messages * 100) if total_messages > 0 else 0

        # Estadísticas por día (últimos 7 días)
        daily_stats = []
        for i in range(7):
            day_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            day_messages = queryset.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )

            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'total': day_messages.count(),
                'delivered': day_messages.filter(status='delivered').count(),
                'failed': day_messages.filter(status='failed').count(),
            })

        return Response({
            'period_days': days,
            'total_messages': total_messages,
            'delivery_rate': round(delivery_rate, 2),
            'failed_rate': round(failed_rate, 2),
            'by_status': {item['status']: item['count'] for item in stats_by_status},
            'by_type': {item['message_type']: item['count'] for item in stats_by_type},
            'daily_stats': list(reversed(daily_stats)),  # Más reciente primero
            'organization': org.nombre if org else 'Todas'
        })

    @action(detail=False, methods=['get'])
    def recent_messages(self, request):
        """
        Lista de mensajes recientes de WhatsApp.

        GET /api/citas/whatsapp-reports/recent-messages/
        Query params:
            - limit: Número de mensajes (default: 20, max: 100)
            - status: Filtrar por estado (pending, sent, delivered, failed)
            - message_type: Filtrar por tipo
        """
        org = self.get_user_organization(request)
        limit = min(int(request.query_params.get('limit', 20)), 100)
        status_filter = request.query_params.get('status')
        type_filter = request.query_params.get('message_type')

        # Query base
        queryset = WhatsAppMessage.objects.select_related(
            'cita', 'organizacion'
        ).order_by('-created_at')

        # MULTI-TENANT: Filtrar por organización
        if org:
            queryset = queryset.filter(organizacion=org)

        # Filtros opcionales
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if type_filter:
            queryset = queryset.filter(message_type=type_filter)

        # Limitar resultados
        messages = queryset[:limit]

        # Serializar
        data = []
        for msg in messages:
            data.append({
                'id': msg.id,
                'message_type': msg.message_type,
                'status': msg.status,
                'recipient_name': msg.recipient_name,
                'recipient_phone': msg.recipient_phone,
                'cita_id': msg.cita.id if msg.cita else None,
                'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                'delivered_at': msg.delivered_at.isoformat() if msg.delivered_at else None,
                'error_message': msg.error_message,
                'created_at': msg.created_at.isoformat(),
            })

        return Response({
            'count': len(data),
            'messages': data,
            'organization': org.nombre if org else 'Todas'
        })

    @action(detail=False, methods=['get'])
    def delivery_performance(self, request):
        """
        Rendimiento de entrega de mensajes por tipo.

        GET /api/citas/whatsapp-reports/delivery-performance/
        """
        org = self.get_user_organization(request)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        # Query base
        queryset = WhatsAppMessage.objects.filter(created_at__gte=start_date)

        # MULTI-TENANT: Filtrar por organización
        if org:
            queryset = queryset.filter(organizacion=org)

        # Rendimiento por tipo de mensaje
        performance = []
        for msg_type, msg_label in WhatsAppMessage.MESSAGE_TYPES:
            type_messages = queryset.filter(message_type=msg_type)
            total = type_messages.count()

            if total > 0:
                delivered = type_messages.filter(status='delivered').count()
                failed = type_messages.filter(status='failed').count()
                pending = type_messages.filter(status__in=['pending', 'sent']).count()

                performance.append({
                    'type': msg_type,
                    'label': msg_label,
                    'total': total,
                    'delivered': delivered,
                    'failed': failed,
                    'pending': pending,
                    'delivery_rate': round((delivered / total) * 100, 2),
                    'failure_rate': round((failed / total) * 100, 2)
                })

        return Response({
            'period_days': days,
            'performance': performance,
            'organization': org.nombre if org else 'Todas'
        })
