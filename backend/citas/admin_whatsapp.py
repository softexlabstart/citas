"""
Django Admin configuration for WhatsApp models.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models_whatsapp import WhatsAppMessage, WhatsAppReminderSchedule


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    """Admin para mensajes de WhatsApp enviados"""

    list_display = [
        'id',
        'message_type_badge',
        'recipient_name',
        'recipient_phone',
        'status_badge',
        'organizacion',
        'created_at',
    ]

    list_filter = [
        'status',
        'message_type',
        'created_at',
        'organizacion',
    ]

    search_fields = [
        'recipient_name',
        'recipient_phone',
        'message_body',
        'twilio_sid',
    ]

    readonly_fields = [
        'cita',
        'organizacion',
        'message_type',
        'recipient_phone',
        'recipient_name',
        'message_body',
        'status',
        'twilio_sid',
        'twilio_status',
        'error_code',
        'error_message',
        'cost',
        'created_at',
        'sent_at',
        'delivered_at',
        'updated_at',
    ]

    fieldsets = (
        ('Información General', {
            'fields': ('cita', 'organizacion', 'message_type', 'status')
        }),
        ('Destinatario', {
            'fields': ('recipient_name', 'recipient_phone')
        }),
        ('Mensaje', {
            'fields': ('message_body',)
        }),
        ('Twilio', {
            'fields': ('twilio_sid', 'twilio_status', 'cost'),
            'classes': ('collapse',)
        }),
        ('Error', {
            'fields': ('error_code', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'delivered_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def message_type_badge(self, obj):
        """Display message type with color badge"""
        colors = {
            'confirmation': '#28a745',
            'reminder_24h': '#ffc107',
            'reminder_1h': '#fd7e14',
            'cancellation': '#dc3545',
            'custom': '#6c757d',
        }
        color = colors.get(obj.message_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_message_type_display()
        )
    message_type_badge.short_description = 'Tipo'

    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'pending': '#6c757d',
            'sent': '#17a2b8',
            'delivered': '#28a745',
            'read': '#007bff',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def has_add_permission(self, request):
        """No permitir crear mensajes manualmente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo superusers pueden eliminar"""
        return request.user.is_superuser


@admin.register(WhatsAppReminderSchedule)
class WhatsAppReminderScheduleAdmin(admin.ModelAdmin):
    """Admin para recordatorios programados"""

    list_display = [
        'id',
        'cita',
        'reminder_type_badge',
        'scheduled_time',
        'is_sent_badge',
        'sent_at',
    ]

    list_filter = [
        'reminder_type',
        'is_sent',
        'scheduled_time',
    ]

    search_fields = [
        'cita__nombre',
        'cita__id',
    ]

    readonly_fields = [
        'cita',
        'reminder_type',
        'scheduled_time',
        'is_sent',
        'sent_at',
        'whatsapp_message',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Programación', {
            'fields': ('cita', 'reminder_type', 'scheduled_time')
        }),
        ('Estado', {
            'fields': ('is_sent', 'sent_at', 'whatsapp_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def reminder_type_badge(self, obj):
        """Display reminder type with badge"""
        colors = {
            '24h': '#ffc107',
            '1h': '#fd7e14',
        }
        color = colors.get(obj.reminder_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_reminder_type_display()
        )
    reminder_type_badge.short_description = 'Tipo'

    def is_sent_badge(self, obj):
        """Display sent status with badge"""
        if obj.is_sent:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Enviado</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">⏳ Pendiente</span>'
            )
    is_sent_badge.short_description = 'Estado'

    def has_add_permission(self, request):
        """No permitir crear recordatorios manualmente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo superusers pueden eliminar"""
        return request.user.is_superuser
