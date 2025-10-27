from django.db import models
from django.utils.text import slugify
from .managers import OrganizacionManager

class Organizacion(models.Model):
    """
    Modelo de Organización (Tenant) con soporte para database-per-tenant.
    Cada organización puede tener su propia base de datos o schema PostgreSQL.
    """
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, db_index=True)

    # DATABASE-PER-TENANT: Schema isolation
    schema_name = models.CharField(
        max_length=63,  # PostgreSQL max identifier length
        unique=True,
        blank=True,
        db_index=True,
        help_text='PostgreSQL schema name for this tenant'
    )

    # Database configuration (para clientes enterprise con DB dedicada)
    database_name = models.CharField(
        max_length=63,
        blank=True,
        null=True,
        help_text='Nombre de base de datos dedicada (solo para enterprise)'
    )

    # Estado del tenant
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Si está activo el tenant'
    )

    # Configuración de agendamiento público
    permitir_agendamiento_publico = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Permitir que usuarios sin cuenta agenden citas públicamente'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'organizacion_organizacion'
        # Esta tabla SIEMPRE va en el schema 'public' (shared)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)

        # Generar schema_name automáticamente si no existe
        if not self.schema_name:
            # tenant_1, tenant_2, etc.
            import uuid
            # Usar los primeros 8 caracteres del slug + timestamp para unicidad
            base_name = self.slug.replace('-', '_')[:20]
            unique_suffix = str(uuid.uuid4())[:8]
            self.schema_name = f"tenant_{base_name}_{unique_suffix}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    def get_database_alias(self):
        """
        Retorna el alias de base de datos a usar para este tenant.
        - Si tiene database_name: usa esa BD dedicada
        - Si no: usa 'default' pero con schema routing
        """
        if self.database_name:
            return f"tenant_{self.id}"
        return 'default'

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
