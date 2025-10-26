"""
Comando para crear el schema de un tenant y ejecutar migraciones.

Uso:
    python manage.py create_tenant_schema --organization_id=1
    python manage.py create_tenant_schema --slug=barberia-juan
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.core.management import call_command
from organizacion.models import Organizacion
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crea el schema de PostgreSQL para un tenant y ejecuta migraciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization_id',
            type=int,
            help='ID de la organización'
        )
        parser.add_argument(
            '--slug',
            type=str,
            help='Slug de la organización'
        )

    def handle(self, *args, **options):
        org_id = options.get('organization_id')
        slug = options.get('slug')

        if not org_id and not slug:
            raise CommandError('Debes proporcionar --organization_id o --slug')

        # Obtener la organización
        try:
            if org_id:
                org = Organizacion.objects.get(id=org_id)
            else:
                org = Organizacion.objects.get(slug=slug)
        except Organizacion.DoesNotExist:
            raise CommandError(f'Organización no encontrada')

        schema_name = org.schema_name

        self.stdout.write(
            self.style.SUCCESS(f'Creando schema para: {org.nombre}')
        )
        self.stdout.write(f'Schema name: {schema_name}')

        # 1. Crear el schema en PostgreSQL
        with connection.cursor() as cursor:
            # Verificar si el schema ya existe
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = %s;
            """, [schema_name])

            if cursor.fetchone():
                self.stdout.write(
                    self.style.WARNING(f'Schema {schema_name} ya existe. Saltando creación.')
                )
            else:
                # Crear schema
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name};')
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Schema {schema_name} creado')
                )

        # 2. Ejecutar migraciones en el schema del tenant
        self.stdout.write('Ejecutando migraciones en el schema del tenant...')

        # Configurar search_path para que las migraciones se ejecuten en el schema correcto
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {schema_name}, public;')

        try:
            # Ejecutar migraciones de apps de tenant
            tenant_apps = [
                'citas',
                'marketing',
                'guide',
                'reports',
            ]

            for app in tenant_apps:
                self.stdout.write(f'  Migrando app: {app}')
                try:
                    call_command('migrate', app, verbosity=1, interactive=False)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'    Warning al migrar {app}: {e}')
                    )

            # También migrar parte de usuarios (PerfilUsuario)
            self.stdout.write('  Migrando app: usuarios (perfiles)')
            try:
                call_command('migrate', 'usuarios', verbosity=1, interactive=False)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'    Warning al migrar usuarios: {e}')
                )

            # Migrar Sede (parte de organizacion que va al tenant)
            self.stdout.write('  Migrando app: organizacion (sedes)')
            try:
                call_command('migrate', 'organizacion', verbosity=1, interactive=False)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'    Warning al migrar organizacion: {e}')
                )

            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Tenant {org.nombre} creado y migrado exitosamente!')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  Schema: {schema_name}')
            )

        finally:
            # Restaurar search_path a public
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public;')
