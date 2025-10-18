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
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios', help_text='Sede principal del usuario')
    sedes = models.ManyToManyField(Sede, related_name='usuarios_multisede', blank=True, help_text='Sedes a las que tiene acceso el usuario')
    sedes_administradas = models.ManyToManyField(Sede, related_name='administradores', blank=True, help_text='Sedes que puede administrar')
    
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


class PasswordResetToken(models.Model):
    """
    Modelo para tokens de recuperación de contraseña.
    Los tokens expiran automáticamente después de 30 minutos.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'expires_at', 'used']),
        ]

    def save(self, *args, **kwargs):
        """Establece la fecha de expiración a 30 minutos desde la creación."""
        if not self.pk:  # Solo al crear
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Verifica si el token no ha expirado y no ha sido usado."""
        return not self.used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"Password Reset for {self.user.email} - Expires: {self.expires_at}"


class OnboardingProgress(models.Model):
    """
    Modelo para rastrear el progreso del onboarding de nuevos usuarios.
    Ayuda a guiar a los usuarios en la configuración inicial del sistema.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='onboarding_progress',
        verbose_name='Usuario'
    )

    # Pasos completados
    has_created_service = models.BooleanField(
        default=False,
        verbose_name='Ha creado al menos un servicio'
    )
    has_added_collaborator = models.BooleanField(
        default=False,
        verbose_name='Ha agregado al menos un colaborador'
    )
    has_viewed_public_link = models.BooleanField(
        default=False,
        verbose_name='Ha visto su enlace público'
    )
    has_completed_profile = models.BooleanField(
        default=False,
        verbose_name='Ha completado su perfil'
    )

    # Estado general
    is_completed = models.BooleanField(
        default=False,
        verbose_name='Onboarding completado',
        help_text='Marcado como completo cuando el usuario termina todos los pasos esenciales'
    )
    is_dismissed = models.BooleanField(
        default=False,
        verbose_name='Usuario cerró el onboarding',
        help_text='El usuario decidió saltar el onboarding'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completado el')

    class Meta:
        verbose_name = 'Progreso de Onboarding'
        verbose_name_plural = 'Progresos de Onboarding'
        ordering = ['-created_at']

    def __str__(self):
        return f"Onboarding de {self.user.username} - {'Completado' if self.is_completed else 'En progreso'}"

    def mark_as_completed(self):
        """Marca el onboarding como completado"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

    @property
    def completion_percentage(self):
        """Calcula el porcentaje de completitud del onboarding"""
        total_steps = 4  # Número de pasos en el onboarding
        completed = sum([
            self.has_created_service,
            self.has_added_collaborator,
            self.has_viewed_public_link,
            self.has_completed_profile,
        ])
        return int((completed / total_steps) * 100)

    @property
    def pending_steps(self):
        """Retorna lista de pasos pendientes"""
        steps = []
        if not self.has_created_service:
            steps.append('create_service')
        if not self.has_added_collaborator:
            steps.append('add_collaborator')
        if not self.has_viewed_public_link:
            steps.append('view_public_link')
        if not self.has_completed_profile:
            steps.append('complete_profile')
        return steps


class Invitation(models.Model):
    """
    Modelo para invitaciones de usuarios a una organización.
    Permite invitar nuevos usuarios por email con un enlace único que expira en 7 días.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('sede_admin', 'Administrador de Sede'),
        ('colaborador', 'Colaborador'),
        ('miembro', 'Miembro'),
    ]

    email = models.EmailField(
        verbose_name='Email del invitado',
        db_index=True,
        help_text='Email al que se enviará la invitación'
    )
    organization = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name='Organización'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name='Enviado por'
    )
    sede = models.ForeignKey(
        Sede,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitations',
        verbose_name='Sede',
        help_text='Sede a la que se invita al usuario (opcional)'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name='Rol',
        help_text='Rol que tendrá el usuario invitado'
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name='Nombre',
        blank=True
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name='Apellido',
        blank=True
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name='Token de invitación'
    )
    is_accepted = models.BooleanField(
        default=False,
        verbose_name='Aceptada',
        help_text='Indica si la invitación ha sido aceptada'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creada'
    )
    expires_at = models.DateTimeField(
        editable=False,
        verbose_name='Expira'
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Aceptada el'
    )

    class Meta:
        verbose_name = 'Invitación'
        verbose_name_plural = 'Invitaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_accepted']),
            models.Index(fields=['token', 'expires_at']),
            models.Index(fields=['organization', 'is_accepted']),
        ]
        unique_together = [['email', 'organization', 'is_accepted']]

    def save(self, *args, **kwargs):
        """Establece la fecha de expiración a 7 días desde la creación."""
        if not self.pk:  # Solo al crear
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Verifica si la invitación no ha sido aceptada y no ha expirado."""
        return not self.is_accepted and timezone.now() <= self.expires_at

    def accept(self):
        """Marca la invitación como aceptada."""
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()

    def __str__(self):
        status = 'Aceptada' if self.is_accepted else 'Pendiente'
        return f"Invitación a {self.email} - {self.organization.nombre} ({status})"