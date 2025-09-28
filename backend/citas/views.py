from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from .models import Cita, Servicio, Horario, Colaborador, Bloqueo
from .serializers import CitaSerializer, ServicioSerializer, HorarioSerializer, ColaboradorSerializer, BloqueoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta, time
from django.http import HttpResponse
import csv
import pytz
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from usuarios.models import PerfilUsuario
from django.utils import timezone
from .services import get_available_slots, find_next_available_slots, check_appointment_availability
from .permissions import IsAdminOrSedeAdminOrReadOnly, IsOwnerOrAdminForCita
from .mixins import SedeFilteredMixin
from .pagination import StandardResultsSetPagination
from django.shortcuts import render
from django import forms
from organizacion.models import Sede
from django.db.models import Count, Case, When, IntegerField, Sum, Value, DecimalField, F, Prefetch
from django.db.models.functions import Coalesce
from .utils import send_appointment_email
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


class WelcomeView(APIView):
    """A simple view to confirm the API is running."""
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({
            "message": "Welcome to the Citas API!",
            "status": "ok"
        })

class ColaboradorViewSet(SedeFilteredMixin, viewsets.ModelViewSet):
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    permission_classes = [IsAdminOrSedeAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset().select_related('sede')
        now = timezone.now()
        # Exclude collaborators with an active block
        return queryset.exclude(
            bloqueos__fecha_inicio__lte=now,
            bloqueos__fecha_fin__gte=now
        )


class DisponibilidadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        fecha_str = request.query_params.get('fecha')
        recurso_id = request.query_params.get('recurso_id')
        sede_id = request.query_params.get('sede_id')
        servicio_ids_str = request.query_params.get('servicio_ids')

        if not fecha_str or not recurso_id or not sede_id or not servicio_ids_str:
            return Response({'error': _('Faltan parámetros de fecha, recurso, sede o servicios.')}, status=400)

        try:
            servicio_ids = [int(s_id) for s_id in servicio_ids_str.split(',')]
            slots = get_available_slots(recurso_id, fecha_str, servicio_ids)
            return Response({'disponibilidad': slots})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

class NextAvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        servicio_ids_str = request.query_params.get('servicio_ids')
        sede_id = request.query_params.get('sede_id')

        if not servicio_ids_str or not sede_id:
            return Response({'error': _('Faltan parámetros de servicios o sede.')}, status=400)

        try:
            servicio_ids = [int(s_id) for s_id in servicio_ids_str.split(',')]
            slots = find_next_available_slots(servicio_ids, sede_id)
            return Response(slots)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)


class ServicioViewSet(viewsets.ModelViewSet):
    serializer_class = ServicioSerializer
    permission_classes = [IsAdminOrSedeAdminOrReadOnly]

    def get_queryset(self):
        print(f"[ServicioViewSet] User: {self.request.user.username}")
        user = self.request.user
        sede_id = self.request.query_params.get('sede_id')

        if sede_id:
            # If a sede_id is provided, any user can see the services for that sede.
            # This is the primary way clients will fetch services.
            queryset = Servicio.all_objects.filter(sede_id=sede_id).select_related('sede')
            print(f"[ServicioViewSet] Sede_id provided. Queryset count: {queryset.count()}")
            return queryset

        # If no sede_id is provided, then we fall back to organization-level filtering.
        # This is typically for admin users browsing all services in their org.
        if user.is_staff: # is_staff includes superusers
            # For staff, use the default manager which filters by organization.
            queryset = Servicio.objects.select_related('sede')
            print(f"[ServicioViewSet] No sede_id. Staff user. Initial queryset count: {queryset.count()}")
        else:
            # Non-staff users MUST provide a sede_id to see any services.
            print("[ServicioViewSet] No sede_id. Non-staff user. Returning empty queryset.")
            queryset = Servicio.objects.none()
        
        return queryset

class BloqueoViewSet(SedeFilteredMixin, viewsets.ModelViewSet):
    """API endpoint for managing resource blocks."""
    queryset = Bloqueo.objects.select_related('colaborador__sede').all()
    serializer_class = BloqueoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSedeAdminOrReadOnly] # Only admins can block time

    def get_queryset(self):
        # Start with the parent's queryset (which applies sede filtering)
        queryset = super().get_queryset()

        start_date_str = self.request.query_params.get('start_date')
        end_date_str = self.request.query_params.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                # Filter blocks that overlap with the given range
                queryset = queryset.filter(
                    fecha_inicio__lt=end_date,
                    fecha_fin__gt=start_date
                )
            except (ValueError, TypeError):
                pass # Silently ignore invalid date formats
        
        return queryset


class CitaViewSet(viewsets.ModelViewSet):
    queryset = Cita.objects.all().order_by('fecha')
    serializer_class = CitaSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdminForCita]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            # Staff users' queryset should be filtered by their organization.
            # The default manager 'objects' handles this automatically.
            base_queryset = Cita.objects.select_related('user', 'sede').prefetch_related('servicios', 'colaboradores')
            queryset = base_queryset.all()
        else:
            # For non-staff users (clients, sede admins), we start with all objects
            # and then apply specific permissions.
            base_queryset = Cita.all_objects.select_related('user', 'sede').prefetch_related('servicios', 'colaboradores')
            try:
                perfil = user.perfil
                if perfil.sedes_administradas.exists():
                    # Sede admins see appointments only from the sedes they manage
                    queryset = base_queryset.filter(sede__in=perfil.sedes_administradas.all())
                else:
                    # Regular users see only their own appointments
                    queryset = base_queryset.filter(user=user)
            except PerfilUsuario.DoesNotExist:
                # Users without a profile can only see their own appointments
                queryset = base_queryset.filter(user=user)

        # Apply search filter if provided
        search_term = self.request.query_params.get('search', None)
        if search_term:
            queryset = queryset.filter(nombre__icontains=search_term)

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        # The filter for 'Pendiente' and 'Confirmada' for non-staff was removed
        # to allow users to see their cancelled appointments as well.
        # If you want to hide them, you can add the filter back.

        return queryset.order_by('fecha')

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        recurso_id = data.get('recurso_id') or data.get('colaborador_id')
        if recurso_id and 'colaboradores_ids' not in data:
            data['colaboradores_ids'] = [recurso_id]
        
        # Ensure servicios_ids is a list of integers
        servicios_ids = data.get('servicios_ids')
        if isinstance(servicios_ids, str):
            data['servicios_ids'] = [int(s_id) for s_id in servicios_ids.split(',')]
        elif not isinstance(servicios_ids, list):
            data['servicios_ids'] = [] # Default to empty list if not provided or invalid format

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user

        # Check if the user is a sede administrator
        is_sede_admin = False
        if not user.is_staff:
            try:
                is_sede_admin = user.perfil.is_sede_admin and user.perfil.sedes_administradas.exists()
            except (AttributeError, PerfilUsuario.DoesNotExist):
                pass

        # Sede admins are not allowed to create appointments for users via this endpoint
        if is_sede_admin:
            raise PermissionDenied(_("Los administradores de sede no pueden crear citas para usuarios desde esta vista."))
        
        # For regular users or staff, associate the appointment with the logged-in user.
        # The 'sede' is already handled by the serializer's 'sede_id' field.
        cita = serializer.save(user=user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.estado == 'Cancelada':
            raise PermissionDenied(_("No se puede modificar una cita cancelada."))
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        original_instance = self.get_object()
        old_fecha = original_instance.fecha

        if original_instance.estado == 'Cancelada':
            raise PermissionDenied(_("No se puede modificar una cita cancelada."))
        
        response = super().partial_update(request, *args, **kwargs)

        # After a successful update, check if the date has changed to send a notification
        updated_instance = self.get_object()
        if updated_instance.fecha != old_fecha:
            send_appointment_email.delay(
                appointment_id=updated_instance.id,
                subject=f"Reprogramación de Cita: {', '.join([s.nombre for s in updated_instance.servicios.all()])}",
                template_name='appointment_reschedule'
            )

        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Store date before changing status, for the email
        original_fecha = instance.fecha
        instance.estado = 'Cancelada'
        instance.save()

        # Pass serializable data to the Celery task
        context = {'original_fecha': original_fecha.isoformat()}

        send_appointment_email.delay(
            appointment_id=instance.id,
            subject=f"Cancelación de Cita: {', '.join([s.nombre for s in instance.servicios.all()])}",
            template_name='appointment_cancellation',
            context=context
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        cita = self.get_object()

        if cita.estado == 'Confirmada':
            return Response({'status': 'cita ya estaba confirmada'})

        if cita.estado == 'Pendiente':
            cita.estado = 'Confirmada'
            cita.confirmado = True
            cita.save()

            send_appointment_email.delay(
                appointment_id=cita.id,
                subject=f"Tu cita ha sido confirmada: {', '.join([s.nombre for s in cita.servicios.all()])}",
                template_name='appointment_confirmation'
            )

            return Response({'status': 'cita confirmada'})
        else:
            return Response({'status': f'la cita no se puede confirmar porque su estado es {cita.estado}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def all(self, request, *args, **kwargs):
        """
        Returns appointments without pagination, for use in components like calendars.
        Accepts start_date and end_date query parameters to filter by a date range.
        """
        queryset = self.filter_queryset(self.get_queryset())

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                queryset = queryset.filter(fecha__range=[start_date, end_date])
            except (ValueError, TypeError):
                pass # Silently ignore invalid date formats

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # --- Refactor: Reuse the queryset logic from CitaViewSet ---
        # This avoids repeating permission logic and keeps the code DRY.
        cita_viewset = CitaViewSet()
        cita_viewset.request = request # Provide the request context to the viewset
        base_queryset = cita_viewset.get_queryset()
        # -----------------------------------------------------------

        # Determine if the user is an admin (staff or sede admin)
        is_admin_user = user.is_staff
        if not is_admin_user:
            is_in_admin_group = user.groups.filter(name='SedeAdmin').exists()
            has_sedes_administradas = hasattr(user, 'perfil') and user.perfil and user.perfil.sedes_administradas.exists()
            is_admin_user = is_in_admin_group or has_sedes_administradas

        # Admin/Staff specific stats
        if is_admin_user:
            citas_hoy = base_queryset.filter(fecha__date=today).count()
            pendientes_confirmacion = base_queryset.filter(estado='Pendiente').count()
            
            start_of_month = today.replace(day=1)
            ingresos_mes = base_queryset.filter(
                estado='Asistio',
                fecha__gte=start_of_month
            ).aggregate(total=Sum(F('servicios__precio')))['total'] or 0

            proximas_citas = base_queryset.filter(
                fecha__gte=timezone.now(),
                estado__in=['Pendiente', 'Confirmada']
            ).order_by('fecha')[:5]

            summary = { 'citas_hoy': citas_hoy, 'pendientes_confirmacion': pendientes_confirmacion, 'ingresos_mes': ingresos_mes, 'proximas_citas': CitaSerializer(proximas_citas, many=True).data }
        else: # Regular user stats
            proxima_cita = base_queryset.filter( fecha__gte=timezone.now(), estado__in=['Pendiente', 'Confirmada'] ).order_by('fecha').first()
            summary = { 'proxima_cita': CitaSerializer(proxima_cita).data if proxima_cita else None, }
            
        return Response(summary)

class HorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.select_related('colaborador__sede').all()
    serializer_class = HorarioSerializer
    permission_classes = [IsAdminOrSedeAdminOrReadOnly]
    
    def get_queryset(self):
        # Use the custom manager which automatically filters by organization
        user = self.request.user
        if user.is_staff:
            return super().get_queryset()
        
        try:
            perfil = user.perfil
            if perfil.sedes_administradas.exists():
                # Corrected filter: Horario is linked to Sede via Colaborador
                return super().get_queryset().filter(colaborador__sede__in=perfil.sedes_administradas.all())
        except PerfilUsuario.DoesNotExist:
            pass
        
        # Default to empty queryset if no permissions match
        return Horario.objects.none()

class AppointmentReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        servicio_ids_str = request.query_params.get('servicio_ids')
        colaborador_id = request.query_params.get('colaborador_id') or request.query_params.get('recurso_id')
        estado = request.query_params.get('estado')
        report_format = request.query_params.get('export', 'json')

        if not start_date_str or not end_date_str:
            return Response({"error": _("Please provide start_date and end_date query parameters (YYYY-MM-DD).")}, status=400)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": _("Invalid date format. Please use YYYY-MM-DD.")}, status=400)

        end_date = end_date + timedelta(days=1)

        user = request.user
        if user.is_superuser:
            base_queryset = Cita.all_objects.all()
        elif user.is_staff:
            try:
                organizacion = user.perfil.organizacion
                if organizacion:
                    base_queryset = Cita.all_objects.filter(sede__organizacion=organizacion)
                else:
                    base_queryset = Cita.objects.none()
            except (AttributeError, PerfilUsuario.DoesNotExist):
                base_queryset = Cita.objects.none()
        else:  # Non-staff
            try:
                perfil = user.perfil
                if perfil.sedes_administradas.exists():
                    base_queryset = Cita.all_objects.filter(sede__in=perfil.sedes_administradas.all())
                else:
                    base_queryset = Cita.all_objects.filter(user=user)
            except (AttributeError, PerfilUsuario.DoesNotExist):
                base_queryset = Cita.all_objects.filter(user=user)

        queryset = base_queryset.filter(fecha__range=(start_date, end_date))

        if servicio_ids_str:
            servicio_ids = [int(s_id) for s_id in servicio_ids_str.split(',') if s_id.isdigit()]
            if servicio_ids:
                queryset = queryset.filter(servicios__id__in=servicio_ids)
        if colaborador_id:
            queryset = queryset.filter(colaboradores__id=colaborador_id)
        if estado:
            queryset = queryset.filter(estado=estado)

        if report_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="appointment_report.csv"'

            writer = csv.writer(response)
            writer.writerow([_('ID'), _('Nombre Cliente'), _('Fecha'), _('Servicios'), _('Sede'), _('Estado'), _('Confirmado'), _('Usuario')])

            user_timezone_str = 'UTC'
            try:
                user_timezone_str = request.user.perfil.timezone
            except (AttributeError, PerfilUsuario.DoesNotExist):
                pass
            user_timezone = pytz.timezone(user_timezone_str)

            servicios_prefetch = Prefetch('servicios', queryset=Servicio.all_objects.all())
            colaboradores_prefetch = Prefetch('colaboradores', queryset=Colaborador.all_objects.all())

            for cita in queryset.select_related('user', 'sede').prefetch_related(servicios_prefetch, colaboradores_prefetch):
                local_fecha = cita.fecha.astimezone(user_timezone)
                writer.writerow([
                    cita.id, cita.nombre, local_fecha.strftime('%Y-%m-%d %H:%M'),
                    ", ".join([s.nombre for s in cita.servicios.all()]),
                    cita.sede.nombre, cita.estado,
                    _('Sí') if cita.confirmado else _('No'),
                    cita.user.username if cita.user else _('N/A')
                ])
            return response
        else:
            appointments_by_status = queryset.values('estado').annotate(count=Count('id'))
            status_counts = {item['estado']: item['count'] for item in appointments_by_status}
            report_list = [
                {'estado': choice[0], 'count': status_counts.get(choice[0], 0)}
                for choice in Cita.ESTADO_CHOICES
            ]
            total_revenue = queryset.filter(estado='Asistio').aggregate(total=Sum(F('servicios__precio')))['total'] or 0
            return Response({'report': report_list, 'total_revenue': total_revenue})

class SedeReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        administered_sedes = None

        if user.is_superuser:
            administered_sedes = Sede.all_objects.all()
        else:
            try:
                perfil = user.perfil
                if perfil.sedes_administradas.exists():
                    administered_sedes = perfil.sedes_administradas.all()
                elif user.is_staff and perfil.organizacion:
                    administered_sedes = Sede.all_objects.filter(organizacion=perfil.organizacion)
            except (AttributeError, PerfilUsuario.DoesNotExist):
                pass

        if administered_sedes is None:
            raise PermissionDenied(_("You do not have permission to access this report."))

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        specific_sede_id = request.query_params.get('sede_id')
        servicio_ids_str = request.query_params.get('servicio_ids')
        colaborador_id = request.query_params.get('colaborador_id') or request.query_params.get('recurso_id')
        estado = request.query_params.get('estado')

        if not start_date_str or not end_date_str:
            return Response({"error": _("Please provide start_date and end_date query parameters (YYYY-MM-DD).")}, status=400)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": _("Invalid date format. Please use YYYY-MM-DD.")}, status=400)

        end_date = end_date + timedelta(days=1)

        base_queryset = Cita.all_objects.filter(
            sede__in=administered_sedes,
            fecha__range=(start_date, end_date)
        )

        if specific_sede_id:
            if not administered_sedes.filter(id=specific_sede_id).exists():
                raise PermissionDenied(_("You do not administer the specified location."))
            base_queryset = base_queryset.filter(sede_id=specific_sede_id)

        if servicio_ids_str:
            servicio_ids = [int(s_id) for s_id in servicio_ids_str.split(',') if s_id.isdigit()]
            if servicio_ids:
                base_queryset = base_queryset.filter(servicios__id__in=servicio_ids)
        if colaborador_id:
            base_queryset = base_queryset.filter(colaboradores__id=colaborador_id)

        total_revenue = base_queryset.filter(estado='Asistio').aggregate(total=Sum(F('servicios__precio')))['total'] or 0

        queryset = base_queryset
        if estado:
            queryset = queryset.filter(estado=estado)

        report_data = queryset.values('sede__id', 'sede__nombre').annotate(
            total_citas=Count('id'),
            pendientes=Count(Case(When(estado='Pendiente', then=1), output_field=IntegerField())),
            confirmadas=Count(Case(When(estado='Confirmada', then=1), output_field=IntegerField())),
            canceladas=Count(Case(When(estado='Cancelada', then=1), output_field=IntegerField())),
            asistio=Count(Case(When(estado='Asistio', then=1), output_field=IntegerField())),
            no_asistio=Count(Case(When(estado='No Asistio', then=1), output_field=IntegerField())),
            ingresos=Sum(
                Case(
                    When(estado='Asistio', then=F('servicios__precio')),
                    default=Value(0),
                    output_field=DecimalField()
                )
            )
        ).order_by('sede__nombre')

        response_data = []
        for item in report_data:
            response_data.append({
                'sede_id': item['sede__id'],
                'sede_nombre': item['sede__nombre'],
                'total_citas': item['total_citas'],
                'estados': [
                    {'estado': 'Pendiente', 'count': item['pendientes']},
                    {'estado': 'Confirmada', 'count': item['confirmadas']},
                    {'estado': 'Cancelada', 'count': item['canceladas']},
                    {'estado': 'Asistio', 'count': item['asistio']},
                    {'estado': 'No Asistio', 'count': item['no_asistio']},
                ],
                'ingresos': item['ingresos'] or 0
            })
        
        services_summary = queryset.values('servicios__nombre').annotate(count=Count('servicios__nombre')).order_by('servicios__nombre')
        resources_summary = queryset.values('colaboradores__nombre').annotate(count=Count('colaboradores__nombre')).order_by('colaboradores__nombre')

        final_response = {
            'reporte_por_sede': response_data,
            'resumen_servicios': list(services_summary),
            'resumen_recursos': list(resources_summary),
            'ingresos_totales': total_revenue,
        }

        return Response(final_response)

class ReportForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label=_("Fecha de Inicio"))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label=_("Fecha de Fin"))
    servicios = forms.ModelMultipleChoiceField(queryset=Servicio.objects.none(), required=False, label=_("Servicios"))
    colaborador = forms.ModelChoiceField(queryset=Colaborador.objects.none(), required=False, label=_("Colaborador"))
    estado = forms.ChoiceField(choices=[('', _('Todos'))] + Cita.ESTADO_CHOICES, required=False, label=_("Estado"))
    report_format = forms.ChoiceField(choices=[('json', _('JSON (Resumen)')), ('csv', _('CSV (Detallado)'))], label=_("Formato de Reporte"))

    def __init__(self, *args, **kwargs):
        initial_queryset = kwargs.pop('initial_queryset', None)
        super().__init__(*args, **kwargs)
        if initial_queryset:
            self.fields['servicios'].queryset = initial_queryset.get('servicios', Servicio.objects.none())
            self.fields['colaborador'].queryset = initial_queryset.get('colaborador', Colaborador.objects.none())

def admin_report_view(request):
    # Custom permission check for admin_report_view
    if not request.user.is_authenticated:
        raise PermissionDenied(_("You must be logged in to access this report."))

    has_permission = False
    if request.user.is_staff:
        has_permission = True
    else:
        try:
            perfil = request.user.perfil
            if perfil.sedes_administradas.exists():
                has_permission = True
        except PerfilUsuario.DoesNotExist:
            pass

    if not has_permission:
        raise PermissionDenied(_("You do not have permission to access this report."))

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            servicios = form.cleaned_data['servicios']
            colaborador = form.cleaned_data['colaborador']
            estado = form.cleaned_data['estado']
            report_format = form.cleaned_data['report_format']

            # Re-use the logic from AppointmentReportView's get method
            # Construct a dummy request object for AppointmentReportView
            from django.test import RequestFactory
            factory = RequestFactory()
            dummy_request = factory.get('/dummy-path/')
            dummy_request.user = request.user # Pass the actual user
            dummy_request.query_params = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'export': report_format # Corrected from 'format' to 'export'
            }
            if servicios:
                dummy_request.query_params['servicio_ids'] = ",".join([str(s.id) for s in servicios])
            if colaborador:
                dummy_request.query_params['colaborador_id'] = colaborador.id
            if estado:
                dummy_request.query_params['estado'] = estado

            response = AppointmentReportView.as_view()(dummy_request)

            if isinstance(response, HttpResponse) and response.get('Content-Type') == 'text/csv':
                return response
            else:
                
                return render(request, 'admin/citas/report_results.html', {'report_data': response.data})
    else:
        form = ReportForm()
    
    return render(request, 'admin/citas/report_form.html', {'form': form})

class IsColaboradorUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Colaborador').exists()

class ColaboradorCitaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CitaSerializer
    permission_classes = [IsAuthenticated, IsColaboradorUser]

    def get_queryset(self):
        user = self.request.user
        try:
            colaborador = Colaborador.objects.get(usuario=user)
            return Cita.objects.filter(colaboradores=colaborador).order_by('fecha')
        except Colaborador.DoesNotExist:
            return Cita.objects.none()

    @action(detail=True, methods=['post'])
    def marcar_asistencia(self, request, pk=None):
        cita = self.get_object()
        if cita.estado == 'Cancelada':
            raise PermissionDenied(_('No se puede cambiar el estado de una cita cancelada.'))
        asistio = request.data.get('asistio')
        comentario = request.data.get('comentario')

        if asistio is None:
            return Response({'error': 'El campo "asistio" es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        if asistio:
            cita.estado = 'Asistio'
        else:
            cita.estado = 'No Asistio'
        
        if comentario:
            cita.comentario = comentario
        
        cita.save()
        return Response(CitaSerializer(cita).data)

class IsRecursoUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Recurso').exists()

class RecursoCitaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CitaSerializer
    permission_classes = [IsAuthenticated, IsRecursoUser]

    def get_queryset(self):
        user = self.request.user
        try:
            recurso = Colaborador.objects.get(usuario=user)
            return Cita.objects.filter(colaboradores=recurso).order_by('fecha')
        except Colaborador.DoesNotExist:
            # Log a warning or return an empty queryset gracefully
            print(f"WARNING: No Colaborador instance found for user: {user.username}")
            return Cita.objects.none()

    @action(detail=True, methods=['post'])
    def marcar_asistencia(self, request, pk=None):
        cita = self.get_object()
        if cita.estado == 'Cancelada':
            raise PermissionDenied(_('No se puede cambiar el estado de una cita cancelada.'))
        asistio = request.data.get('asistio')
        comentario = request.data.get('comentario')

        if asistio is None:
            return Response({'error': 'El campo "asistio" es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        if asistio:
            cita.estado = 'Asistio'
        else:
            cita.estado = 'No Asistio'
        
        if comentario:
            cita.comentario = comentario
        
        cita.save()
        return Response(CitaSerializer(cita).data)

class RecursoViewSet(viewsets.ModelViewSet):
    serializer_class = ColaboradorSerializer
    permission_classes = [IsAdminOrSedeAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        sede_id = self.request.query_params.get('sede_id')

        if sede_id:
            # If a sede_id is provided, any user can see the resources for that sede.
            queryset = Colaborador.all_objects.filter(sede_id=sede_id).select_related('sede')
        elif user.is_staff:
            # For staff without a sede_id, use the default manager to filter by organization.
            queryset = Colaborador.objects.select_related('sede')
        else:
            # Non-staff users MUST provide a sede_id to see any resources.
            queryset = Colaborador.objects.none()

        # Exclude collaborators with an active block
        now = timezone.now()
        return queryset.exclude(
            bloqueos__fecha_inicio__lte=now,
            bloqueos__fecha_fin__gte=now
        )