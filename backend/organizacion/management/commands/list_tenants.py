"""
Comando para listar todos los tenants y sus schemas.

Uso:
    python manage.py list_tenants
"""

from django.core.management.base import BaseCommand
from django.db import connection
from organizacion.models import Organizacion


class Command(BaseCommand):
    help = 'Lista todos los tenants y sus schemas'

    def handle(self, *args, **options):
        # Obtener todos los schemas de PostgreSQL
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY schema_name;
            """)
            db_schemas = [row[0] for row in cursor.fetchall()]

        # Obtener todas las organizaciones
        organizaciones = Organizacion.objects.all().order_by('id')

        self.stdout.write('\n' + '='*80)
        self.stdout.write(
            self.style.SUCCESS('  TENANTS REGISTRADOS')
        )
        self.stdout.write('='*80 + '\n')

        self.stdout.write(f'{'ID':<5} {'Nombre':<30} {'Schema':<30} {'Estado':<10}')
        self.stdout.write('-'*80)

        for org in organizaciones:
            estado = '✓ Activo' if org.is_active else '✗ Inactivo'
            schema_exists = '✓' if org.schema_name in db_schemas else '✗ NO EXISTE'

            self.stdout.write(
                f'{org.id:<5} {org.nombre[:28]:<30} {org.schema_name[:28]:<30} {estado}'
            )
            if schema_exists == '✗ NO EXISTE':
                self.stdout.write(
                    self.style.WARNING(f'      → Schema no creado en PostgreSQL')
                )

        self.stdout.write('\n' + '='*80)
        self.stdout.write(
            self.style.SUCCESS(f'  SCHEMAS EN POSTGRESQL')
        )
        self.stdout.write('='*80 + '\n')

        for schema in db_schemas:
            # Verificar si hay tenant asociado
            try:
                org = Organizacion.objects.get(schema_name=schema)
                self.stdout.write(f'✓ {schema:<40} → {org.nombre}')
            except Organizacion.DoesNotExist:
                if schema == 'public':
                    self.stdout.write(f'✓ {schema:<40} → (Schema compartido)')
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ {schema:<40} → HUÉRFANO (sin tenant asociado)'
                        )
                    )

        self.stdout.write('\n' + '='*80 + '\n')
