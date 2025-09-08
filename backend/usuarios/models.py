from django.db import models
from django.contrib.auth.models import User
import pytz
from organizacion.models import Sede

class PerfilUsuario(models.Model):
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    timezone = models.CharField(max_length=100, choices=TIMEZONE_CHOICES, default='UTC')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    sedes_administradas = models.ManyToManyField(Sede, related_name='administradores', blank=True)

    def __str__(self):
        return self.user.username


class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre