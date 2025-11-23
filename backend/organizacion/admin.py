from django.contrib import admin # type: ignore
from .models import Organizacion, Sede

# MULTI-TENANT: Import helper for profile management
from usuarios.utils import get_perfil_or_first

@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'permitir_agendamiento_publico', 'usar_branding_personalizado', 'is_active', 'created_at')
    list_filter = ('is_active', 'permitir_agendamiento_publico', 'usar_branding_personalizado', 'created_at')
    search_fields = ('nombre', 'slug')
    readonly_fields = ('slug', 'schema_name', 'created_at', 'updated_at')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'is_active')
        }),
        ('Configuración de Agendamiento', {
            'fields': ('permitir_agendamiento_publico',),
            'description': 'Controla si usuarios sin cuenta pueden agendar citas públicamente'
        }),
        ('Notificaciones WhatsApp', {
            'fields': (
                'whatsapp_enabled',
                'whatsapp_sender_name',
                'whatsapp_confirmation_enabled',
                'whatsapp_reminder_24h_enabled',
                'whatsapp_reminder_1h_enabled',
                'whatsapp_cancellation_enabled',
            ),
            'description': 'Configura las notificaciones automáticas por WhatsApp via Twilio'
        }),
        ('Plantillas de WhatsApp Personalizadas', {
            'classes': ('collapse',),
            'fields': (
                'whatsapp_template_confirmation',
                'whatsapp_template_reminder_24h',
                'whatsapp_template_reminder_1h',
                'whatsapp_template_cancellation',
            ),
            'description': 'Personaliza los mensajes de WhatsApp. Deja en blanco para usar las plantillas por defecto. Variables disponibles: {nombre}, {fecha}, {hora}, {sede}, {servicios}, {colaboradores}, {razon}'
        }),
        ('Branding Personalizado', {
            'fields': (
                'usar_branding_personalizado',
                'logo',
                'color_primario',
                'color_secundario',
                'color_texto',
                'color_fondo',
                'texto_bienvenida'
            ),
            'description': 'Personaliza la apariencia de la página pública de agendamiento'
        }),
        ('Database-per-Tenant (Avanzado)', {
            'classes': ('collapse',),
            'fields': ('schema_name', 'database_name')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        })
    )

    # Only superusers can see and manage organizations
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'organizacion', 'direccion', 'telefono')
    list_filter = ('organizacion__nombre',)
    search_fields = ('nombre', 'direccion', 'organizacion__nombre')
    list_select_related = ('organizacion',)

    def get_queryset(self, request):
        # Use all_objects to bypass the default OrganizacionManager
        qs = self.model.all_objects.all()
        if request.user.is_superuser:
            return qs

        # MULTI-TENANT: Usar helper para obtener perfil
        perfil = get_perfil_or_first(request.user)
        if perfil and perfil.organizacion:
            return qs.filter(organizacion=perfil.organizacion)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Restrict the 'organizacion' dropdown in the Sede form
        if db_field.name == "organizacion" and not request.user.is_superuser:
            # MULTI-TENANT: Usar helper para obtener perfil
            perfil = get_perfil_or_first(request.user)
            if perfil and perfil.organizacion:
                kwargs["queryset"] = Organizacion.objects.filter(pk=perfil.organizacion.pk)
            else:
                kwargs["queryset"] = Organizacion.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
