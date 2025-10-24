from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q, F, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from citas.models import Cita, Colaborador
from .permissions import IsAdminOrSedeAdmin

# MULTI-TENANT: Import helper for profile management
from usuarios.utils import get_perfil_or_first


class FinancialSummaryView(APIView):
    """
    Endpoint para obtener resumen financiero de citas.

    GET /api/reports/financial-summary/

    Query Parameters:
    - start_date (opcional): Fecha inicio en formato YYYY-MM-DD
    - end_date (opcional): Fecha fin en formato YYYY-MM-DD

    Si no se proporcionan fechas, usa los últimos 30 días por defecto.

    Permisos:
    - IsAdminOrSedeAdmin: Solo superusuarios y administradores de sede/organización

    Multi-tenancy:
    - Superusuarios ven datos de todas las organizaciones
    - Administradores ven solo datos de su organización
    """

    permission_classes = [IsAuthenticated, IsAdminOrSedeAdmin]

    def get(self, request, *args, **kwargs):
        # 1. Obtener parámetros de fecha
        start_date, end_date = self._get_date_range(request)

        # 2. Aplicar filtros de multi-tenancy
        queryset = self._apply_organization_filter(request.user)

        # 3. Filtrar por rango de fechas
        queryset = queryset.filter(fecha__gte=start_date, fecha__lte=end_date)

        # 4. Filtrar por colaborador específico (si se proporciona)
        colaborador_id = request.query_params.get('colaborador_id')
        if colaborador_id:
            try:
                queryset = queryset.filter(colaboradores__id=int(colaborador_id))
            except (ValueError, TypeError):
                # Si el ID no es válido, ignorar el filtro
                pass

        # 4. OPTIMIZACIÓN: Calcular todas las métricas principales en UNA SOLA QUERY
        metrics = queryset.aggregate(
            # Ingresos realizados (citas con estado 'Asistio' o 'Asistió')
            ingresos_realizados=Coalesce(
                Sum(
                    'servicios__precio',
                    filter=Q(estado__in=['Asistio', 'Asistió'])
                ),
                Value(0),
                output_field=DecimalField()
            ),

            # Ingresos proyectados (citas Pendiente o Confirmada)
            ingresos_proyectados=Coalesce(
                Sum(
                    'servicios__precio',
                    filter=Q(estado__in=['Pendiente', 'Confirmada'])
                ),
                Value(0),
                output_field=DecimalField()
            ),

            # Ingresos perdidos (citas No Asistio o No Asistió)
            ingresos_perdidos=Coalesce(
                Sum(
                    'servicios__precio',
                    filter=Q(estado__in=['No Asistio', 'No Asistió'])
                ),
                Value(0),
                output_field=DecimalField()
            ),

            # Ingresos cancelados (citas Cancelada)
            ingresos_cancelados=Coalesce(
                Sum(
                    'servicios__precio',
                    filter=Q(estado='Cancelada')
                ),
                Value(0),
                output_field=DecimalField()
            ),

            # Conteo de citas por estado
            total_citas=Count('id'),
            citas_asistio=Count('id', filter=Q(estado__in=['Asistio', 'Asistió'])),
            citas_pendiente=Count('id', filter=Q(estado='Pendiente')),
            citas_confirmada=Count('id', filter=Q(estado='Confirmada')),
            citas_no_asistio=Count('id', filter=Q(estado__in=['No Asistio', 'No Asistió'])),
            citas_cancelada=Count('id', filter=Q(estado='Cancelada')),
        )

        # 5. Calcular ingresos por servicio (solo citas asistidas)
        ingresos_por_servicio = queryset.filter(
            estado__in=['Asistio', 'Asistió']
        ).values(
            'servicios__nombre'
        ).annotate(
            total_ingresos=Sum('servicios__precio'),
            cantidad_citas=Count('id')
        ).order_by('-total_ingresos')[:10]  # Top 10 servicios

        # 6. Preparar respuesta
        response_data = {
            'periodo': {
                'inicio': start_date.strftime('%Y-%m-%d'),
                'fin': end_date.strftime('%Y-%m-%d')
            },
            'metricas_principales': {
                'ingresos_realizados': float(metrics['ingresos_realizados'] or 0),
                'ingresos_proyectados': float(metrics['ingresos_proyectados'] or 0),
                'ingresos_perdidos': float(metrics['ingresos_perdidos'] or 0),
                'ingresos_cancelados': float(metrics['ingresos_cancelados'] or 0),
                'total_ingresos': float(
                    (metrics['ingresos_realizados'] or 0) +
                    (metrics['ingresos_proyectados'] or 0)
                ),
            },
            'citas_por_estado': [
                {
                    'estado': 'Asistio',
                    'cantidad': metrics['citas_asistio'],
                    'porcentaje': round(
                        (metrics['citas_asistio'] / metrics['total_citas'] * 100)
                        if metrics['total_citas'] > 0 else 0,
                        2
                    )
                },
                {
                    'estado': 'Pendiente',
                    'cantidad': metrics['citas_pendiente'],
                    'porcentaje': round(
                        (metrics['citas_pendiente'] / metrics['total_citas'] * 100)
                        if metrics['total_citas'] > 0 else 0,
                        2
                    )
                },
                {
                    'estado': 'Confirmada',
                    'cantidad': metrics['citas_confirmada'],
                    'porcentaje': round(
                        (metrics['citas_confirmada'] / metrics['total_citas'] * 100)
                        if metrics['total_citas'] > 0 else 0,
                        2
                    )
                },
                {
                    'estado': 'No Asistio',
                    'cantidad': metrics['citas_no_asistio'],
                    'porcentaje': round(
                        (metrics['citas_no_asistio'] / metrics['total_citas'] * 100)
                        if metrics['total_citas'] > 0 else 0,
                        2
                    )
                },
                {
                    'estado': 'Cancelada',
                    'cantidad': metrics['citas_cancelada'],
                    'porcentaje': round(
                        (metrics['citas_cancelada'] / metrics['total_citas'] * 100)
                        if metrics['total_citas'] > 0 else 0,
                        2
                    )
                },
            ],
            'ingresos_por_servicio': [
                {
                    'servicio': item['servicios__nombre'] or 'Sin servicio',
                    'total_ingresos': float(item['total_ingresos'] or 0),
                    'cantidad_citas': item['cantidad_citas']
                }
                for item in ingresos_por_servicio
            ],
            'total_citas': metrics['total_citas']
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _get_date_range(self, request):
        """
        Obtiene el rango de fechas desde los query params.
        Por defecto: últimos 30 días.
        """
        try:
            # Intentar obtener start_date
            start_date_str = request.query_params.get('start_date')
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)
            else:
                # Por defecto: 30 días atrás
                start_date = timezone.now() - timedelta(days=30)

            # Intentar obtener end_date
            end_date_str = request.query_params.get('end_date')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date)
                # Ajustar a fin del día
                end_date = end_date.replace(hour=23, minute=59, second=59)
            else:
                # Por defecto: hoy
                end_date = timezone.now()

        except ValueError:
            # Si hay error en el formato de fecha, usar valores por defecto
            start_date = timezone.now() - timedelta(days=30)
            end_date = timezone.now()

        return start_date, end_date

    def _apply_organization_filter(self, user):
        """
        Aplica filtros de multi-tenancy según el tipo de usuario.

        - Superusuarios: ven todas las citas
        - Administradores: ven solo citas de su organización
        """
        # Obtener queryset base usando all_objects para bypass de OrganizacionManager
        queryset = Cita.all_objects.select_related(
            'sede',
            'sede__organizacion'
        ).prefetch_related(
            'servicios'
        )

        # Superusuarios ven todo
        if user.is_superuser:
            return queryset

        # Intentar obtener organización del usuario
        user_org = None

        # 1. Buscar en perfiles (plural) usando helper
        perfil = get_perfil_or_first(user)
        if perfil and perfil.organizacion:
            user_org = perfil.organizacion

        # 2. Si no tiene organización en perfil, buscar en Colaborador
        if not user_org:
            try:
                colaborador = Colaborador.all_objects.select_related(
                    'sede__organizacion'
                ).get(usuario=user)
                if colaborador.sede and colaborador.sede.organizacion:
                    user_org = colaborador.sede.organizacion
            except Colaborador.DoesNotExist:
                pass

        # Si se encontró organización, filtrar por ella
        if user_org:
            queryset = queryset.filter(sede__organizacion=user_org)
        else:
            # Si no tiene organización, retornar queryset vacío
            queryset = queryset.none()

        return queryset
