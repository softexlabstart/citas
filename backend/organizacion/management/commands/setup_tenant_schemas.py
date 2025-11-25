"""
Comando para configurar schemas de tenants existentes.
Útil para arreglar organizaciones que fueron creadas antes de la automatización.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from organizacion.models import Organizacion
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Configura schemas y tablas para organizaciones existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=int,
            help='ID de organización específica a configurar'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Configurar todas las organizaciones'
        )

    def handle(self, *args, **options):
        if options['org_id']:
            # Configurar una organización específica
            try:
                org = Organizacion.objects.get(id=options['org_id'])
                self.setup_organization(org)
            except Organizacion.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Organización con ID {options['org_id']} no encontrada"))
                return

        elif options['all']:
            # Configurar todas las organizaciones
            organizations = Organizacion.objects.all()
            self.stdout.write(f"Configurando {organizations.count()} organizaciones...")

            for org in organizations:
                self.setup_organization(org)

        else:
            self.stdout.write(self.style.ERROR("Debe especificar --org-id o --all"))

    def setup_organization(self, org):
        """Configura el schema y tablas para una organización"""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Configurando: {org.nombre} (ID: {org.id})")
        self.stdout.write(f"Schema: {org.schema_name}")
        self.stdout.write(f"{'='*60}")

        try:
            with connection.cursor() as cursor:
                # Crear el schema
                self.stdout.write("1. Creando schema...")
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{org.schema_name}"')
                self.stdout.write(self.style.SUCCESS("   ✓ Schema creado"))

                # Copiar tabla citas_cita
                self.stdout.write("2. Creando tabla citas_cita...")
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{org.schema_name}".citas_cita
                    (LIKE public.citas_cita INCLUDING ALL)
                ''')
                self.stdout.write(self.style.SUCCESS("   ✓ Tabla citas_cita creada"))

                # Copiar tabla citas_whatsapp_message
                self.stdout.write("3. Creando tabla citas_whatsapp_message...")
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{org.schema_name}".citas_whatsapp_message
                    (LIKE public.citas_whatsapp_message INCLUDING ALL)
                ''')
                self.stdout.write(self.style.SUCCESS("   ✓ Tabla citas_whatsapp_message creada"))

                # Copiar tabla citas_servicio
                self.stdout.write("4. Creando tabla citas_servicio...")
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{org.schema_name}".citas_servicio
                    (LIKE public.citas_servicio INCLUDING ALL)
                ''')
                self.stdout.write(self.style.SUCCESS("   ✓ Tabla citas_servicio creada"))

                # Copiar tabla citas_cita_servicios
                self.stdout.write("5. Creando tabla citas_cita_servicios...")
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{org.schema_name}".citas_cita_servicios
                    (LIKE public.citas_cita_servicios INCLUDING ALL)
                ''')
                self.stdout.write(self.style.SUCCESS("   ✓ Tabla citas_cita_servicios creada"))

                # Copiar tabla citas_cita_colaboradores
                self.stdout.write("6. Creando tabla citas_cita_colaboradores...")
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{org.schema_name}".citas_cita_colaboradores
                    (LIKE public.citas_cita_colaboradores INCLUDING ALL)
                ''')
                self.stdout.write(self.style.SUCCESS("   ✓ Tabla citas_cita_colaboradores creada"))

            self.stdout.write(self.style.SUCCESS(f"\n✅ Organización {org.nombre} configurada exitosamente\n"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error configurando {org.nombre}: {str(e)}\n"))
            logger.error(f"Error configurando tenant {org.nombre}: {str(e)}", exc_info=True)
