#!/usr/bin/env python
"""Script para verificar qué versión del código está en el servidor"""
import os
import subprocess

print("=" * 70)
print("VERIFICACIÓN DE VERSIÓN DEL CÓDIGO")
print("=" * 70)

# Verificar el commit actual
try:
    commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
    print(f"\n✓ Commit actual: {commit}")

    commit_msg = subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode().strip()
    print(f"✓ Último commit: {commit_msg[:100]}...")

except Exception as e:
    print(f"\n✗ Error verificando git: {e}")

# Verificar si services.py tiene los cambios
print("\n" + "=" * 70)
print("VERIFICANDO services.py")
print("=" * 70)

services_path = os.path.join(os.path.dirname(__file__), 'citas', 'services.py')
if os.path.exists(services_path):
    with open(services_path, 'r') as f:
        content = f.read()

    # Buscar líneas clave que indican que el fix está aplicado
    has_distinct = '.distinct()' in content and 'prefetch_related' in content
    has_manual_duration = 'cita.duracion_total = sum(s.duracion_estimada' in content
    has_optimized_mapping = 'for cita in all_citas:' in content and 'for colaborador in cita.colaboradores.all():' in content

    print(f"\n✓ Archivo services.py encontrado")
    print(f"  - Tiene .distinct() en queries: {'✓ SÍ' if has_distinct else '✗ NO'}")
    print(f"  - Calcula duracion_total manualmente: {'✓ SÍ' if has_manual_duration else '✗ NO'}")
    print(f"  - Tiene mapeo optimizado de colaboradores: {'✓ SÍ' if has_optimized_mapping else '✗ NO'}")

    if has_distinct and has_manual_duration and has_optimized_mapping:
        print("\n✓✓✓ EL FIX ESTÁ APLICADO CORRECTAMENTE ✓✓✓")
    else:
        print("\n✗✗✗ EL FIX NO ESTÁ COMPLETO - NECESITAS HACER git pull ✗✗✗")
else:
    print(f"\n✗ No se encontró {services_path}")

print("\n" + "=" * 70)
print("COMANDOS PARA ACTUALIZAR:")
print("=" * 70)
print("""
1. git pull
2. sudo systemctl restart gunicorn  # o el servicio que uses
3. Verifica los logs: sudo journalctl -u gunicorn -n 50
""")
print("=" * 70)
