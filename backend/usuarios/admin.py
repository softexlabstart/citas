from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib import messages
from .models import PerfilUsuario, OnboardingProgress, FailedLoginAttempt, ActiveJWTToken, AuditLog
from organizacion.models import Sede, Organizacion
import hashlib
import logging

# MULTI-TENANT: Import helper for profile management
from .utils import get_perfil_or_first

logger = logging.getLogger(__name__)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'get_email',
        'organizacion',
        'display_badge',
        'get_additional_roles_display',
        'is_active',
        'get_sedes_count',
        'get_otros_perfiles'
    )
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_filter = ('role', 'is_active', 'organizacion', 'created_at')
    filter_horizontal = ('sedes', 'sedes_administradas')
    actions = ['activar_perfiles', 'desactivar_perfiles']
    readonly_fields = ('get_otros_perfiles_detalle', 'created_at', 'updated_at', 'get_accessible_sedes_display')

    fieldsets = (
        ('👤 Usuario y Organización', {
            'fields': ('user', 'organizacion', 'is_active'),
            'description': 'Usuario y su membresía en la organización'
        }),
        ('🎭 Sistema de Roles', {
            'fields': ('role', 'additional_roles'),
            'description': '✨ ROL PRINCIPAL: Selecciona el rol principal del usuario. '
                          'ROLES ADICIONALES: Puedes agregar roles adicionales como ["cliente"] si un colaborador también es cliente.'
        }),
        ('🏢 Sedes según Rol', {
            'fields': ('sede', 'sedes', 'sedes_administradas', 'get_accessible_sedes_display'),
            'description': '📍 SEDE: Sede principal del usuario | '
                          'SEDES: Para colaboradores que trabajan en múltiples sedes | '
                          'SEDES ADMINISTRADAS: Para administradores de sede'
        }),
        ('🔐 Permisos Personalizados', {
            'fields': ('permissions',),
            'classes': ('collapse',),
            'description': 'Permisos granulares adicionales en formato JSON. '
                          'Ejemplo: {"can_view_reports": true, "can_export_data": false}'
        }),
        ('⚙️ Configuración', {
            'fields': ('timezone',),
            'classes': ('collapse',)
        }),
        ('📋 Datos Personales', {
            'fields': ('telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento'),
            'classes': ('collapse',)
        }),
        ('✅ Consentimiento de Datos', {
            'fields': ('has_consented_data_processing', 'data_processing_opt_out'),
            'classes': ('collapse',)
        }),
        ('📅 Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('🔗 Información Multi-organización', {
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

    def get_additional_roles_display(self, obj):
        """Muestra roles adicionales de manera legible"""
        if not obj.additional_roles or len(obj.additional_roles) == 0:
            return '-'
        role_names = {
            'owner': 'Propietario',
            'admin': 'Admin',
            'sede_admin': 'Admin Sede',
            'colaborador': 'Colaborador',
            'cliente': 'Cliente'
        }
        return ', '.join([role_names.get(r, r) for r in obj.additional_roles])
    get_additional_roles_display.short_description = 'Roles Adicionales'

    def get_sedes_count(self, obj):
        """Muestra cantidad de sedes accesibles"""
        count = obj.accessible_sedes.count()
        if obj.can_access_all_sedes:
            return f'✨ Todas ({count})'
        return str(count)
    get_sedes_count.short_description = 'Sedes Accesibles'

    def get_accessible_sedes_display(self, obj):
        """Muestra lista de sedes accesibles (readonly)"""
        sedes = obj.accessible_sedes
        if not sedes.exists():
            return "Ninguna sede accesible"

        sede_list = [f"• {sede.nombre}" for sede in sedes[:10]]
        if sedes.count() > 10:
            sede_list.append(f"... y {sedes.count() - 10} más")

        from django.utils.html import format_html
        return format_html('<br>'.join(sede_list))
    get_accessible_sedes_display.short_description = 'Sedes Accesibles (según roles)'

    def activar_perfiles(self, request, queryset):
        """Activa perfiles seleccionados"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} perfil(es) activado(s) exitosamente.", messages.SUCCESS)
    activar_perfiles.short_description = "✅ Activar perfiles seleccionados"

    def desactivar_perfiles(self, request, queryset):
        """Desactiva perfiles seleccionados"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} perfil(es) desactivado(s) exitosamente.", messages.WARNING)
    desactivar_perfiles.short_description = "❌ Desactivar perfiles seleccionados"

    def save_model(self, request, obj, form, change):
        """
        Auto-sincroniza el perfil con otros modelos del sistema cuando se guarda.
        - Si es colaborador: crea/actualiza registro en Colaborador
        - Si cambia de sede: actualiza Colaborador
        """
        super().save_model(request, obj, form, change)

        # Sincronizar con Colaborador si tiene rol de colaborador
        if 'colaborador' in obj.all_roles and obj.sede:
            from citas.models import Colaborador
            from organizacion.thread_locals import set_current_organization

            # Establecer contexto de organización para OrganizationManager
            set_current_organization(obj.organizacion)

            try:
                # Crear o actualizar colaborador
                # NOTA: Colaborador no tiene campo 'organizacion', solo 'sede'
                # La organización se obtiene a través de sede.organizacion
                colaborador, created = Colaborador.all_objects.get_or_create(
                    usuario=obj.user,
                    defaults={
                        'nombre': obj.user.get_full_name() or obj.user.username,
                        'email': obj.user.email,
                        'sede': obj.sede,
                    }
                )

                if created:
                    self.message_user(
                        request,
                        f"Se creó el registro de Colaborador para {obj.user.username}",
                        messages.SUCCESS
                    )
                else:
                    # Si ya existe, actualizar sede si cambió
                    if obj.sede and colaborador.sede != obj.sede:
                        colaborador.sede = obj.sede
                        colaborador.save()
                        self.message_user(
                            request,
                            f"Se actualizó la sede del colaborador a '{obj.sede.nombre}'",
                            messages.INFO
                        )
            finally:
                # Limpiar contexto
                set_current_organization(None)

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


@admin.register(FailedLoginAttempt)
class FailedLoginAttemptAdmin(admin.ModelAdmin):
    """
    SEGURIDAD: Admin para monitorear intentos de login fallidos.
    Solo lectura para preservar evidencia de seguridad.
    """
    list_display = ('email', 'ip_address', 'attempted_at', 'user_agent_short')
    list_filter = ('attempted_at',)
    search_fields = ('email', 'ip_address')
    readonly_fields = ('email', 'ip_address', 'attempted_at', 'user_agent')
    date_hierarchy = 'attempted_at'
    ordering = ('-attempted_at',)

    # Solo lectura - no permitir edición de logs de seguridad
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Solo superusuarios pueden borrar logs antiguos
        return request.user.is_superuser

    def user_agent_short(self, obj):
        """Muestra versión corta del user agent"""
        if obj.user_agent:
            return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
        return '-'
    user_agent_short.short_description = 'User Agent'

    actions = ['clear_old_attempts']

    def clear_old_attempts(self, request, queryset):
        """Limpia intentos de más de 30 días"""
        from datetime import timedelta
        from django.utils import timezone

        cutoff = timezone.now() - timedelta(days=30)
        count = FailedLoginAttempt.objects.filter(attempted_at__lt=cutoff).delete()[0]

        self.message_user(
            request,
            f"Se eliminaron {count} intentos fallidos de más de 30 días.",
            messages.SUCCESS
        )
    clear_old_attempts.short_description = "🧹 Limpiar intentos antiguos (>30 días)"


@admin.register(ActiveJWTToken)
class ActiveJWTTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for monitoring active JWT sessions.
    """
    list_display = ('user', 'device_info', 'ip_address', 'created_at', 'last_used', 'expires_at', 'is_expired')
    list_filter = ('created_at', 'last_used', 'expires_at')
    search_fields = ('user__username', 'user__email', 'ip_address', 'device_info')
    readonly_fields = ('user', 'jti', 'token', 'device_info', 'ip_address', 'created_at', 'last_used', 'expires_at')
    ordering = ('-last_used',)

    def is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at < timezone.now()
    is_expired.boolean = True
    is_expired.short_description = 'Expirado'

    def has_add_permission(self, request):
        # No permitir creación manual
        return False

    def has_change_permission(self, request, obj=None):
        # No permitir edición
        return False

    actions = ['revoke_sessions']

    def revoke_sessions(self, request, queryset):
        """Acción personalizada para revocar sesiones seleccionadas."""
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

        count = 0
        for session in queryset:
            try:
                # Buscar el token en OutstandingToken y blacklistearlo
                outstanding = OutstandingToken.objects.filter(jti=session.jti).first()
                if outstanding:
                    BlacklistedToken.objects.get_or_create(token=outstanding)
                # Eliminar la sesión
                session.delete()
                count += 1
            except Exception as e:
                logger.error(f"Error revoking session {session.id}: {e}")

        self.message_user(
            request,
            f"Se revocaron exitosamente {count} sesiones.",
            messages.SUCCESS
        )
    revoke_sessions.short_description = "🚫 Revocar sesiones seleccionadas"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing audit logs.
    Read-only to prevent tampering with audit trail.
    """
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'success', 'ip_address')
    list_filter = ('action', 'success', 'timestamp', 'model_name')
    search_fields = ('user__username', 'user__email', 'model_name', 'object_id', 'notes', 'ip_address')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'user_agent', 'timestamp', 'success', 'notes')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        # No permitir creación manual de audit logs
        return False

    def has_change_permission(self, request, obj=None):
        # No permitir edición de audit logs
        return False

    def has_delete_permission(self, request, obj=None):
        # Solo superusuarios pueden eliminar logs (para limpieza de datos antiguos)
        return request.user.is_superuser

