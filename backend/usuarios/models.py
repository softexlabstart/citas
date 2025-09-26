from django.db import models
from django.contrib.auth.models import User
import pytz
from organizacion.models import Sede, Organizacion
from organizacion.managers import OrganizacionManager
from datetime import date

class PerfilUsuario(models.Model):
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    organizacion = models.ForeignKey(Organizacion.Organizacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
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