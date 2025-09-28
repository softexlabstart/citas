from django.contrib import admin
from .models import Colaborador, Servicio, Cita, Horario, Bloqueo
from django.contrib.admin.models import LogEntry
from django.urls import path
from .views import admin_report_view
from django.contrib.auth.models import User
from .forms import HorarioAdminForm
from .reports import generate_excel_report, generate_pdf_report
from .utils import send_appointment_email
from organizacion.models import Sede

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    form = HorarioAdminForm
    list_display = ('colaborador', 'get_sede', 'get_dia_semana_display_custom', 'hora_inicio', 'hora_fin')
    list_filter = ('colaborador__sede__nombre', 'dia_semana', 'colaborador__nombre')
    search_fields = ('colaborador__nombre',)
    list_select_related = ('colaborador', 'colaborador__sede')

    def get_queryset(self, request):
        qs = self.model.all_objects.all()
        if request.user.is_superuser:
            return qs
        try:
            organizacion = request.user.perfil.organizacion
            if organizacion:
                return qs.filter(colaborador__sede__organizacion=organizacion)
            return qs.none()
        except AttributeError:
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "colaborador":
            qs = Colaborador.all_objects.all()
            if not request.user.is_superuser:
                try:
                    organizacion = request.user.perfil.organizacion
                    if organizacion:
                        qs = qs.filter(sede__organizacion=organizacion)
                    else:
                        qs = qs.none()
                except AttributeError:
                    qs = qs.none()
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='Sede')
    def get_sede(self, obj):
        if obj.colaborador:
            return obj.colaborador.sede
        return "N/A"

    @admin.display(description='Día de la Semana', ordering='dia_semana')
    def get_dia_semana_display_custom(self, obj):
        return obj.get_dia_semana_display()

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sede', 'descripcion')
    list_filter = ('sede__nombre',)
    search_fields = ('nombre', 'sede__nombre')
    list_select_related = ('sede',)

    def get_queryset(self, request):
        qs = self.model.all_objects.all()
        if request.user.is_superuser:
            return qs
        try:
            organizacion = request.user.perfil.organizacion
            if organizacion:
                return qs.filter(sede__organizacion=organizacion)
            return qs.none()
        except AttributeError:
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sede":
            if request.user.is_superuser:
                kwargs['queryset'] = Sede.all_objects.all()
            else:
                try:
                    organizacion = request.user.perfil.organizacion
                    if organizacion:
                        kwargs['queryset'] = Sede.all_objects.filter(organizacion=organizacion)
                    else:
                        kwargs['queryset'] = Sede.objects.none()
                except AttributeError:
                    kwargs['queryset'] = Sede.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "servicios":
            if request.user.is_superuser:
                kwargs["queryset"] = Servicio.all_objects.all()
            else:
                try:
                    organizacion = request.user.perfil.organizacion
                    if organizacion:
                        kwargs["queryset"] = Servicio.all_objects.filter(sede__organizacion=organizacion)
                    else:
                        kwargs["queryset"] = Servicio.objects.none()
                except (AttributeError, PerfilUsuario.DoesNotExist):
                    kwargs["queryset"] = Servicio.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sede', 'duracion_estimada', 'precio')
    list_filter = ('sede__nombre',)
    search_fields = ('nombre', 'sede__nombre')
    list_select_related = ('sede',)

    def get_queryset(self, request):
        qs = self.model.all_objects.all()
        if request.user.is_superuser:
            return qs
        try:
            organizacion = request.user.perfil.organizacion
            if organizacion:
                return qs.filter(sede__organizacion=organizacion)
            return qs.none()
        except AttributeError:
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sede":
            if request.user.is_superuser:
                kwargs['queryset'] = Sede.all_objects.all()
            else:
                try:
                    organizacion = request.user.perfil.organizacion
                    if organizacion:
                        kwargs['queryset'] = Sede.all_objects.filter(organizacion=organizacion)
                    else:
                        kwargs['queryset'] = Sede.objects.none()
                except AttributeError:
                    kwargs['queryset'] = Sede.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'get_servicios_display', 'sede', 'confirmado', 'estado')
    list_filter = ('sede__nombre', 'estado', 'confirmado', 'fecha', 'servicios__nombre')
    search_fields = ('nombre', 'sede__nombre')
    list_select_related = ('sede', 'user')
    prefetch_related = ('servicios', 'colaboradores')
    actions = ['confirmar_citas', 'cancelar_citas', 'export_to_excel', 'export_to_pdf', 'marcar_asistio', 'marcar_no_asistio']

    def get_queryset(self, request):
        qs = self.model.all_objects.all()
        if request.user.is_superuser:
            return qs
        try:
            organizacion = request.user.perfil.organizacion
            if organizacion:
                return qs.filter(sede__organizacion=organizacion)
            return qs.none()
        except AttributeError:
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sede":
            qs = Sede.all_objects.all()
            if not request.user.is_superuser:
                try:
                    organizacion = request.user.perfil.organizacion
                    if organizacion:
                        qs = qs.filter(organizacion=organizacion)
                    else:
                        qs = qs.none()
                except AttributeError:
                    qs = qs.none()
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            try:
                organizacion = request.user.perfil.organizacion
                if organizacion:
                    if db_field.name == "servicios":
                        kwargs["queryset"] = Servicio.all_objects.filter(sede__organizacion=organizacion)
                    if db_field.name == "colaboradores":
                        kwargs["queryset"] = Colaborador.all_objects.filter(sede__organizacion=organizacion)
                else:
                    if db_field.name in ["servicios", "colaboradores"]:
                        kwargs["queryset"] = db_field.related_model.objects.none()
            except AttributeError:
                if db_field.name in ["servicios", "colaboradores"]:
                    kwargs["queryset"] = db_field.related_model.objects.none()
        else:
            if db_field.name == "servicios":
                kwargs["queryset"] = Servicio.all_objects.all()
            if db_field.name == "colaboradores":
                kwargs["queryset"] = Colaborador.all_objects.all()

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description='Servicios')
    def get_servicios_display(self, obj):
        return ", ".join([servicio.nombre for servicio in obj.servicios.all()])

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
                appointment_id=cita.id,
                subject=f"Tu cita ha sido confirmada: {', '.join([s.nombre for s in cita.servicios.all()])}",
                template_name='appointment_confirmation'
            )
            updated_count += 1
        self.message_user(request, f"{updated_count} citas han sido confirmadas y notificadas.")
    confirmar_citas.short_description = "Confirmar citas seleccionadas"

    def cancelar_citas(self, request, queryset):
        updated_count = 0
        for cita in queryset.filter(estado__in=['Pendiente', 'Confirmada']):
            original_fecha = cita.fecha
            cita.estado = 'Cancelada'
            cita.confirmado = False
            cita.save()
            send_appointment_email(
                appointment_id=cita.id,
                subject=f"Cancelación de Cita: {', '.join([s.nombre for s in cita.servicios.all()])}",
                template_name='appointment_cancellation',
                context={'original_fecha': original_fecha.isoformat()}
            )
            updated_count += 1
        self.message_user(request, f"{updated_count} citas han sido canceladas y notificadas.")
    cancelar_citas.short_description = "Cancelar citas seleccionadas"

    def marcar_asistio(self, request, queryset):
        updated_count = 0
        for cita in queryset.filter(estado='Confirmada'):
            cita.estado = 'Asistio'
            cita.save()
            updated_count += 1
        self.message_user(request, f"{updated_count} citas han sido marcadas como 'Asistió'.")
    marcar_asistio.short_description = "Marcar como asistida"

    def marcar_no_asistio(self, request, queryset):
        updated_count = 0
        for cita in queryset.filter(estado__in=['Pendiente', 'Confirmada']):
            cita.estado = 'No Asistio'
            cita.save()
            updated_count += 1
        self.message_user(request, f"{updated_count} citas han sido marcadas como 'No Asistió'.")
    marcar_no_asistio.short_description = "Marcar como no asistida"

    def export_to_excel(self, request, queryset):
        optimized_queryset = queryset.prefetch_related('servicios')
        return generate_excel_report(optimized_queryset)
    export_to_excel.short_description = 'Exportar a Excel'

    def export_to_pdf(self, request, queryset):
        optimized_queryset = queryset.prefetch_related('servicios')
        return generate_pdf_report(optimized_queryset)
    export_to_pdf.short_description = 'Exportar a PDF'


@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ('colaborador', 'get_sede', 'motivo', 'fecha_inicio', 'fecha_fin')
    list_filter = ('colaborador__sede__nombre', 'colaborador__nombre')
    search_fields = ('motivo', 'colaborador__nombre')
    date_hierarchy = 'fecha_inicio'
    list_select_related = ('colaborador', 'colaborador__sede')

    def get_queryset(self, request):
        qs = self.model.all_objects.all()
        if request.user.is_superuser:
            return qs
        try:
            organizacion = request.user.perfil.organizacion
            if organizacion:
                return qs.filter(colaborador__sede__organizacion=organizacion)
            return qs.none()
        except AttributeError:
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "colaborador":
            qs = Colaborador.all_objects.all()
            if not request.user.is_superuser:
                try:
                    organizacion = request.user.perfil.organizacion
                    if organizacion:
                        qs = qs.filter(sede__organizacion=organizacion)
                    else:
                        qs = qs.none()
                except AttributeError:
                    qs = qs.none()
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='Sede')
    def get_sede(self, obj):
        if obj.colaborador:
            return obj.colaborador.sede
        return "N/A"


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag')
    list_filter = ('action_time', 'user', 'content_type')
    search_fields = ('user__username', 'object_repr')
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            organizacion = request.user.perfil.organizacion
            if organizacion:
                # Filter logs for users of the same organization
                return qs.filter(user__perfil__organizacion=organizacion)
            return qs.none()
        except AttributeError:
            return qs.none()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
