from django.contrib import admin
from .models import Recurso, Servicio, Cita, Horario
from django.http import HttpResponse
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib.admin.models import LogEntry
from django.urls import path
from .views import admin_report_view
from django import forms
from django.contrib.auth.models import User


class HorarioAdminForm(forms.ModelForm):
    TIME_CHOICES = [('', '---------')]
    for i in range(24):
        for j in [0, 30]:
            time_str = f'{i:02d}:{j:02d}:00'
            TIME_CHOICES.append((time_str, time_str.rsplit(':', 1)[0]))

    hora_inicio = forms.ChoiceField(choices=TIME_CHOICES, required=True)
    hora_fin = forms.ChoiceField(choices=TIME_CHOICES, required=True)

    class Meta:
        model = Horario
        fields = '__all__'


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
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=citas.xlsx'
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Citas'

        columns = ['Nombre', 'Fecha', 'Servicio', 'Confirmado', 'Estado']
        sheet.append(columns)

        for cita in queryset:
            sheet.append([
                cita.nombre,
                cita.fecha.strftime('%Y-%m-%d %H:%M'),
                cita.servicio.nombre,
                'Sí' if cita.confirmado else 'No',
                cita.estado
            ])

        workbook.save(response)
        return response
    export_to_excel.short_description = 'Exportar a Excel'

    def export_to_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=citas.pdf'

        p = canvas.Canvas(response, pagesize=letter)
        p.drawString(100, 750, "Reporte de Citas")

        y = 700
        for cita in queryset:
            p.drawString(100, y, f"Nombre: {cita.nombre}")
            p.drawString(100, y - 20, f"Fecha: {cita.fecha.strftime('%Y-%m-%d %H:%M')}")
            p.drawString(100, y - 40, f"Servicio: {cita.servicio.nombre}")
            p.drawString(100, y - 60, f"Confirmado: {'Sí' if cita.confirmado else 'No'}")
            p.drawString(100, y - 80, f"Estado: {cita.estado}")
            y -= 100

        p.showPage()
        p.save()
        return response
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