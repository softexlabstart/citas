"""
Script para sincronizar usuarios con rol 'colaborador' y crear registros en tabla Colaborador
Ejecutar con: python manage.py shell < sincronizar_colaboradores.py
"""

from usuarios.models import PerfilUsuario
from citas.models import Colaborador
from organizacion.models import _organization

print("\n" + "="*80)
print("SINCRONIZACIÓN: Crear registros de Colaborador para usuarios con rol colaborador")
print("="*80)

# Obtener todos los usuarios con rol de colaborador
perfiles_colaborador = PerfilUsuario.all_objects.filter(role='colaborador') | PerfilUsuario.all_objects.filter(additional_roles__contains=['colaborador'])

print(f"\n📊 Total de perfiles con rol 'colaborador': {perfiles_colaborador.count()}")

creados = 0
actualizados = 0
errores = 0

for perfil in perfiles_colaborador:
    print(f"\n{'─'*80}")
    print(f"👤 Procesando: {perfil.user.username} ({perfil.user.email})")
    print(f"   Organización: {perfil.organizacion.nombre if perfil.organizacion else 'Sin organización'}")
    print(f"   Sede: {perfil.sede.nombre if perfil.sede else 'Sin sede'}")

    # Verificar que tenga organización y sede
    if not perfil.organizacion:
        print(f"   ⚠️  ERROR: No tiene organización asignada. Saltando...")
        errores += 1
        continue

    if not perfil.sede:
        print(f"   ⚠️  ERROR: No tiene sede asignada. Saltando...")
        errores += 1
        continue

    # Establecer el contexto de la organización para el OrganizationManager
    _organization.value = perfil.organizacion

    try:
        # Intentar obtener o crear el Colaborador
        colaborador, created = Colaborador.all_objects.get_or_create(
            usuario=perfil.user,
            defaults={
                'nombre': perfil.user.get_full_name() or perfil.user.username,
                'email': perfil.user.email,
                'sede': perfil.sede,
            }
        )

        if created:
            print(f"   ✅ CREADO nuevo registro de Colaborador (ID: {colaborador.id})")
            creados += 1
        else:
            print(f"   ℹ️  Ya existía registro de Colaborador (ID: {colaborador.id})")
            # Actualizar sede si cambió
            if colaborador.sede != perfil.sede:
                colaborador.sede = perfil.sede
                colaborador.save()
                print(f"   🔄 Actualizada sede a: {perfil.sede.nombre}")
                actualizados += 1

    except Exception as e:
        print(f"   ❌ ERROR al crear/actualizar: {str(e)}")
        errores += 1
    finally:
        # Limpiar el contexto
        _organization.value = None

print("\n" + "="*80)
print("RESUMEN:")
print(f"  ✅ Colaboradores creados: {creados}")
print(f"  🔄 Colaboradores actualizados: {actualizados}")
print(f"  ❌ Errores: {errores}")
print("="*80 + "\n")
