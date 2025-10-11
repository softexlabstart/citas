#!/usr/bin/env python
"""Script para verificar y agregar sedes a un usuario."""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from organizacion.models import Sede

def main():
    # Obtener usuario
    username = 'valery'
    try:
        user = User.objects.get(username=username)
        perfil = user.perfil
    except User.DoesNotExist:
        print(f"Usuario '{username}' no encontrado")
        return
    except PerfilUsuario.DoesNotExist:
        print(f"Usuario '{username}' no tiene perfil")
        return

    print(f"\n=== Usuario: {username} ===")
    print(f"ID: {user.id}")
    print(f"Perfil ID: {perfil.id}")
    print(f"Organización: {perfil.organizacion}")
    print(f"Sede principal: {perfil.sede}")

    # Verificar sedes actuales
    print(f"\n=== Sedes asignadas (usando perfil.sedes.all()) ===")
    sedes_actuales = perfil.sedes.all()
    print(f"Count: {sedes_actuales.count()}")
    for sede in sedes_actuales:
        print(f"  - {sede.id}: {sede.nombre}")

    # Verificar sedes actuales usando all_objects
    print(f"\n=== Sedes asignadas (usando Sede.all_objects) ===")
    # Obtener IDs de la tabla intermedia directamente
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.id, s.nombre
            FROM organizacion_sede s
            INNER JOIN usuarios_perfilusuario_sedes ups ON s.id = ups.sede_id
            WHERE ups.perfilusuario_id = %s
        """, [perfil.id])
        rows = cursor.fetchall()
        print(f"Count (DB directa): {len(rows)}")
        for row in rows:
            print(f"  - {row[0]}: {row[1]}")

    # Buscar sedes disponibles de la organización
    print(f"\n=== Sedes disponibles en la organización ===")
    sedes_org = Sede.all_objects.filter(organizacion=perfil.organizacion)
    print(f"Count: {sedes_org.count()}")
    for sede in sedes_org:
        print(f"  - {sede.id}: {sede.nombre}")

    # Verificar qué sedes faltan
    sedes_ids_actuales = {row[0] for row in rows}
    sedes_faltantes = [sede for sede in sedes_org if sede.id not in sedes_ids_actuales]

    if sedes_faltantes:
        print(f"\n=== Sedes faltantes ({len(sedes_faltantes)}) ===")
        for sede in sedes_faltantes:
            print(f"  - {sede.id}: {sede.nombre}")

        print("\n¿Deseas agregar las sedes faltantes al usuario? (y/n)")
        respuesta = input().strip().lower()
        if respuesta == 'y':
            # Agregar sedes faltantes usando through table directamente si es necesario
            from django.db import connection
            for sede in sedes_faltantes:
                # Intentar agregar usando el método add()
                try:
                    perfil.sedes.add(sede)
                    print(f"✓ Agregada: {sede.nombre}")
                except Exception as e:
                    print(f"✗ Error al agregar {sede.nombre}: {e}")
                    # Intentar inserción directa si falla
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO usuarios_perfilusuario_sedes (perfilusuario_id, sede_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                            """, [perfil.id, sede.id])
                        print(f"✓ Agregada (inserción directa): {sede.nombre}")
                    except Exception as e2:
                        print(f"✗ Error en inserción directa: {e2}")

            print("\n=== Verificación después de agregar (consulta directa) ===")
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT s.id, s.nombre
                    FROM organizacion_sede s
                    INNER JOIN usuarios_perfilusuario_sedes ups ON s.id = ups.sede_id
                    WHERE ups.perfilusuario_id = %s
                """, [perfil.id])
                rows_nuevas = cursor.fetchall()
                print(f"Count: {len(rows_nuevas)}")
                for row in rows_nuevas:
                    print(f"  - {row[0]}: {row[1]}")
    else:
        print("\n✓ Todas las sedes de la organización ya están asignadas")

if __name__ == '__main__':
    main()
