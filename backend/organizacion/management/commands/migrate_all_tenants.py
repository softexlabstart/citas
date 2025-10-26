"""
Comando para ejecutar migraciones en todos los schemas de tenants.

Uso:
    python manage.py migrate_all_tenants
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from organizacion.models import Organizacion
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ejecuta migraciones en todos los schemas de tenants existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-public',
            action='store_true',
            help='Saltar migraciones del schema public (compartido)'
        )

    def handle(self, *args, **options):
        skip_public = options.get('skip_public', False)

        # 1. Migrar schema public (tablas compartidas) primero
        if not skip_public:
            self.stdout.write(
                self.style.SUCCESS('\n=== Migrando schema PUBLIC (compartido) ===')
            )
            try:
                call_command('migrate', verbosity=1, interactive=False)
                self.stdout.write(
                    self.style.SUCCESS('✓ Schema public migrado exitosamente\n')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error migrando public: {e}\n')
                )
                return

        # 2. Migrar cada tenant
        organizaciones = Organizacion.objects.filter(is_active=True)
        total = organizaciones.count()

        self.stdout.write(
            self.style.SUCCESS(f'\n=== Migrando {total} tenants ===\n')
        )

        success_count = 0
        error_count = 0

        for i, org in enumerate(organizaciones, 1):
            self.stdout.write(
                f'[{i}/{total}] Migrando: {org.nombre} (schema: {org.schema_name})'
            )

            try:
                call_command(
                    'create_tenant_schema',
                    organization_id=org.id,
                    verbosity=0
                )
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {org.nombre} migrado\n')
                )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error en {org.nombre}: {e}\n')
                )
                logger.error(f'Error migrando tenant {org.nombre}: {e}')

        # 3. Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(f'✓ Exitosos: {success_count}')
        )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'✗ Errores: {error_count}')
            )
        self.stdout.write('='*60 + '\n')
