from django.db import models
from django.utils.text import slugify
from .managers import OrganizacionManager

class Organizacion(models.Model):  # type: ignore
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

    # Configuración de notificaciones WhatsApp
    whatsapp_enabled = models.BooleanField(
        default=False,
        help_text='Activar notificaciones por WhatsApp'
    )
    whatsapp_sender_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Nombre del negocio que aparecerá en los mensajes'
    )
    whatsapp_reminder_24h_enabled = models.BooleanField(
        default=True,
        help_text='Enviar recordatorio 24 horas antes de la cita'
    )
    whatsapp_reminder_1h_enabled = models.BooleanField(
        default=True,
        help_text='Enviar recordatorio 1 hora antes de la cita'
    )
    whatsapp_confirmation_enabled = models.BooleanField(
        default=True,
        help_text='Enviar confirmación al crear la cita'
    )
    whatsapp_cancellation_enabled = models.BooleanField(
        default=True,
        help_text='Enviar notificación al cancelar la cita'
    )

    # Plantillas personalizables de WhatsApp
    whatsapp_template_confirmation = models.TextField(
        blank=True,
        default='',
        help_text='Plantilla de confirmación. Variables: {nombre}, {fecha}, {hora}, {sede}, {servicios}, {colaboradores}'
    )
    whatsapp_template_reminder_24h = models.TextField(
        blank=True,
        default='',
        help_text='Plantilla recordatorio 24h. Variables: {nombre}, {fecha}, {hora}, {sede}, {servicios}, {colaboradores}'
    )
    whatsapp_template_reminder_1h = models.TextField(
        blank=True,
        default='',
        help_text='Plantilla recordatorio 1h. Variables: {nombre}, {fecha}, {hora}, {sede}, {servicios}, {colaboradores}'
    )
    whatsapp_template_cancellation = models.TextField(
        blank=True,
        default='',
        help_text='Plantilla de cancelación. Variables: {nombre}, {fecha}, {hora}, {sede}, {razon}'
    )

    # Configuración de branding personalizado
    usar_branding_personalizado = models.BooleanField(
        default=False,
        help_text='Activar branding personalizado para la página pública'
    )
    logo = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True,
        help_text='Logo de la organización (máx. 2MB, formatos: PNG, JPG, SVG)'
    )
    color_primario = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        default='#007bff',
        help_text='Color principal en formato hex (ej: #007bff)'
    )
    color_secundario = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        default='#6c757d',
        help_text='Color secundario en formato hex'
    )
    color_texto = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        default='#212529',
        help_text='Color del texto en formato hex'
    )
    color_fondo = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        default='#ffffff',
        help_text='Color de fondo en formato hex'
    )
    texto_bienvenida = models.TextField(
        blank=True,
        null=True,
        help_text='Mensaje de bienvenida personalizado para la página pública'
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

class Sede(models.Model):  # type: ignore
    organizacion = models.ForeignKey(Organizacion, on_delete=models.CASCADE, related_name='sedes', null=True)
    nombre = models.CharField(max_length=100, db_index=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    objects = OrganizacionManager(organization_filter_path='organizacion')
    all_objects = models.Manager()  # To access all objects without filtering

    def __str__(self) -> str:
        # The string representation will be more informative with the organization name
        return f"{self.organizacion.nombre} - {self.nombre}" if self.organizacion else self.nombre
