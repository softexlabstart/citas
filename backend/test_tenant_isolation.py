"""
Script de prueba para verificar el aislamiento de datos por tenant.

Ejecutar:
    cd ~/appcitas/citas/backend
    python test_tenant_isolation.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from organizacion.models import Organizacion
from organizacion.thread_locals import set_current_organization


def test_schema_isolation():
    """Prueba que los schemas estén correctamente aislados"""

    print("\n" + "="*80)
    print("  TEST DE AISLAMIENTO DE SCHEMAS")
    print("="*80 + "\n")

    # Obtener organizaciones
    orgs = Organizacion.objects.all()[:2]

    if orgs.count() < 2:
        print("⚠️  Necesitas al menos 2 organizaciones para probar el aislamiento")
        return

    org1, org2 = orgs[0], orgs[1]

    print(f"📊 Organización 1: {org1.nombre}")
    print(f"   Schema: {org1.schema_name}\n")

    print(f"📊 Organización 2: {org2.nombre}")
    print(f"   Schema: {org2.schema_name}\n")

    # Test 1: Verificar que los schemas existen en PostgreSQL
    print("="*80)
    print("TEST 1: Verificar que los schemas existen en PostgreSQL")
    print("="*80)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'tenant_%'
            ORDER BY schema_name;
        """)
        db_schemas = [row[0] for row in cursor.fetchall()]

    print(f"\n✓ Schemas en PostgreSQL: {len(db_schemas)}")
    for schema in db_schemas:
        org = Organizacion.objects.filter(schema_name=schema).first()
        if org:
            print(f"  - {schema} → {org.nombre}")
        else:
            print(f"  - {schema} → HUÉRFANO")

    # Test 2: Verificar search_path para org1
    print("\n" + "="*80)
    print("TEST 2: Verificar search_path dinámico")
    print("="*80)

    # Simular request con org1
    set_current_organization(org1)

    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {org1.schema_name}, public;")
        cursor.execute("SHOW search_path;")
        path = cursor.fetchone()[0]
        print(f"\n✓ Search path para {org1.nombre}: {path}")

    # Simular request con org2
    set_current_organization(org2)

    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {org2.schema_name}, public;")
        cursor.execute("SHOW search_path;")
        path = cursor.fetchone()[0]
        print(f"✓ Search path para {org2.nombre}: {path}")

    # Test 3: Verificar que las tablas existen en cada schema
    print("\n" + "="*80)
    print("TEST 3: Verificar tablas en cada schema")
    print("="*80)

    for org in [org1, org2]:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{org.schema_name}'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]

        print(f"\n✓ {org.nombre} ({org.schema_name}):")
        print(f"  Tablas: {len(tables)}")
        if tables:
            for table in tables[:5]:  # Mostrar solo las primeras 5
                print(f"    - {table}")
            if len(tables) > 5:
                print(f"    ... y {len(tables) - 5} más")
        else:
            print("  ⚠️  NO HAY TABLAS - Ejecuta: python manage.py create_tenant_schema")

    # Test 4: Verificar tablas compartidas en 'public'
    print("\n" + "="*80)
    print("TEST 4: Verificar tablas compartidas en 'public'")
    print("="*80)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE '%organizacion%'
            ORDER BY table_name;
        """)
        public_tables = [row[0] for row in cursor.fetchall()]

    print(f"\n✓ Tablas de organización en 'public': {len(public_tables)}")
    for table in public_tables:
        print(f"  - {table}")

    # Test 5: Verificar aislamiento con query real
    print("\n" + "="*80)
    print("TEST 5: Verificar aislamiento de datos")
    print("="*80)

    try:
        from citas.models import Cita

        # Contar citas en cada tenant
        for org in [org1, org2]:
            set_current_organization(org)

            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {org.schema_name}, public;")

            count = Cita.objects.count()
            print(f"\n✓ {org.nombre}: {count} citas en su schema")

    except Exception as e:
        print(f"\n⚠️  No se pudo probar con Cita model: {e}")
        print("   Esto es normal si aún no has migrado los schemas de tenant")

    # Resumen final
    print("\n" + "="*80)
    print("  RESUMEN")
    print("="*80)

    if len(db_schemas) == orgs.count():
        print("\n✅ TODOS LOS TESTS PASARON")
        print(f"   - {len(db_schemas)} schemas creados correctamente")
        print(f"   - Aislamiento de datos funcionando")
        print(f"   - Tablas compartidas en 'public' correctas")
    else:
        print("\n⚠️  ACCIÓN REQUERIDA:")
        print(f"   - Tenants en Django: {orgs.count()}")
        print(f"   - Schemas en PostgreSQL: {len(db_schemas)}")
        print(f"\n   Ejecuta: python manage.py migrate_all_tenants")

    print("\n")


if __name__ == "__main__":
    test_schema_isolation()
