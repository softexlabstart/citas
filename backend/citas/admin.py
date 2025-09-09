from django.contrib import admin
from .models import Recurso, Servicio, Cita, Horario, Bloqueo
from django.contrib.admin.models import LogEntry
from django.urls import path
from .views import admin_report_view
from django.contrib.auth.models import User
from .forms import HorarioAdminForm
from .reports import generate_excel_report, generate_pdf_report

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
    list_editable = ('confirmado', 'estado')
    actions = ['confirmar_citas', 'cancelar_citas', 'export_to_excel', 'export_to_pdf', 'marcar_asistio', 'marcar_no_asistio']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reportes/', self.admin_site.admin_view(admin_report_view), name='citas_report_form'),
        ]
        return custom_urls + urls

    def confirmar_citas(self, request, queryset):
        updated_count = queryset.update(confirmado=True, estado='Confirmada')
        self.message_user(request, f"{updated_count} citas han sido confirmadas.")
    confirmar_citas.short_description = "Confirmar citas seleccionadas"

    def cancelar_citas(self, request, queryset):
        updated_count = queryset.update(confirmado=False, estado='Cancelada')
        self.message_user(request, f"{updated_count} citas han sido canceladas.")
    cancelar_citas.short_description = "Cancelar citas seleccionadas"

    def marcar_asistio(self, request, queryset):
        updated_count = queryset.update(estado='Asistio')
        self.message_user(request, f"{updated_count} citas han sido marcadas como 'Asistió'.")
    marcar_asistio.short_description = "Marcar como asistida"

    def marcar_no_asistio(self, request, queryset):
        updated_count = queryset.update(estado='No Asistio')
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
    list_display = ('recurso', 'sede', 'motivo', 'fecha_inicio', 'fecha_fin')
    list_filter = ('sede', 'recurso')
    search_fields = ('motivo', 'recurso__nombre', 'sede__nombre')
    date_hierarchy = 'fecha_inicio'


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