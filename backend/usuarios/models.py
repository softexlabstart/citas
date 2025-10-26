from django.db import models
from django.contrib.auth.models import User
import pytz
from organizacion.models import Sede, Organizacion
from organizacion.managers import OrganizacionManager
from datetime import date, timedelta
from django.utils import timezone
import uuid

class PerfilUsuario(models.Model):
    """
    Representa la membresía de un usuario en una organización.
    Un usuario puede tener MÚLTIPLES perfiles (uno por organización).

    Sistema de Roles:
    - owner: Propietario de la organización (acceso total)
    - admin: Administrador global de la organización
    - sede_admin: Administrador de sedes específicas
    - colaborador: Empleado/recurso que atiende citas
    - cliente: Usuario final que agenda citas

    Un usuario puede tener múltiples roles simultáneos usando 'additional_roles'.
    Ejemplo: role='colaborador', additional_roles=['cliente']
    """

    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('admin', 'Administrador'),
        ('sede_admin', 'Administrador de Sede'),
        ('colaborador', 'Colaborador'),
        ('cliente', 'Cliente'),
    ]

    # ==================== RELACIONES BÁSICAS ====================
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='perfiles')
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='miembros'
    )

    # ==================== SISTEMA DE ROLES ====================
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='cliente',
        verbose_name='Rol Principal',
        help_text='Rol principal del usuario en esta organización',
        db_index=True
    )

    additional_roles = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Roles Adicionales',
        help_text='Roles adicionales del usuario (ej: ["cliente", "colaborador"])'
    )

    # ==================== ESTADO DE MEMBRESÍA ====================
    is_active = models.BooleanField(
        default=True,
        verbose_name='Membresía Activa',
        help_text='Indica si el usuario tiene acceso activo a esta organización',
        db_index=True
    )

    # ==================== SEDES POR ROL ====================
    sede = models.ForeignKey(
        Sede,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_principales',
        verbose_name='Sede Principal',
        help_text='Sede principal del usuario'
    )

    # Para colaboradores: sedes donde trabaja
    sedes = models.ManyToManyField(
        Sede,
        related_name='colaboradores_multisede',
        blank=True,
        verbose_name='Sedes de Trabajo',
        help_text='Sedes donde este usuario trabaja (para colaboradores)'
    )

    # Para admins de sede: sedes que administra
    sedes_administradas = models.ManyToManyField(
        Sede,
        related_name='administradores',
        blank=True,
        verbose_name='Sedes Administradas',
        help_text='Sedes que este usuario administra (para sede_admin)'
    )

    # ==================== PERMISOS PERSONALIZADOS ====================
    permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Permisos Personalizados',
        help_text='Permisos granulares adicionales en formato JSON'
    )

    # ==================== CONFIGURACIÓN ====================
    timezone = models.CharField(max_length=100, choices=TIMEZONE_CHOICES, default='UTC')

    # ==================== DATOS PERSONALES ====================
    telefono = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    barrio = models.CharField(max_length=100, blank=True, null=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    # ==================== CONSENTIMIENTO DE DATOS ====================
    has_consented_data_processing = models.BooleanField(default=False)
    data_processing_opt_out = models.BooleanField(default=False)

    # ==================== METADATA ====================
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')

    # ==================== MANAGERS ====================
    objects = OrganizacionManager(organization_filter_path='organizacion')
    all_objects = models.Manager()

    class Meta:
        # Constraint: Un usuario solo puede tener un perfil por organización
        unique_together = ('user', 'organizacion')
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        ordering = ['user__username', 'organizacion__nombre']
        indexes = [
            models.Index(fields=['user', 'organizacion']),
        ]

    def __str__(self):
        org_name = self.organizacion.nombre if self.organizacion else 'Sin organización'
        return f"{self.user.username} - {org_name}"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def age(self):
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None

    # ==================== HELPER METHODS ====================

    @property
    def all_roles(self):
        """
        Retorna todos los roles del usuario (principal + adicionales).

        Returns:
            list: Lista de roles, ej: ['colaborador', 'cliente']
        """
        roles = [self.role]
        if self.additional_roles and isinstance(self.additional_roles, list):
            roles.extend(self.additional_roles)
        return list(set(roles))  # Eliminar duplicados

    def has_role(self, role):
        """
        Verifica si el usuario tiene un rol específico (principal o adicional).

        Args:
            role (str): Rol a verificar ('owner', 'admin', 'sede_admin', 'colaborador', 'cliente')

        Returns:
            bool: True si tiene el rol
        """
        return role in self.all_roles

    def has_permission(self, permission_key):
        """
        Verifica si tiene un permiso personalizado específico.

        Args:
            permission_key (str): Clave del permiso en el JSON

        Returns:
            bool: True si tiene el permiso
        """
        if not isinstance(self.permissions, dict):
            return False
        return self.permissions.get(permission_key, False)

    @property
    def can_access_all_sedes(self):
        """
        Retorna True si puede acceder a todas las sedes de la organización.
        Propietarios y administradores tienen acceso total.

        Returns:
            bool: True si tiene acceso a todas las sedes
        """
        return self.role in ['owner', 'admin']

    @property
    def accessible_sedes(self):
        """
        Retorna QuerySet de todas las sedes accesibles según sus roles.

        Returns:
            QuerySet: Sedes a las que el usuario tiene acceso
        """
        if not self.organizacion:
            return Sede.all_objects.none()

        if self.can_access_all_sedes:
            return Sede.all_objects.filter(organizacion=self.organizacion)

        sede_ids = set()

        # Sedes donde trabaja como colaborador
        if self.has_role('colaborador'):
            sede_ids.update(self.sedes.values_list('id', flat=True))

        # Sedes que administra
        if self.has_role('sede_admin'):
            sede_ids.update(self.sedes_administradas.values_list('id', flat=True))

        # Sede principal
        if self.sede:
            sede_ids.add(self.sede.id)

        # Si no tiene sedes específicas pero es cliente, puede acceder a todas
        if self.has_role('cliente') and not sede_ids:
            return Sede.all_objects.filter(organizacion=self.organizacion)

        return Sede.all_objects.filter(id__in=sede_ids)

    @property
    def sedes_acceso(self):
        """
        LEGACY: Mantener compatibilidad con código anterior.
        Retorna las sedes del campo M2M 'sedes' sin filtrado del OrganizacionManager.

        Returns:
            QuerySet: Sedes a las que el usuario tiene acceso
        """
        sede_ids = self.sedes.values_list('id', flat=True)
        return Sede.all_objects.filter(id__in=sede_ids)

    @property
    def display_badge(self):
        """
        Badge visual del rol para mostrar en admin y frontend.

        Returns:
            str: Badge con emoji, ej: "🟢 Colaborador +1"
        """
        badges = {
            'owner': '👑 Propietario',
            'admin': '🔴 Admin',
            'sede_admin': '🟠 Admin Sede',
            'colaborador': '🟢 Colaborador',
            'cliente': '🔵 Cliente',
        }
        badge = badges.get(self.role, self.role)

        if self.additional_roles and len(self.additional_roles) > 0:
            badge += f" +{len(self.additional_roles)}"

        return badge

    @property
    def is_owner(self):
        """Verifica si es propietario de la organización"""
        return self.role == 'owner'

    @property
    def is_admin(self):
        """Verifica si es administrador"""
        return self.role == 'admin'

    @property
    def is_sede_admin(self):
        """Verifica si es administrador de sede"""
        return self.has_role('sede_admin')

    @property
    def is_colaborador(self):
        """Verifica si es colaborador"""
        return self.has_role('colaborador')

    @property
    def is_cliente(self):
        """Verifica si es cliente"""
        return self.has_role('cliente')


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


class FailedLoginAttempt(models.Model):
    """
    SEGURIDAD: Rastrea intentos de login fallidos para prevenir ataques de fuerza bruta.

    Este modelo registra:
    - Intentos fallidos por email/username
    - IP de origen del intento
    - Timestamp de cada intento

    Se usa para:
    1. Bloquear temporalmente después de X intentos
    2. Detectar patrones de ataque
    3. Alertar sobre actividad sospechosa
    """
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField()
    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['email', '-attempted_at']),
            models.Index(fields=['ip_address', '-attempted_at']),
        ]

    def __str__(self):
        return f"Failed login: {self.email} from {self.ip_address} at {self.attempted_at}"

    @staticmethod
    def is_blocked(email, max_attempts=5, lockout_duration_minutes=15):
        """
        Verifica si un email está bloqueado por demasiados intentos fallidos.

        Args:
            email: Email a verificar
            max_attempts: Número máximo de intentos permitidos (default: 5)
            lockout_duration_minutes: Minutos de bloqueo (default: 15)

        Returns:
            tuple: (is_blocked: bool, attempts_count: int, time_remaining: timedelta)
        """
        from django.utils import timezone

        cutoff_time = timezone.now() - timedelta(minutes=lockout_duration_minutes)

        recent_attempts = FailedLoginAttempt.objects.filter(
            email=email.lower(),
            attempted_at__gte=cutoff_time
        ).count()

        is_blocked = recent_attempts >= max_attempts

        if is_blocked:
            # Calcular tiempo restante de bloqueo
            oldest_attempt = FailedLoginAttempt.objects.filter(
                email=email.lower(),
                attempted_at__gte=cutoff_time
            ).order_by('attempted_at').first()

            if oldest_attempt:
                unlock_time = oldest_attempt.attempted_at + timedelta(minutes=lockout_duration_minutes)
                time_remaining = unlock_time - timezone.now()
            else:
                time_remaining = timedelta(0)
        else:
            time_remaining = timedelta(0)

        return is_blocked, recent_attempts, time_remaining

    @staticmethod
    def record_failed_attempt(email, ip_address, user_agent=None):
        """
        Registra un intento de login fallido.

        Args:
            email: Email del intento
            ip_address: IP de origen
            user_agent: User agent del navegador
        """
        import logging
        logger = logging.getLogger(__name__)

        FailedLoginAttempt.objects.create(
            email=email.lower(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Loggear para análisis de seguridad
        is_blocked, attempts, _ = FailedLoginAttempt.is_blocked(email)

        if is_blocked:
            logger.warning(
                f"[SECURITY] Account locked - {email} from {ip_address} - "
                f"{attempts} failed attempts"
            )
        else:
            logger.info(
                f"[SECURITY] Failed login attempt {attempts}/5 - {email} from {ip_address}"
            )

    @staticmethod
    def clear_attempts(email):
        """
        Limpia los intentos fallidos después de un login exitoso.

        Args:
            email: Email del usuario
        """
        FailedLoginAttempt.objects.filter(email=email.lower()).delete()

    @staticmethod
    def cleanup_old_records(days=30):
        """
        Limpia registros antiguos (ejecutar periódicamente via cron/celery).

        Args:
            days: Días de antigüedad para eliminar (default: 30)
        """
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(days=days)
        deleted_count = FailedLoginAttempt.objects.filter(attempted_at__lt=cutoff).delete()[0]
        return deleted_count


class ActiveJWTToken(models.Model):
    """
    SECURITY: Track active JWT tokens for session management.
    Allows limiting number of concurrent sessions per user and token rotation.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_tokens')
    jti = models.CharField(max_length=255, unique=True, db_index=True)  # JWT ID from token
    token = models.TextField()  # Encrypted refresh token
    device_info = models.CharField(max_length=255, blank=True, null=True)  # User agent
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_used = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Active JWT Token'
        verbose_name_plural = 'Active JWT Tokens'
        ordering = ['-last_used']

    def __str__(self):
        return f"{self.user.username} - {self.device_info or 'Unknown Device'}"

    @staticmethod
    def get_active_sessions_count(user):
        """Get number of active sessions for a user."""
        from django.utils import timezone
        return ActiveJWTToken.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        ).count()

    @staticmethod
    def revoke_oldest_session(user):
        """Revoke the oldest session if max sessions exceeded."""
        oldest_session = ActiveJWTToken.objects.filter(user=user).order_by('created_at').first()
        if oldest_session:
            oldest_session.delete()
            return True
        return False

    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired tokens from database."""
        from django.utils import timezone
        deleted_count = ActiveJWTToken.objects.filter(expires_at__lt=timezone.now()).delete()[0]
        return deleted_count