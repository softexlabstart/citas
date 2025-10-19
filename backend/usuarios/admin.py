from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib import messages
from .models import PerfilUsuario, OnboardingProgress
from organizacion.models import Sede, Organizacion
import hashlib

# MULTI-TENANT: Import helper for profile management
from .utils import get_perfil_or_first


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email', 'organizacion', 'get_sede_nombre', 'get_otros_perfiles')
    search_fields = ('user__username', 'user__email', 'nombre')
    list_filter = ('organizacion', 'sede')
    filter_horizontal = ('sedes', 'sedes_administradas',)
    actions = ['crear_perfil_en_otra_organizacion']
    readonly_fields = ('get_otros_perfiles_detalle',)
    fieldsets = (
        ('Información de Usuario', {
            'fields': ('user', 'organizacion', 'timezone')
        }),
        ('Sedes', {
            'fields': ('sede', 'sedes', 'sedes_administradas'),
            'description': 'Sede principal y sedes adicionales a las que tiene acceso'
        }),
        ('Datos Personales', {
            'fields': ('telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento'),
            'classes': ('collapse',)
        }),
        ('Consentimiento de Datos', {
            'fields': ('has_consented_data_processing', 'data_processing_opt_out'),
            'classes': ('collapse',)
        }),
        ('Información Multi-organización', {
            'fields': ('get_otros_perfiles_detalle',),
            'classes': ('collapse',)
        }),
    )

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_otros_perfiles(self, obj):
        """Muestra si hay otros usuarios con el mismo email"""
        email = obj.user.email
        count = User.objects.filter(email=email).count()
        if count > 1:
            return f"⚠️ {count} cuentas"
        return "✓ Única"
    get_otros_perfiles.short_description = 'Multi-org'

    def get_otros_perfiles_detalle(self, obj):
        """Muestra detalles de otros perfiles con el mismo email"""
        email = obj.user.email
        otros_users = User.objects.filter(email=email).exclude(id=obj.user.id)

        if not otros_users.exists():
            return "Este es el único perfil para este email."

        info = [f"<strong>Otros perfiles para {email}:</strong><ul>"]
        for user in otros_users:
            # MULTI-TENANT: Obtener todos los perfiles del usuario
            perfiles = user.perfiles.select_related('organizacion').all()
            if perfiles.exists():
                for perfil in perfiles:
                    org = perfil.organizacion.nombre if perfil.organizacion else "Sin org"
                    info.append(f"<li>Username: {user.username} - Organización: {org}</li>")
            else:
                info.append(f"<li>Username: {user.username} - Sin perfil</li>")
        info.append("</ul>")

        from django.utils.html import format_html
        return format_html(''.join(info))
    get_otros_perfiles_detalle.short_description = 'Otros perfiles del mismo email'

    def crear_perfil_en_otra_organizacion(self, request, queryset):
        """
        Crea un nuevo usuario con el mismo email en otra organización.
        Útil para usuarios que necesitan acceso a múltiples organizaciones.
        """
        if queryset.count() != 1:
            self.message_user(request, "Por favor selecciona solo un perfil.", messages.ERROR)
            return

        perfil_original = queryset.first()
        original_user = perfil_original.user

        # Mostrar formulario o mensaje
        self.message_user(
            request,
            f"Para crear acceso a otra organización para {original_user.email}: "
            f"1) Ve a Usuarios > Agregar usuario, "
            f"2) Username: {original_user.email.split('@')[0]}_NOMBREORG, "
            f"3) Email: {original_user.email}, "
            f"4) Luego crea su perfil con la nueva organización.",
            messages.INFO
        )

    crear_perfil_en_otra_organizacion.short_description = "Instrucciones: Crear en otra organización"

    def get_queryset(self, request):
        qs = self.model.all_objects.all()
        if request.user.is_superuser:
            return qs

        # MULTI-TENANT: Usar helper
        perfil = get_perfil_or_first(request.user)
        if perfil and perfil.organizacion:
            return qs.filter(organizacion=perfil.organizacion)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_superuser:
            if db_field.name == "sede":
                kwargs["queryset"] = Sede.all_objects.all()
            if db_field.name == "organizacion":
                kwargs["queryset"] = Organizacion.objects.all()
        else:
            # MULTI-TENANT: Usar helper
            perfil = get_perfil_or_first(request.user)
            if perfil and perfil.organizacion:
                organizacion = perfil.organizacion
                if db_field.name == "sede":
                    kwargs["queryset"] = Sede.all_objects.filter(organizacion=organizacion)
                if db_field.name == "organizacion":
                    kwargs["queryset"] = Organizacion.objects.filter(pk=organizacion.pk)
            else:
                if db_field.name in ["sede", "organizacion"]:
                    kwargs["queryset"] = Sede.all_objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if request.user.is_superuser:
            if db_field.name in ["sedes", "sedes_administradas"]:
                kwargs["queryset"] = Sede.all_objects.all()
        else:
            # MULTI-TENANT: Usar helper
            perfil = get_perfil_or_first(request.user)
            if perfil and perfil.organizacion and db_field.name in ["sedes", "sedes_administradas"]:
                kwargs["queryset"] = Sede.all_objects.filter(organizacion=perfil.organizacion)
            else:
                kwargs["queryset"] = Sede.all_objects.none()

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_sede_nombre(self, obj):
        """
        Devuelve el nombre de la sede o un valor por defecto si no existe.
        """
        if obj.sede:
            return obj.sede.nombre
        return "Sin sede asignada"
    get_sede_nombre.short_description = 'Sede'


@admin.register(OnboardingProgress)
class OnboardingProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'completion_percentage', 'is_completed', 'is_dismissed', 'updated_at')
    list_filter = ('is_completed', 'is_dismissed', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('completion_percentage', 'pending_steps', 'created_at', 'updated_at', 'completed_at')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Progreso', {
            'fields': (
                'has_created_service',
                'has_added_collaborator', 
                'has_viewed_public_link',
                'has_completed_profile',
                'completion_percentage',
                'pending_steps'
            )
        }),
        ('Estado', {
            'fields': ('is_completed', 'is_dismissed')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

