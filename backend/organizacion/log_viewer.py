"""
Visor de logs para el panel de administración.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from organizacion.models_logs import ApplicationLog
from organizacion.models import Organizacion


@staff_member_required
def log_viewer(request):
    """
    Vista para ver logs de la aplicación con filtros y búsqueda.
    """

    # Obtener parámetros de filtro
    level = request.GET.get('level', '')
    org_id = request.GET.get('org_id', '')
    search = request.GET.get('search', '')
    logger_name = request.GET.get('logger', '')
    page = request.GET.get('page', 1)

    # Query base
    logs = ApplicationLog.objects.select_related('organizacion').all()

    # Filtrar por nivel
    if level:
        logs = logs.filter(level=level)

    # Filtrar por organización
    if org_id:
        logs = logs.filter(organizacion_id=org_id)

    # Filtrar por logger
    if logger_name:
        logs = logs.filter(logger_name__icontains=logger_name)

    # Búsqueda en mensaje
    if search:
        logs = logs.filter(
            Q(message__icontains=search) |
            Q(pathname__icontains=search) |
            Q(func_name__icontains=search) |
            Q(exc_info__icontains=search)
        )

    # Paginación
    paginator = Paginator(logs, 50)  # 50 logs por página
    page_obj = paginator.get_page(page)

    # Obtener lista de organizaciones para el filtro
    organizations = Organizacion.objects.all().order_by('nombre')

    # Obtener loggers únicos para el filtro
    unique_loggers = ApplicationLog.objects.values_list(
        'logger_name', flat=True
    ).distinct().order_by('logger_name')[:50]  # Limitar a 50 loggers más comunes

    # Estadísticas rápidas
    total_logs = logs.count()
    error_count = logs.filter(level__in=['ERROR', 'CRITICAL']).count()
    warning_count = logs.filter(level='WARNING').count()

    context = {
        'page_obj': page_obj,
        'organizations': organizations,
        'unique_loggers': unique_loggers,
        'level_choices': ApplicationLog.LEVEL_CHOICES,
        'filters': {
            'level': level,
            'org_id': org_id,
            'search': search,
            'logger_name': logger_name,
        },
        'stats': {
            'total': total_logs,
            'errors': error_count,
            'warnings': warning_count,
        }
    }

    return render(request, 'admin/log_viewer.html', context)
