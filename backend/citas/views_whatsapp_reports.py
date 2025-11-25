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

        # Estadísticas generales usando agregaciones (1 query en lugar de 3)
        from django.db.models import Sum, Case, When, IntegerField

        stats_aggregate = queryset.aggregate(
            total=Count('id'),
            delivered=Count(Case(When(status='delivered', then=1))),
            failed=Count(Case(When(status='failed', then=1)))
        )

        total_messages = stats_aggregate['total']
        delivered = stats_aggregate['delivered']
        failed = stats_aggregate['failed']

        delivery_rate = (delivered / total_messages * 100) if total_messages > 0 else 0
        failed_rate = (failed / total_messages * 100) if total_messages > 0 else 0

        # Estadísticas por estado y tipo (queries optimizadas)
        stats_by_status = queryset.values('status').annotate(count=Count('id'))
        stats_by_type = queryset.values('message_type').annotate(count=Count('id'))

        # Estadísticas por día usando una sola query con agregación
        from django.db.models.functions import TruncDate

        daily_data = queryset.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Count('id'),
            delivered=Count(Case(When(status='delivered', then=1))),
            failed=Count(Case(When(status='failed', then=1)))
        ).order_by('date')

        # Convertir a diccionario por fecha para lookup rápido
        daily_dict = {item['date'].strftime('%Y-%m-%d'): item for item in daily_data}

        # Generar estadísticas para los últimos 7 días (rellenar con 0 si no hay datos)
        daily_stats = []
        for i in range(7):
            day_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            date_key = day_start.strftime('%Y-%m-%d')

            if date_key in daily_dict:
                daily_stats.append({
                    'date': date_key,
                    'total': daily_dict[date_key]['total'],
                    'delivered': daily_dict[date_key]['delivered'],
                    'failed': daily_dict[date_key]['failed']
                })
            else:
                daily_stats.append({
                    'date': date_key,
                    'total': 0,
                    'delivered': 0,
                    'failed': 0
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
        Lista de mensajes recientes de WhatsApp con paginación.

        GET /api/citas/whatsapp-reports/recent-messages/
        Query params:
            - page: Número de página (default: 1)
            - page_size: Tamaño de página (default: 20, max: 100)
            - status: Filtrar por estado (pending, sent, delivered, failed)
            - message_type: Filtrar por tipo
        """
        org = self.get_user_organization(request)

        # Parámetros de paginación
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)

        # Filtros
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

        # Calcular total y paginación
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size  # Redondeo hacia arriba

        # Calcular offset
        offset = (page - 1) * page_size

        # Obtener página actual
        messages = queryset[offset:offset + page_size]

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
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
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

        # Rendimiento por tipo de mensaje usando una sola query optimizada
        from django.db.models import Sum, Case, When, IntegerField

        performance_data = queryset.values('message_type').annotate(
            total=Count('id'),
            delivered=Count(Case(When(status='delivered', then=1))),
            failed=Count(Case(When(status='failed', then=1))),
            pending=Count(Case(When(status__in=['pending', 'sent'], then=1)))
        )

        # Convertir a diccionario para lookup rápido
        perf_dict = {item['message_type']: item for item in performance_data}

        # Crear lista de performance con etiquetas
        performance = []
        for msg_type, msg_label in WhatsAppMessage.MESSAGE_TYPES:
            if msg_type in perf_dict:
                data = perf_dict[msg_type]
                total = data['total']
                delivered = data['delivered']
                failed = data['failed']

                performance.append({
                    'type': msg_type,
                    'label': msg_label,
                    'total': total,
                    'delivered': delivered,
                    'failed': failed,
                    'pending': data['pending'],
                    'delivery_rate': round((delivered / total) * 100, 2) if total > 0 else 0,
                    'failure_rate': round((failed / total) * 100, 2) if total > 0 else 0
                })

        return Response({
            'period_days': days,
            'performance': performance,
            'organization': org.nombre if org else 'Todas'
        })
