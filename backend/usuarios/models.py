from django.db import models
from django.contrib.auth.models import User
import pytz
from organizacion.models import Sede, Organizacion
from organizacion.managers import OrganizacionManager
from datetime import date, timedelta
from django.utils import timezone
import uuid

class PerfilUsuario(models.Model):
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    organizacion = models.ForeignKey(Organizacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    timezone = models.CharField(max_length=100, choices=TIMEZONE_CHOICES, default='UTC')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    sedes_administradas = models.ManyToManyField(Sede, related_name='administradores', blank=True)
    
    # New fields for client data
    telefono = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    barrio = models.CharField(max_length=100, blank=True, null=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    has_consented_data_processing = models.BooleanField(default=False) # New field for consent
    data_processing_opt_out = models.BooleanField(default=False) # New field for opting out of data processing

    objects = OrganizacionManager(organization_filter_path='organizacion')
    all_objects = models.Manager()

    def __str__(self):
        return self.user.username

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def age(self):
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None


class Usuario(models.Model):
    nombre = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class MagicLinkToken(models.Model):
    """
    Modelo para tokens de Magic Link que permiten acceso temporal sin contraseña.
    Los tokens expiran automáticamente después de 15 minutos.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='magic_link_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)

    class Meta:
        verbose_name = 'Magic Link Token'
        verbose_name_plural = 'Magic Link Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'expires_at']),
        ]

    def save(self, *args, **kwargs):
        """Establece la fecha de expiración a 15 minutos desde la creación."""
        if not self.pk:  # Solo al crear
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Verifica si el token no ha expirado."""
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Magic Link for {self.user.email} - Expires: {self.expires_at}"