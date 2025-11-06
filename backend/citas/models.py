from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from organizacion.models import Sede

# Create your models here.

class Horario(models.Model):
    DIA_SEMANA_CHOICES = [
        (0, _('Lunes')),
        (1, _('Martes')),
        (2, _('Miércoles')),
        (3, _('Jueves')),
        (4, _('Viernes')),
        (5, _('Sábado')),
        (6, _('Domingo')),
    ]

    colaborador = models.ForeignKey('Colaborador', on_delete=models.CASCADE, related_name='horarios', null=True, blank=True)
    dia_semana = models.IntegerField(choices=DIA_SEMANA_CHOICES, db_index=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    # NOTA: Filtrado manual en vistas
    objects = models.Manager()
    all_objects = models.Manager()

    def __str__(self):
        colaborador_nombre = self.colaborador.nombre if self.colaborador else _("Sin asignar")
        return f"{colaborador_nombre} - {self.get_dia_semana_display()} ({self.hora_inicio} - {self.hora_fin})"


class Servicio(models.Model):
    nombre = models.CharField(max_length=100, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    duracion_estimada = models.IntegerField(default=30) # Duration in minutes
    precio = models.DecimalField(max_digits=10, decimal_places=0, default=0.00, help_text=_("Precio del servicio"))
    metadata = models.JSONField(blank=True, null=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='servicios')

    # NOTA: Filtrado manual en vistas en lugar de OrganizacionManager
    # para evitar conflictos con serializers y relaciones ManyToMany
    objects = models.Manager()  # Manager por defecto sin filtrado automático
    all_objects = models.Manager()

    class Meta:
        unique_together = ('sede', 'nombre')

    def __str__(self):
        return self.nombre


class Colaborador(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='colaboradores')
    nombre = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(max_length=254, blank=True, null=True, db_index=True)
    servicios = models.ManyToManyField('Servicio', related_name='colaboradores', blank=True)
    descripcion = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='colaboradores')

    # NOTA: Filtrado manual en vistas para evitar conflictos
    objects = models.Manager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ('sede', 'nombre')

    def __str__(self):
        return self.nombre

class Bloqueo(models.Model):
    """Represents a block of time when a resource is unavailable for non-appointment reasons."""
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name='bloqueos', null=True, blank=True)
    motivo = models.CharField(max_length=100, help_text=_("Ej: Almuerzo, Reunión, Cita personal"))
    fecha_inicio = models.DateTimeField(db_index=True)
    fecha_fin = models.DateTimeField(db_index=True)

    # NOTA: Filtrado manual en vistas
    objects = models.Manager()
    all_objects = models.Manager()

    def __str__(self):
        colaborador_nombre = self.colaborador.nombre if self.colaborador else _("Sin asignar")
        return f"Bloqueo de {colaborador_nombre}: {self.motivo} ({self.fecha_inicio.strftime('%Y-%m-%d %H:%M')})"


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', _('Pendiente')),
        ('Confirmada', _('Confirmada')),
        ('Cancelada', _('Cancelada')),
        ('Asistio', _('Asistió')),
        ('No Asistio', _('No Asistió')),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='citas', null=True, blank=True)
    nombre = models.CharField(max_length=100, db_index=True)
    fecha = models.DateTimeField(db_index=True)
    servicios = models.ManyToManyField(Servicio, related_name='citas')
    colaboradores = models.ManyToManyField('Colaborador', related_name='citas', blank=True)
    confirmado = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente', db_index=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='citas')
    comentario = models.TextField(blank=True, null=True)

    # Campos para reservas de invitados (guest bookings)
    email_cliente = models.EmailField(max_length=254, blank=True, null=True, db_index=True,
                                      help_text=_("Email del cliente para reservas como invitado"))
    telefono_cliente = models.CharField(max_length=20, blank=True, null=True,
                                        help_text=_("Teléfono del cliente para reservas como invitado"))

    # Tipo de cita: registrado vs invitado
    TIPO_CITA_CHOICES = [
        ('registrado', _('Usuario Registrado')),
        ('invitado', _('Invitado (sin cuenta)')),
    ]
    tipo_cita = models.CharField(
        max_length=20,
        choices=TIPO_CITA_CHOICES,
        default='registrado',
        db_index=True,
        help_text=_("Indica si la cita fue creada por usuario registrado o invitado público")
    )

    # Token para que invitados gestionen su cita sin login
    token_invitado = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Token único para que invitados vean/cancelen su cita")
    )

    # NOTA: Filtrado manual en vistas para evitar conflictos con relaciones
    objects = models.Manager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"