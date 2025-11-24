"""
Modelos para el sistema de notificaciones por WhatsApp.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class WhatsAppMessage(models.Model):
    """
    Registro de mensajes de WhatsApp enviados.
    Permite tracking, debugging y analytics.
    """

    MESSAGE_TYPES = [
        ('confirmation', 'Confirmación de cita'),
        ('reminder_24h', 'Recordatorio 24h'),
        ('reminder_1h', 'Recordatorio 1h'),
        ('cancellation', 'Cancelación'),
        ('marketing', 'Marketing/Promoción'),
        ('custom', 'Personalizado'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('delivered', 'Entregado'),
        ('read', 'Leído'),
        ('failed', 'Fallido'),
    ]

    # Relaciones
    cita = models.ForeignKey(
        'citas.Cita',
        on_delete=models.CASCADE,
        related_name='whatsapp_messages',
        blank=True,
        null=True,
        help_text='Cita relacionada (opcional para mensajes de marketing)'
    )
    organizacion = models.ForeignKey(
        'organizacion.Organizacion',
        on_delete=models.CASCADE,
        related_name='whatsapp_messages'
    )

    # Información del mensaje
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        db_index=True
    )
    recipient_phone = models.CharField(
        max_length=20,
        help_text='Número de teléfono del destinatario con código de país'
    )
    recipient_name = models.CharField(
        max_length=200,
        help_text='Nombre del destinatario'
    )
    message_body = models.TextField(
        help_text='Contenido del mensaje enviado'
    )

    # Estado y tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Datos de Twilio
    twilio_sid = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Message SID de Twilio'
    )
    twilio_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Status devuelto por Twilio'
    )
    error_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text='Código de error si falló'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text='Mensaje de error detallado'
    )

    # Costos (opcional, para tracking)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        help_text='Costo del mensaje en USD'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Momento en que se envió el mensaje'
    )
    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Momento en que se entregó el mensaje'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'citas_whatsapp_message'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cita', 'message_type']),
            models.Index(fields=['organizacion', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_message_type_display()} - {self.recipient_name} ({self.status})"

    def mark_as_sent(self, twilio_sid, twilio_status):
        """Marca el mensaje como enviado"""
        from django.utils import timezone
        self.status = 'sent'
        self.twilio_sid = twilio_sid
        self.twilio_status = twilio_status
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'twilio_sid', 'twilio_status', 'sent_at', 'updated_at'])

    def mark_as_failed(self, error_code, error_message):
        """Marca el mensaje como fallido"""
        self.status = 'failed'
        self.error_code = error_code
        self.error_message = error_message
        self.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])

    def mark_as_delivered(self):
        """Marca el mensaje como entregado"""
        from django.utils import timezone
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])


class WhatsAppReminderSchedule(models.Model):
    """
    Programación de recordatorios de WhatsApp.
    Permite saber qué recordatorios están pendientes de envío.
    """

    REMINDER_TYPES = [
        ('24h', 'Recordatorio 24 horas'),
        ('1h', 'Recordatorio 1 hora'),
    ]

    # Relaciones
    cita = models.ForeignKey(
        'citas.Cita',
        on_delete=models.CASCADE,
        related_name='whatsapp_reminders'
    )

    # Tipo y programación
    reminder_type = models.CharField(
        max_length=10,
        choices=REMINDER_TYPES,
        db_index=True
    )
    scheduled_time = models.DateTimeField(
        help_text='Momento programado para enviar',
        db_index=True
    )

    # Estado
    is_sent = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Si ya fue enviado'
    )
    sent_at = models.DateTimeField(
        blank=True,
        null=True
    )
    whatsapp_message = models.ForeignKey(
        WhatsAppMessage,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text='Mensaje enviado asociado'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'citas_whatsapp_reminder_schedule'
        ordering = ['scheduled_time']
        indexes = [
            models.Index(fields=['is_sent', 'scheduled_time']),
            models.Index(fields=['cita', 'reminder_type']),
        ]
        # Evitar duplicados
        unique_together = [['cita', 'reminder_type']]

    def __str__(self):
        status = "Enviado" if self.is_sent else "Pendiente"
        return f"{self.get_reminder_type_display()} para cita #{self.cita_id} - {status}"

    def mark_as_sent(self, whatsapp_message):
        """Marca como enviado"""
        from django.utils import timezone
        self.is_sent = True
        self.sent_at = timezone.now()
        self.whatsapp_message = whatsapp_message
        self.save(update_fields=['is_sent', 'sent_at', 'whatsapp_message', 'updated_at'])
