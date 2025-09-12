from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from .models import Cita, Servicio, Horario, Colaborador, Bloqueo
from .serializers import CitaSerializer, ServicioSerializer, HorarioSerializer, ColaboradorSerializer, BloqueoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta, time
from django.http import HttpResponse
import csv
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
from django.db.models import Count, Case, When, IntegerField, Sum, Value, DecimalField,F
from django.db.models.functions import Coalesce
from .utils import send_appointment_email


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


class DisponibilidadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        fecha_str = request.query_params.get('fecha')
        recurso_id = request.query_params.get('recurso_id')
        sede_id = request.query_params.get('sede_id')

        if not fecha_str or not recurso_id or not sede_id:
            return Response({'error': _('Faltan parámetros de fecha, recurso o sede.')}, status=400)

        try:
            slots = get_available_slots(recurso_id, fecha_str)
            return Response({'disponibilidad': slots})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

class NextAvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        servicio_id = request.query_params.get('servicio_id')
        sede_id = request.query_params.get('sede_id')

        if not servicio_id or not sede_id:
            return Response({'error': _('Faltan parámetros de servicio o sede.')}, status=400)

        try:
            slots = find_next_available_slots(servicio_id, sede_id)
            return Response(slots)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)


class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    permission_classes = [IsAdminOrSedeAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        sede_id = self.request.query_params.get('sede_id')

        if sede_id:
            return queryset.filter(sede_id=sede_id)

        if user.is_staff:
            return queryset

        if hasattr(user, 'perfil') and user.perfil and user.perfil.sedes_administradas.exists():
            return queryset.filter(sede__in=user.perfil.sedes_administradas.all())
        
        return queryset.none()

class BloqueoViewSet(SedeFilteredMixin, viewsets.ModelViewSet):
    """API endpoint for managing resource blocks."""
    queryset = Bloqueo.objects.all()
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

        # Refactored permission-based filtering for clarity and correctness
        if user.is_staff:
            # Staff users can see all appointments across all sedes
            queryset = Cita.objects.all()
        else:
            try:
                perfil = user.perfil
                if perfil.sedes_administradas.exists():
                    # Sede admins see appointments only from the sedes they manage
                    queryset = Cita.objects.filter(sede__in=perfil.sedes_administradas.all())
                else:
                    # Regular users see only their own appointments
                    queryset = Cita.objects.filter(user=user)
            except PerfilUsuario.DoesNotExist:
                # Users without a profile can only see their own appointments
                queryset = Cita.objects.filter(user=user)

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
        serializer.save(user=user)

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
            send_appointment_email(
                appointment=updated_instance,
                subject=f"Reprogramación de Cita: {updated_instance.servicio.nombre}",
                template_name='appointment_reschedule'
            )

        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Store date before changing status, for the email
        original_fecha = instance.fecha
        instance.estado = 'Cancelada'
        instance.save()

        send_appointment_email(
            appointment=instance,
            subject=f"Cancelación de Cita: {instance.servicio.nombre}",
            template_name='appointment_cancellation',
            context={'original_fecha': original_fecha}
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

            send_appointment_email(
                appointment=cita,
                subject=f"Tu cita ha sido confirmada: {cita.servicio.nombre}",
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
        if not is_admin_user and hasattr(user, 'perfil') and user.perfil:
            is_admin_user = user.perfil.sedes_administradas.exists()

        # Admin/Staff specific stats
        if is_admin_user:
            citas_hoy = base_queryset.filter(fecha__date=today).count()
            pendientes_confirmacion = base_queryset.filter(estado='Pendiente').count()
            
            start_of_month = today.replace(day=1)
            ingresos_mes = base_queryset.filter(
                estado='Asistio',
                fecha__gte=start_of_month
            ).aggregate(total=Sum('servicio__precio'))['total'] or 0

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
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    permission_classes = [IsAdminOrSedeAdminOrReadOnly]
    
    def get_queryset(self):
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
        servicio_id = request.query_params.get('servicio_id')
        colaborador_id = request.query_params.get('colaborador_id')
        estado = request.query_params.get('estado')
        report_format = request.query_params.get('export', 'json') # Use 'export' to avoid conflict with DRF's 'format'

        if not start_date_str or not end_date_str:
            return Response({"error": _("Please provide start_date and end_date query parameters (YYYY-MM-DD).")}, status=400)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": _("Invalid date format. Please use YYYY-MM-DD.")}, status=400)

        # Ensure end_date includes the whole day
        end_date = end_date + timedelta(days=1)

        # **CRITICAL SECURITY FIX**: Filter initial queryset based on user permissions
        user = request.user
        if user.is_staff:
            base_queryset = Cita.objects.all()
        else:
            try:
                perfil = user.perfil
                if perfil.sedes_administradas.exists():
                    base_queryset = Cita.objects.filter(sede__in=perfil.sedes_administradas.all())
                else:
                    base_queryset = Cita.objects.filter(user=user)
            except PerfilUsuario.DoesNotExist:
                base_queryset = Cita.objects.filter(user=user)

        # Apply date and other filters to the permission-filtered queryset
        queryset = base_queryset.filter(
            fecha__range=(start_date, end_date)
        )

        if servicio_id:
            queryset = queryset.filter(servicio_id=servicio_id)
        if colaborador_id:
            queryset = queryset.filter(colaboradores__id=colaborador_id)
        if estado:
            queryset = queryset.filter(estado=estado)

        if report_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="appointment_report.csv"'

            writer = csv.writer(response)
            # Write header
            writer.writerow([_('ID'), _('Nombre Cliente'), _('Fecha'), _('Servicio'), _('Sede'), _('Estado'), _('Confirmado'), _('Usuario')])

            # Write data rows
            # Add 'sede' to select_related for performance optimization
            for cita in queryset.select_related('servicio', 'user', 'sede').prefetch_related('colaboradores'):
                writer.writerow([
                    cita.id,
                    cita.nombre,
                    cita.fecha.strftime('%Y-%m-%d %H:%M'),
                    cita.servicio.nombre,
                    cita.sede.nombre,
                    cita.estado,
                    _('Sí') if cita.confirmado else _('No'),
                    cita.user.username if cita.user else _('N/A')
                ])
            return response
        else: # Default to JSON format
            appointments_data = queryset.values('estado').annotate(count=Count('estado'))

            report = {item['estado']: item['count'] for item in appointments_data}
            
            # Add counts for all possible states, even if 0
            all_states = ['Pendiente', 'Confirmada', 'Cancelada', 'Asistio', 'No Asistio']
            for state in all_states:
                if state not in report:
                    report[state] = 0

            return Response(report)

class SedeReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Permission Check: Only staff or sede admins can access
        if not user.is_staff:
            try:
                if not user.perfil.sedes_administradas.exists():
                    raise PermissionDenied(_("You do not have permission to access this report."))
            except (AttributeError, PerfilUsuario.DoesNotExist):
                raise PermissionDenied(_("You do not have permission to access this report."))

        # Determine which sedes the user can report on
        if user.is_staff:
            administered_sedes = Sede.objects.all()
        else:
            administered_sedes = user.perfil.sedes_administradas.all()

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        specific_sede_id = request.query_params.get('sede_id')
        servicio_id = request.query_params.get('servicio_id')
        colaborador_id = request.query_params.get('colaborador_id')
        estado = request.query_params.get('estado')

        if not start_date_str or not end_date_str:
            return Response({"error": _("Please provide start_date and end_date query parameters (YYYY-MM-DD).")}, status=400)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": _("Invalid date format. Please use YYYY-MM-DD.")}, status=400)

        # Ensure end_date includes the whole day
        end_date = end_date + timedelta(days=1)

        # Start with a base queryset filtered by user permissions and date range
        base_queryset = Cita.objects.filter(
            sede__in=administered_sedes,
            fecha__range=(start_date, end_date)
        )

        # Apply specific sede filter if provided and administered by the user
        if specific_sede_id:
            try:
                # Ensure the requested sede is one the user administers
                if not administered_sedes.filter(id=specific_sede_id).exists():
                    raise PermissionDenied(_("You do not administer the specified location."))
                base_queryset = base_queryset.filter(sede_id=specific_sede_id)
            except Sede.DoesNotExist:
                return Response({"error": _("Specified location not found.")}, status=404)

        # Apply optional filters for service and resource to the base queryset
        if servicio_id:
            base_queryset = base_queryset.filter(servicio_id=servicio_id)
        if colaborador_id:
            base_queryset = base_queryset.filter(colaboradores__id=colaborador_id)

        # Calculate total revenue from the base queryset, before applying the status filter.
        # This ensures the total revenue reflects all attended appointments in the selected scope,
        # regardless of the status filter applied to the detailed view.
        total_revenue = base_queryset.filter(estado='Asistio').aggregate(total=Sum('servicio__precio'))['total'] or 0

        # Now, apply the optional estado filter to get the final queryset for the detailed report
        queryset = base_queryset
        if estado:
            queryset = queryset.filter(estado=estado)

        # Aggregate data per sede
        report_data = queryset.values('sede__id', 'sede__nombre').annotate(
            total_citas=Count('id'),
            pendientes=Count(Case(When(estado='Pendiente', then=1), output_field=IntegerField())),
            confirmadas=Count(Case(When(estado='Confirmada', then=1), output_field=IntegerField())),
            canceladas=Count(Case(When(estado='Cancelada', then=1), output_field=IntegerField())),
            asistio=Count(Case(When(estado='Asistio', then=1), output_field=IntegerField())),
            no_asistio=Count(Case(When(estado='No Asistio', then=1), output_field=IntegerField())),
            ingresos=Sum(
                Case(
                    When(estado='Asistio', then=F('servicio__precio')),
                    default=Value(0),
                    output_field=DecimalField()
                )
            )
        ).order_by('sede__nombre')

        # Prepare response
        response_data = []
        for item in report_data:
            response_data.append({
                'sede_id': item['sede__id'],
                'sede_nombre': item['sede__nombre'],
                'total_citas': item['total_citas'],
                'estados': {
                    'Pendiente': item['pendientes'],
                    'Confirmada': item['confirmadas'],
                    'Cancelada': item['canceladas'],
                    'Asistio': item['asistio'],
                    'No Asistio': item['no_asistio'],
                },
                'ingresos': item['ingresos'] or 0
            })
        
        # For services and resources, it's better to provide a separate breakdown per sede
        # or aggregate them across all filtered appointments.        
        # Let's provide a summary of services and resources used within the filtered set.
        
        # Services summary
        services_summary = queryset.values('servicio__nombre').annotate(
            count=Count('servicio__nombre')
        ).order_by('servicio__nombre')

        # Resources summary
        resources_summary = queryset.values('colaboradores__nombre').annotate(
            count=Count('colaboradores__nombre')
        ).order_by('colaboradores__nombre')

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
    servicio = forms.ModelChoiceField(queryset=Servicio.objects.all(), required=False, label=_("Servicio"))
    colaborador = forms.ModelChoiceField(queryset=Colaborador.objects.all(), required=False, label=_("Colaborador"))
    estado = forms.ChoiceField(choices=[('', _('Todos'))] + Cita.ESTADO_CHOICES, required=False, label=_("Estado"))
    report_format = forms.ChoiceField(choices=[('json', _('JSON (Resumen)')), ('csv', _('CSV (Detallado)'))], label=_("Formato de Reporte"))

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
            servicio = form.cleaned_data['servicio']
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
            if servicio:
                dummy_request.query_params['servicio_id'] = servicio.id
            if colaborador:
                dummy_request.query_params['colaborador_id'] = colaborador.id
            if estado:
                dummy_request.query_params['estado'] = estado

            response = AppointmentReportView.as_view()(dummy_request)

            # If it's a CSV response, return it directly
            if isinstance(response, HttpResponse) and response.get('Content-Type') == 'text/csv':
                return response
            else:
                # For JSON response, render it in a template
                # You might want to format this JSON nicely for display
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
        asistio = request.data.get('asistio')

        if asistio is None:
            return Response({'error': 'El campo "asistio" es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        if asistio:
            cita.estado = 'Asistio'
        else:
            cita.estado = 'No Asistio'
        
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
            return Cita.objects.filter(recursos=recurso).order_by('fecha')
        except Colaborador.DoesNotExist:
            return Cita.objects.none()

    @action(detail=True, methods=['post'])
    def marcar_asistencia(self, request, pk=None):
        cita = self.get_object()
        asistio = request.data.get('asistio')

        if asistio is None:
            return Response({'error': 'El campo "asistio" es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        if asistio:
            cita.estado = 'Asistio'
        else:
            cita.estado = 'No Asistio'
        
        cita.save()
        return Response(CitaSerializer(cita).data)

class RecursoViewSet(SedeFilteredMixin, viewsets.ModelViewSet):
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    permission_classes = [IsAdminOrSedeAdminOrReadOnly]
