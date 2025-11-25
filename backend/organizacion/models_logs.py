"""
Modelo para almacenar logs de la aplicación.
Permite ver logs desde el admin sin necesidad de SSH.
"""
from django.db import models
from django.utils import timezone


class ApplicationLog(models.Model):
    """
    Modelo para almacenar logs de aplicación.
    Se guarda en el schema 'public' (compartido).
    """

    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    # Información del log
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, db_index=True)
    logger_name = models.CharField(max_length=200, db_index=True, help_text='Nombre del logger (ej: organizacion.models)')
    message = models.TextField(help_text='Mensaje del log')

    # Contexto
    organizacion = models.ForeignKey(
        'organizacion.Organizacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        help_text='Organización relacionada (si aplica)'
    )
    user_id = models.IntegerField(null=True, blank=True, help_text='ID del usuario que generó el log')
    user_username = models.CharField(max_length=150, blank=True, help_text='Username del usuario')

    # Información técnica
    pathname = models.CharField(max_length=500, blank=True, help_text='Ruta del archivo que generó el log')
    func_name = models.CharField(max_length=100, blank=True, help_text='Función que generó el log')
    lineno = models.IntegerField(null=True, blank=True, help_text='Línea del código')

    # Traceback para errores
    exc_info = models.TextField(blank=True, help_text='Traceback completo del error')

    # Request info (si está disponible)
    request_path = models.CharField(max_length=500, blank=True, help_text='Path del request HTTP')
    request_method = models.CharField(max_length=10, blank=True, help_text='Método HTTP (GET, POST, etc.)')
    request_user_agent = models.CharField(max_length=500, blank=True, help_text='User agent del request')

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'organizacion_application_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'level']),
            models.Index(fields=['organizacion', '-created_at']),
        ]

    def __str__(self):
        org_str = f"[{self.organizacion.nombre}] " if self.organizacion else ""
        return f"{org_str}{self.level}: {self.message[:100]}"

    @property
    def short_message(self):
        """Retorna versión corta del mensaje para listados"""
        if len(self.message) > 200:
            return self.message[:200] + "..."
        return self.message

    @property
    def is_error(self):
        """True si es un error o crítico"""
        return self.level in ['ERROR', 'CRITICAL']
