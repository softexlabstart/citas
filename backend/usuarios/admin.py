from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
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
        # Si no tiene email, no contar como duplicado
        if not email or email.strip() == '':
            return "Sin email"
        count = User.objects.filter(email=email).exclude(email='').count()
        if count > 1:
            return f"⚠️ {count} cuentas"
        return "✓ Única"
    get_otros_perfiles.short_description = 'Multi-org'

    def get_otros_perfiles_detalle(self, obj):
        """Muestra detalles de otros perfiles con el mismo email"""
        email = obj.user.email

        # Si no tiene email, no mostrar duplicados
        if not email or email.strip() == '':
            return "Usuario sin email - no se buscan duplicados."

        otros_users = User.objects.filter(email=email).exclude(email='').exclude(id=obj.user.id)

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
    list_display = ('timestamp', 'user', 'user_organization', 'action', 'model_name', 'object_id', 'success_badge', 'ip_address')
    list_filter = (
        'action',
        'success',
        'timestamp',
        'model_name',
        ('user__perfiles__organizacion', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('user__username', 'user__email', 'model_name', 'object_id', 'notes', 'ip_address', 'user__perfiles__organizacion__nombre')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'changes_display', 'ip_address', 'user_agent', 'timestamp', 'success', 'notes')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    list_select_related = ('user',)

    fieldsets = (
        ('Usuario y Acción', {
            'fields': ('user', 'action', 'timestamp', 'success')
        }),
        ('Objeto Afectado', {
            'fields': ('model_name', 'object_id', 'changes_display')
        }),
        ('Contexto', {
            'fields': ('ip_address', 'user_agent', 'notes'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Organización')
    def user_organization(self, obj):
        """Muestra la organización del usuario"""
        if obj.user:
            from usuarios.utils import get_perfil_or_first
            perfil = get_perfil_or_first(obj.user)
            if perfil and perfil.organizacion:
                from django.utils.html import format_html
                from django.urls import reverse
                url = reverse('admin:organizacion_organizacion_change', args=[perfil.organizacion.pk])
                return format_html(
                    '<a href="{}">{}</a>',
                    url,
                    perfil.organizacion.nombre
                )
        return '-'

    @admin.display(description='Éxito')
    def success_badge(self, obj):
        """Muestra el estado de éxito con badge"""
        from django.utils.html import format_html
        if obj.success:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Sí</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ No</span>'
            )

    @admin.display(description='Cambios')
    def changes_display(self, obj):
        """Muestra los cambios en formato legible"""
        from django.utils.html import format_html
        import json

        if not obj.changes:
            return '-'

        try:
            changes_json = json.dumps(obj.changes, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; max-width: 600px; overflow-x: auto;">{}</pre>',
                changes_json
            )
        except:
            return str(obj.changes)

    def has_add_permission(self, request):
        # No permitir creación manual de audit logs
        return False

    def has_change_permission(self, request, obj=None):
        # No permitir edición de audit logs
        return False

    def has_delete_permission(self, request, obj=None):
        # Solo superusuarios pueden eliminar logs (para limpieza de datos antiguos)
        return request.user.is_superuser

    def get_queryset(self, request):
        """Filtrar logs por organización si no es superuser"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        from usuarios.utils import get_perfil_or_first
        perfil = get_perfil_or_first(request.user)
        if perfil and perfil.organizacion:
            return qs.filter(user__perfiles__organizacion=perfil.organizacion)

        return qs.none()


# ==================== USER ADMIN PERSONALIZADO ====================

class PerfilUsuarioInline(admin.TabularInline):
    """Inline para mostrar perfiles del usuario"""
    model = PerfilUsuario
    extra = 0
    fields = ('organizacion', 'role', 'additional_roles', 'sede', 'is_active')
    readonly_fields = ('role', 'organizacion', 'sede')
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


# Desregistrar el admin por defecto de User
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Admin personalizado para User con información multi-organización.
    Extiende el UserAdmin de Django con funcionalidad de perfiles.
    """
    inlines = [PerfilUsuarioInline]

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'get_organizations',
        'get_roles',
        'is_active',
        'date_joined_short',
        'last_login_short',
    )

    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
        ('perfiles__organizacion', admin.RelatedOnlyFieldListFilter),
        ('perfiles__role', admin.ChoicesFieldListFilter),
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'perfiles__organizacion__nombre',
    )

    readonly_fields = BaseUserAdmin.readonly_fields + (
        'get_all_perfiles_info',
        'get_login_history',
    )

    # Modificar fieldsets para agregar información de perfiles
    fieldsets = BaseUserAdmin.fieldsets + (
        ('📊 Información Multi-Organización', {
            'fields': ('get_all_perfiles_info', 'get_login_history'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Organizaciones')
    def get_organizations(self, obj):
        """Muestra todas las organizaciones del usuario"""
        perfiles = obj.perfiles.select_related('organizacion').all()
        if not perfiles.exists():
            return format_html('<span style="color: #999;">Sin organización</span>')

        org_names = []
        for perfil in perfiles:
            if perfil.organizacion:
                url = reverse('admin:organizacion_organizacion_change', args=[perfil.organizacion.pk])
                org_names.append(f'<a href="{url}">{perfil.organizacion.nombre}</a>')

        return format_html('<br>'.join(org_names) if org_names else '-')

    @admin.display(description='Roles')
    def get_roles(self, obj):
        """Muestra todos los roles del usuario en formato badge"""
        perfiles = obj.perfiles.all()
        if not perfiles.exists():
            return '-'

        role_names = {
            'owner': ('Propietario', '#6f42c1'),
            'admin': ('Admin', '#007bff'),
            'sede_admin': ('Admin Sede', '#17a2b8'),
            'colaborador': ('Colaborador', '#28a745'),
            'cliente': ('Cliente', '#ffc107')
        }

        roles_set = set()
        for perfil in perfiles:
            roles_set.add(perfil.role)
            if perfil.additional_roles:
                roles_set.update(perfil.additional_roles)

        badges = []
        for role in roles_set:
            label, color = role_names.get(role, (role, '#6c757d'))
            badges.append(
                f'<span style="background-color: {color}; color: white; padding: 2px 8px; '
                f'border-radius: 3px; font-size: 11px; margin-right: 4px;">{label}</span>'
            )

        return format_html(''.join(badges))

    @admin.display(description='Registro')
    def date_joined_short(self, obj):
        """Muestra fecha de registro en formato corto"""
        return obj.date_joined.strftime('%d/%m/%Y')

    @admin.display(description='Último Login')
    def last_login_short(self, obj):
        """Muestra último login en formato corto"""
        if obj.last_login:
            return obj.last_login.strftime('%d/%m/%Y %H:%M')
        return '-'

    @admin.display(description='Información de Perfiles')
    def get_all_perfiles_info(self, obj):
        """Muestra información detallada de todos los perfiles"""
        perfiles = obj.perfiles.select_related('organizacion', 'sede').all()

        if not perfiles.exists():
            return format_html('<p><em>Este usuario no tiene perfiles asociados</em></p>')

        html = '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">'
        html += '<h3 style="margin-top: 0;">Perfiles del Usuario</h3>'

        for perfil in perfiles:
            org_name = perfil.organizacion.nombre if perfil.organizacion else 'Sin organización'
            sede_name = perfil.sede.nombre if perfil.sede else 'Sin sede'

            html += '<div style="background: white; padding: 10px; margin-bottom: 10px; border-left: 3px solid #007bff;">'
            html += f'<strong>Organización:</strong> {org_name}<br>'
            html += f'<strong>Rol Principal:</strong> {perfil.get_role_display()}<br>'

            if perfil.additional_roles:
                roles_display = ', '.join([perfil.get_role_display() for r in perfil.additional_roles])
                html += f'<strong>Roles Adicionales:</strong> {roles_display}<br>'

            html += f'<strong>Sede:</strong> {sede_name}<br>'
            html += f'<strong>Estado:</strong> {"✅ Activo" if perfil.is_active else "❌ Inactivo"}<br>'

            # Link al perfil
            perfil_url = reverse('admin:usuarios_perfilusuario_change', args=[perfil.pk])
            html += f'<a href="{perfil_url}" style="color: #007bff;">Ver detalles del perfil →</a>'
            html += '</div>'

        html += '</div>'
        return format_html(html)

    @admin.display(description='Historial de Login')
    def get_login_history(self, obj):
        """Muestra historial de sesiones activas"""
        tokens = ActiveJWTToken.objects.filter(user=obj).order_by('-last_used')[:5]

        if not tokens.exists():
            return format_html('<p><em>No hay sesiones activas</em></p>')

        html = '<div style="background: #fff3cd; padding: 15px; border-radius: 5px;">'
        html += '<h3 style="margin-top: 0;">Últimas 5 Sesiones</h3>'
        html += '<table style="width: 100%; font-size: 12px;">'
        html += '<tr><th>Dispositivo</th><th>IP</th><th>Último Uso</th><th>Expira</th></tr>'

        for token in tokens:
            from django.utils import timezone
            is_expired = token.expires_at < timezone.now()
            status_color = '#dc3545' if is_expired else '#28a745'

            html += f'<tr>'
            html += f'<td>{token.device_info or "Desconocido"}</td>'
            html += f'<td>{token.ip_address or "-"}</td>'
            html += f'<td>{token.last_used.strftime("%d/%m/%Y %H:%M")}</td>'
            html += f'<td style="color: {status_color};">'
            html += f'{"Expirado" if is_expired else token.expires_at.strftime("%d/%m/%Y")}'
            html += f'</td>'
            html += f'</tr>'

        html += '</table>'
        html += '</div>'
        return format_html(html)

    def get_queryset(self, request):
        """Filtrar usuarios por organización si no es superuser"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs.prefetch_related('perfiles__organizacion')

        perfil = get_perfil_or_first(request.user)
        if perfil and perfil.organizacion:
            # Mostrar usuarios que pertenecen a la misma organización
            return qs.filter(
                perfiles__organizacion=perfil.organizacion
            ).distinct().prefetch_related('perfiles__organizacion')

        return qs.none()
