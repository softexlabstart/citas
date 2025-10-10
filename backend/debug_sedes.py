#!/usr/bin/env python
"""Script para verificar y agregar sedes a un usuario."""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
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

    # Preguntar si agregar sedes
    if len(rows) == 0:
        print("\n¿Deseas agregar sedes al usuario? (y/n)")
        respuesta = input().strip().lower()
        if respuesta == 'y':
            # Agregar todas las sedes de la organización
            for sede in sedes_org:
                perfil.sedes.add(sede)
                print(f"✓ Agregada: {sede.nombre}")

            print("\n=== Verificación después de agregar ===")
            sedes_nuevas = perfil.sedes.all()
            print(f"Count: {sedes_nuevas.count()}")
            for sede in sedes_nuevas:
                print(f"  - {sede.id}: {sede.nombre}")

if __name__ == '__main__':
    main()
