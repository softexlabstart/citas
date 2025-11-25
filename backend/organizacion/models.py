from django.db import models, connection
from django.utils.text import slugify
from django.core.management import call_command
from .managers import OrganizacionManager
import logging

logger = logging.getLogger(__name__)

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

        # Detectar si es una nueva organización
        is_new = self.pk is None

        # Generar schema_name automáticamente si no existe
        if not self.schema_name:
            # tenant_1, tenant_2, etc.
            import uuid
            # Usar los primeros 8 caracteres del slug + timestamp para unicidad
            base_name = self.slug.replace('-', '_')[:20]
            unique_suffix = str(uuid.uuid4())[:8]
            self.schema_name = f"tenant_{base_name}_{unique_suffix}"

        super().save(*args, **kwargs)

        # Si es una nueva organización, crear el schema y ejecutar migraciones
        if is_new:
            self._setup_tenant_schema()

    def _setup_tenant_schema(self):
        """
        Crea el schema de PostgreSQL y las tablas para este tenant.
        Se ejecuta automáticamente cuando se crea una nueva organización.
        """
        try:
            logger.info(f"[TENANT SETUP] Creando schema {self.schema_name} para {self.nombre}")

            with connection.cursor() as cursor:
                # Crear el schema
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')
                logger.info(f"[TENANT SETUP] Schema {self.schema_name} creado exitosamente")

                # Copiar la estructura de las tablas desde public al nuevo schema
                logger.info(f"[TENANT SETUP] Copiando estructura de tablas al schema {self.schema_name}")

                # Copiar tabla citas_cita
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{self.schema_name}".citas_cita
                    (LIKE public.citas_cita INCLUDING ALL)
                ''')

                # Copiar tabla citas_whatsapp_message
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{self.schema_name}".citas_whatsapp_message
                    (LIKE public.citas_whatsapp_message INCLUDING ALL)
                ''')

                # Copiar tabla citas_servicio
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{self.schema_name}".citas_servicio
                    (LIKE public.citas_servicio INCLUDING ALL)
                ''')

                # Copiar tabla citas_cita_servicios (many-to-many)
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{self.schema_name}".citas_cita_servicios
                    (LIKE public.citas_cita_servicios INCLUDING ALL)
                ''')

                # Copiar tabla citas_cita_colaboradores (many-to-many)
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{self.schema_name}".citas_cita_colaboradores
                    (LIKE public.citas_cita_colaboradores INCLUDING ALL)
                ''')

                logger.info(f"[TENANT SETUP] Tablas creadas exitosamente en schema {self.schema_name}")

            logger.info(f"[TENANT SETUP] Tenant {self.nombre} configurado exitosamente")

        except Exception as e:
            logger.error(f"[TENANT SETUP] Error configurando tenant {self.nombre}: {str(e)}", exc_info=True)
            # No lanzar la excepción para no bloquear la creación de la organización
            # El admin puede ver el problema en el Panel de Salud

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

# Import log model
from .models_logs import ApplicationLog
