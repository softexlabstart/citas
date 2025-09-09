from django.contrib import admin
from .models import Recurso, Servicio, Cita, Horario, Bloqueo
from django.contrib.admin.models import LogEntry
from django.urls import path
from .views import admin_report_view
from django.contrib.auth.models import User
from .forms import HorarioAdminForm
from .reports import generate_excel_report, generate_pdf_report
from .utils import send_appointment_email

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    form = HorarioAdminForm
    list_display = ('recurso', 'get_sede', 'get_dia_semana_display_custom', 'hora_inicio', 'hora_fin')
    list_filter = ('recurso__sede', 'dia_semana', 'recurso')
    search_fields = ('recurso__nombre', 'recurso__sede__nombre')
    list_select_related = ('recurso', 'recurso__sede')

    @admin.display(description='Sede', ordering='recurso__sede__nombre')
    def get_sede(self, obj):
        if obj.recurso:
            return obj.recurso.sede
        return "N/A"

    @admin.display(description='Día de la Semana', ordering='dia_semana')
    def get_dia_semana_display_custom(self, obj):
        return obj.get_dia_semana_display()

@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sede', 'descripcion')
    list_filter = ('sede',)
    search_fields = ('nombre', 'sede__nombre')
    list_select_related = ('sede',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sede', 'duracion_estimada', 'precio')
    list_filter = ('sede',)
    search_fields = ('nombre', 'sede__nombre')
    list_select_related = ('sede',)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'servicio', 'sede', 'confirmado', 'estado')
    list_filter = ('sede', 'estado', 'confirmado', 'fecha', 'servicio')
    search_fields = ('nombre', 'servicio__nombre', 'sede__nombre', 'user__username')
    list_select_related = ('servicio', 'sede', 'user')
    # 'list_editable' is removed for 'estado' and 'confirmado' to enforce using custom actions.
    # This ensures that business logic, like sending email notifications, is always triggered
    # when an appointment's status changes, preventing inconsistencies.
    actions = ['confirmar_citas', 'cancelar_citas', 'export_to_excel', 'export_to_pdf', 'marcar_asistio', 'marcar_no_asistio']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reportes/', self.admin_site.admin_view(admin_report_view), name='citas_report_form'),
        ]
        return custom_urls + urls

    def confirmar_citas(self, request, queryset):
        updated_count = 0
        for cita in queryset.filter(estado='Pendiente'):
            cita.confirmado = True
            cita.estado = 'Confirmada'
            cita.save()
            send_appointment_email(
                appointment=cita,
                subject=f"Tu cita ha sido confirmada: {cita.servicio.nombre}",
                template_name='appointment_confirmation'
            )
            updated_count += 1
        self.message_user(request, f"{updated_count} citas han sido confirmadas y notificadas.")
    confirmar_citas.short_description = "Confirmar citas seleccionadas"

    def cancelar_citas(self, request, queryset):
        # Iterate to ensure business logic (like sending emails) is triggered for each cancellation.
        # This is more consistent than a bulk .update() which bypasses model save methods and signals.
        updated_count = 0
        for cita in queryset.filter(estado__in=['Pendiente', 'Confirmada']):
            original_fecha = cita.fecha
            cita.estado = 'Cancelada'
            cita.confirmado = False
            cita.save()
            send_appointment_email(
                appointment=cita,
                subject=f"Cancelación de Cita: {cita.servicio.nombre}",
                template_name='appointment_cancellation',
                context={'original_fecha': original_fecha}
            )
            updated_count += 1
        self.message_user(request, f"{updated_count} citas han sido canceladas y notificadas.")
    cancelar_citas.short_description = "Cancelar citas seleccionadas"

    def marcar_asistio(self, request, queryset):
        # Only mark confirmed appointments as attended for logical consistency
        updated_count = 0
        for cita in queryset.filter(estado='Confirmada'):
            cita.estado = 'Asistio'
            cita.save()
            updated_count += 1
        self.message_user(request, f"{updated_count} citas han sido marcadas como 'Asistió'.")
    marcar_asistio.short_description = "Marcar como asistida"

    def marcar_no_asistio(self, request, queryset):
        # A 'No Show' can happen for pending or confirmed appointments
        updated_count = 0
        for cita in queryset.filter(estado__in=['Pendiente', 'Confirmada']):
            cita.estado = 'No Asistio'
            cita.save()
            updated_count += 1
        self.message_user(request, f"{updated_count} citas han sido marcadas como 'No Asistió'.")
    marcar_no_asistio.short_description = "Marcar como no asistida"

    def export_to_excel(self, request, queryset):
        optimized_queryset = queryset.select_related('servicio')
        return generate_excel_report(optimized_queryset)
    export_to_excel.short_description = 'Exportar a Excel'

    def export_to_pdf(self, request, queryset):
        optimized_queryset = queryset.select_related('servicio')
        return generate_pdf_report(optimized_queryset)
    export_to_pdf.short_description = 'Exportar a PDF'


@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'get_sede', 'motivo', 'fecha_inicio', 'fecha_fin')
    list_filter = ('recurso__sede', 'recurso')
    search_fields = ('motivo', 'recurso__nombre', 'recurso__sede__nombre')
    date_hierarchy = 'fecha_inicio'
    list_select_related = ('recurso', 'recurso__sede')

    @admin.display(description='Sede', ordering='recurso__sede__nombre')
    def get_sede(self, obj):
        if obj.recurso:
            return obj.recurso.sede
        return "N/A"


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag')
    list_filter = ('action_time', 'user', 'content_type')
    search_fields = ('user__username', 'object_repr')
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False