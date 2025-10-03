from django.db import models
from django.utils.text import slugify
from .managers import OrganizacionManager

class Organizacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, db_index=True)
    # In the future, you can add fields for subscription plans, status, etc.

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Sede(models.Model):
    organizacion = models.ForeignKey(Organizacion, on_delete=models.CASCADE, related_name='sedes', null=True)
    nombre = models.CharField(max_length=100, db_index=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    objects = OrganizacionManager(organization_filter_path='organizacion')
    all_objects = models.Manager() # To access all objects without filtering

    def __str__(self):
        # The string representation will be more informative with the organization name
        return f"{self.organizacion.nombre} - {self.nombre}" if self.organizacion else self.nombre
