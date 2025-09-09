from django.contrib import admin
from .models import Recurso, Servicio, Cita, Horario
from django.contrib.admin.models import LogEntry
from django.urls import path
from .views import admin_report_view
from django.contrib.auth.models import User
from .forms import HorarioAdminForm
from .reports import generate_excel_report, generate_pdf_report

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    form = HorarioAdminForm
    list_display = ('dia_semana', 'hora_inicio', 'hora_fin', 'recurso')
    list_filter = ('dia_semana', 'recurso')
    search_fields = ('recurso__nombre',)


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'servicio', 'confirmado', 'estado')
    list_filter = ('confirmado', 'fecha', 'servicio', 'estado')
    search_fields = ('nombre', 'servicio__nombre')
    list_editable = ('confirmado', 'estado')
    actions = ['confirmar_citas', 'cancelar_citas', 'export_to_excel', 'export_to_pdf', 'marcar_asistio', 'marcar_no_asistio']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reportes/', self.admin_site.admin_view(admin_report_view), name='citas_report_form'),
        ]
        return custom_urls + urls

    def confirmar_citas(self, request, queryset):
        queryset.update(confirmado=True, estado='Confirmada')
    confirmar_citas.short_description = "Confirmar citas seleccionadas"

    def cancelar_citas(self, request, queryset):
        queryset.update(confirmado=False, estado='Cancelada')
    cancelar_citas.short_description = "Cancelar citas seleccionadas"

    def marcar_asistio(self, request, queryset):
        queryset.update(estado='Asistio')
    marcar_asistio.short_description = "Marcar como asistida"

    def marcar_no_asistio(self, request, queryset):
        queryset.update(estado='No Asistio')
    marcar_no_asistio.short_description = "Marcar como no asistida"

    def export_to_excel(self, request, queryset):
        optimized_queryset = queryset.select_related('servicio')
        return generate_excel_report(optimized_queryset)
    export_to_excel.short_description = 'Exportar a Excel'

    def export_to_pdf(self, request, queryset):
        optimized_queryset = queryset.select_related('servicio')
        return generate_pdf_report(optimized_queryset)
    export_to_pdf.short_description = 'Exportar a PDF'


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