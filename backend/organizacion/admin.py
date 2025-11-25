from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Organizacion, Sede

# MULTI-TENANT: Import helper for profile management
from usuarios.utils import get_perfil_or_first


class SedeInline(admin.TabularInline):
    """Inline para ver sedes de la organización"""
    model = Sede
    extra = 0
    fields = ('nombre', 'direccion', 'telefono')
    can_delete = False
    show_change_link = True


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'slug',
        'is_active',
        'whatsapp_status',
        'users_count',
        'messages_count',
        'last_activity',
        'created_at',
        'view_details_link'
    )
    list_filter = (
        'is_active',
        'whatsapp_enabled',
        'permitir_agendamiento_publico',
        'usar_branding_personalizado',
        'created_at'
    )
    search_fields = ('nombre', 'slug')
    readonly_fields = (
        'slug',
        'schema_name',
        'created_at',
        'updated_at',
        'organization_stats',
        'whatsapp_stats',
        'recent_activity'
    )

    inlines = [SedeInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'is_active', 'organization_stats')
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
                'whatsapp_stats',
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
            'classes': ('collapse',),
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
        ('Actividad Reciente', {
            'fields': ('recent_activity',),
            'description': 'Últimas acciones realizadas en esta organización'
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        })
    )

    actions = ['enable_whatsapp', 'disable_whatsapp', 'view_audit_logs']

    # ==================== CUSTOM DISPLAY METHODS ====================

    @admin.display(description='WhatsApp')
    def whatsapp_status(self, obj):
        """Muestra el estado de WhatsApp con íconos"""
        if obj.whatsapp_enabled:
            return format_html(
                '<span style="color: green;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inactivo</span>'
        )

    @admin.display(description='Usuarios')
    def users_count(self, obj):
        """Cuenta total de usuarios en la organización"""
        count = obj.miembros.count()
        return format_html(
            '<a href="{}?organizacion__id__exact={}">{}</a>',
            reverse('admin:usuarios_perfilusuario_changelist'),
            obj.id,
            count
        )

    @admin.display(description='Mensajes WhatsApp')
    def messages_count(self, obj):
        """Cuenta mensajes WhatsApp enviados (últimos 30 días)"""
        from django.db import connection

        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Usar SQL raw para contar mensajes en el schema del tenant
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{obj.schema_name}"."citas_whatsapp_message"
                    WHERE organizacion_id = %s
                    AND created_at >= %s
                """, [obj.id, thirty_days_ago])
                count = cursor.fetchone()[0]
        except Exception:
            # Si falla, probablemente no hay tabla en ese schema
            count = 0

        if count > 0:
            return format_html(
                '<a href="{}?organizacion__id__exact={}">{}</a>',
                reverse('admin:citas_whatsappmessage_changelist'),
                obj.id,
                count
            )
        return count

    @admin.display(description='Última Actividad')
    def last_activity(self, obj):
        """Muestra la última actividad de la organización"""
        from usuarios.models import AuditLog

        # Buscar el último log de cualquier usuario de esta org
        last_log = AuditLog.objects.filter(
            user__perfiles__organizacion=obj
        ).first()

        if last_log:
            return format_html(
                '<span title="{}">{}</span>',
                last_log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                last_log.timestamp.strftime('%d/%m/%Y')
            )
        return '-'

    @admin.display(description='Detalles')
    def view_details_link(self, obj):
        """Link para ver detalles completos"""
        url = reverse('admin:organizacion_organizacion_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Ver Detalles</a>',
            url
        )

    # ==================== READONLY FIELD METHODS ====================

    @admin.display(description='Estadísticas de la Organización')
    def organization_stats(self, obj):
        """Muestra estadísticas generales de la organización"""
        from django.contrib.auth.models import User
        from django.db import connection

        # Contar usuarios por rol (estos están en public)
        total_users = obj.miembros.count()
        admins = obj.miembros.filter(role='admin').count()
        colaboradores = obj.miembros.filter(Q(role='colaborador') | Q(additional_roles__contains=['colaborador'])).count()
        clientes = obj.miembros.filter(Q(role='cliente') | Q(additional_roles__contains=['cliente'])).count()

        # Contar sedes (están en public)
        total_sedes = obj.sedes.count()

        # Contar citas (últimos 30 días) - usando SQL raw porque están en schema del tenant
        thirty_days_ago = timezone.now() - timedelta(days=30)
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{obj.schema_name}"."citas_cita"
                    WHERE created_at >= %s
                """, [thirty_days_ago])
                total_citas = cursor.fetchone()[0]
        except Exception:
            total_citas = 0

        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Resumen General</h3>
            <table style="width: 100%;">
                <tr>
                    <td><strong>Total Usuarios:</strong></td>
                    <td>{total_users}</td>
                    <td><strong>Administradores:</strong></td>
                    <td>{admins}</td>
                </tr>
                <tr>
                    <td><strong>Colaboradores:</strong></td>
                    <td>{colaboradores}</td>
                    <td><strong>Clientes:</strong></td>
                    <td>{clientes}</td>
                </tr>
                <tr>
                    <td><strong>Sedes:</strong></td>
                    <td>{total_sedes}</td>
                    <td><strong>Citas (30 días):</strong></td>
                    <td>{total_citas}</td>
                </tr>
            </table>
        </div>
        """
        return format_html(html)

    @admin.display(description='Estadísticas de WhatsApp')
    def whatsapp_stats(self, obj):
        """Muestra estadísticas de mensajes WhatsApp"""
        if not obj.whatsapp_enabled:
            return format_html('<p><em>WhatsApp no está habilitado</em></p>')

        from django.db import connection

        # Estadísticas de últimos 30 días usando SQL raw
        thirty_days_ago = timezone.now() - timedelta(days=30)

        try:
            with connection.cursor() as cursor:
                # Contar todos los mensajes
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM "{obj.schema_name}"."citas_whatsapp_message"
                    WHERE organizacion_id = %s
                    AND created_at >= %s
                """, [obj.id, thirty_days_ago])
                total = cursor.fetchone()[0]

                if total == 0:
                    return format_html('<p><em>No hay mensajes en los últimos 30 días</em></p>')

                # Contar por estado
                cursor.execute(f"""
                    SELECT status, COUNT(*)
                    FROM "{obj.schema_name}"."citas_whatsapp_message"
                    WHERE organizacion_id = %s
                    AND created_at >= %s
                    GROUP BY status
                """, [obj.id, thirty_days_ago])

                status_counts = dict(cursor.fetchall())
                sent = status_counts.get('sent', 0)
                delivered = status_counts.get('delivered', 0)
                read = status_counts.get('read', 0)
                failed = status_counts.get('failed', 0)

        except Exception:
            # Si la tabla no existe en el schema (ej: migraciones pendientes)
            return format_html('<p><em>No hay datos disponibles (tabla no encontrada en schema)</em></p>')

        delivery_rate = (delivered + read) / total * 100 if total > 0 else 0

        html = f"""
        <div style="background: #e7f3ff; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Mensajes WhatsApp (Últimos 30 días)</h3>
            <table style="width: 100%;">
                <tr>
                    <td><strong>Total Enviados:</strong></td>
                    <td>{total}</td>
                    <td><strong>Entregados:</strong></td>
                    <td>{delivered}</td>
                </tr>
                <tr>
                    <td><strong>Leídos:</strong></td>
                    <td>{read}</td>
                    <td><strong>Fallidos:</strong></td>
                    <td style="color: red;">{failed}</td>
                </tr>
                <tr>
                    <td><strong>Tasa de Entrega:</strong></td>
                    <td colspan="3" style="color: {'green' if delivery_rate > 90 else 'orange'};">
                        {delivery_rate:.1f}%
                    </td>
                </tr>
            </table>
        </div>
        """
        return format_html(html)

    @admin.display(description='Actividad Reciente')
    def recent_activity(self, obj):
        """Muestra los últimos 10 audit logs de esta organización"""
        from usuarios.models import AuditLog

        logs = AuditLog.objects.filter(
            user__perfiles__organizacion=obj
        ).select_related('user')[:10]

        if not logs:
            return format_html('<p><em>No hay actividad registrada</em></p>')

        html = '<div style="background: #fff3cd; padding: 15px; border-radius: 5px;">'
        html += '<h3 style="margin-top: 0;">Últimas 10 Acciones</h3>'
        html += '<table style="width: 100%; font-size: 12px;">'
        html += '<tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Modelo</th></tr>'

        for log in logs:
            username = log.user.username if log.user else 'Anónimo'
            html += f'''
            <tr>
                <td>{log.timestamp.strftime('%d/%m %H:%M')}</td>
                <td>{username}</td>
                <td>{log.get_action_display()}</td>
                <td>{log.model_name or '-'}</td>
            </tr>
            '''

        html += '</table>'
        html += f'<p><a href="{reverse("admin:usuarios_auditlog_changelist")}?user__perfiles__organizacion__id__exact={obj.id}">Ver todos los logs →</a></p>'
        html += '</div>'

        return format_html(html)

    # ==================== CUSTOM ACTIONS ====================

    @admin.action(description='Habilitar WhatsApp para organizaciones seleccionadas')
    def enable_whatsapp(self, request, queryset):
        updated = queryset.update(whatsapp_enabled=True)
        self.message_user(request, f'{updated} organización(es) actualizadas: WhatsApp habilitado')

    @admin.action(description='Deshabilitar WhatsApp para organizaciones seleccionadas')
    def disable_whatsapp(self, request, queryset):
        updated = queryset.update(whatsapp_enabled=False)
        self.message_user(request, f'{updated} organización(es) actualizadas: WhatsApp deshabilitado')

    @admin.action(description='Ver logs de auditoría')
    def view_audit_logs(self, request, queryset):
        """Redirige a los audit logs filtrados por organización"""
        if queryset.count() == 1:
            org = queryset.first()
            url = reverse('admin:usuarios_auditlog_changelist')
            url += f'?user__perfiles__organizacion__id__exact={org.id}'
            from django.shortcuts import redirect
            return redirect(url)
        else:
            self.message_user(request, 'Por favor selecciona solo una organización', level='warning')

    # ==================== PERMISSIONS ====================

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
