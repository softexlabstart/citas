"""
Script para vincular colaboradores existentes con sus usuarios
Ejecutar con: python manage.py shell < vincular_colaboradores.py
"""

from usuarios.models import PerfilUsuario
from citas.models import Colaborador
from organizacion.thread_locals import set_current_organization

print("\n" + "="*80)
print("VINCULACIÓN: Conectar colaboradores existentes con usuarios")
print("="*80)

# Obtener todos los usuarios con rol de colaborador
perfiles_colaborador = PerfilUsuario.all_objects.filter(role='colaborador') | PerfilUsuario.all_objects.filter(additional_roles__contains=['colaborador'])

print(f"\n📊 Total de perfiles con rol 'colaborador': {perfiles_colaborador.count()}")

vinculados = 0
creados = 0
errores = 0

for perfil in perfiles_colaborador:
    print(f"\n{'─'*80}")
    print(f"👤 Procesando: {perfil.user.username} ({perfil.user.email})")
    print(f"   Nombre completo: {perfil.user.get_full_name()}")
    print(f"   Email: {perfil.user.email}")
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

    # Establecer el contexto de la organización
    set_current_organization(perfil.organizacion)

    try:
        # Buscar si ya existe un colaborador con este usuario
        colaborador_existente = Colaborador.all_objects.filter(usuario=perfil.user).first()

        if colaborador_existente:
            print(f"   ✅ Ya existe colaborador vinculado (ID: {colaborador_existente.id})")
            vinculados += 1
        else:
            # Buscar colaborador por email en la misma sede
            colaborador_por_email = Colaborador.all_objects.filter(
                email=perfil.user.email,
                sede=perfil.sede
            ).first()

            if colaborador_por_email:
                print(f"   🔍 Encontrado colaborador por email (ID: {colaborador_por_email.id})")
                print(f"      - Nombre en DB: {colaborador_por_email.nombre}")
                print(f"      - Email en DB: {colaborador_por_email.email}")
                print(f"      - Usuario actual: {colaborador_por_email.usuario}")

                if not colaborador_por_email.usuario:
                    # Vincular el usuario a este colaborador
                    colaborador_por_email.usuario = perfil.user
                    colaborador_por_email.save()
                    print(f"   ✅ VINCULADO usuario al colaborador existente!")
                    vinculados += 1
                else:
                    print(f"   ⚠️  Ya tiene usuario vinculado: {colaborador_por_email.usuario.username}")
                    errores += 1
            else:
                # Buscar por nombre en la misma sede
                nombre_completo = perfil.user.get_full_name() or perfil.user.username
                colaborador_por_nombre = Colaborador.all_objects.filter(
                    nombre__iexact=nombre_completo,
                    sede=perfil.sede
                ).first()

                if colaborador_por_nombre:
                    print(f"   🔍 Encontrado colaborador por nombre (ID: {colaborador_por_nombre.id})")
                    print(f"      - Nombre en DB: {colaborador_por_nombre.nombre}")
                    print(f"      - Email en DB: {colaborador_por_nombre.email}")
                    print(f"      - Usuario actual: {colaborador_por_nombre.usuario}")

                    if not colaborador_por_nombre.usuario:
                        # Vincular el usuario a este colaborador
                        colaborador_por_nombre.usuario = perfil.user
                        colaborador_por_nombre.email = perfil.user.email  # Actualizar email también
                        colaborador_por_nombre.save()
                        print(f"   ✅ VINCULADO usuario al colaborador existente!")
                        vinculados += 1
                    else:
                        print(f"   ⚠️  Ya tiene usuario vinculado: {colaborador_por_nombre.usuario.username}")
                        errores += 1
                else:
                    print(f"   ℹ️  No se encontró colaborador existente, intentando crear nuevo...")
                    # Intentar crear uno nuevo
                    colaborador = Colaborador.all_objects.create(
                        usuario=perfil.user,
                        nombre=nombre_completo,
                        email=perfil.user.email,
                        sede=perfil.sede,
                    )
                    print(f"   ✅ CREADO nuevo colaborador (ID: {colaborador.id})")
                    creados += 1

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        errores += 1
    finally:
        # Limpiar el contexto
        set_current_organization(None)

print("\n" + "="*80)
print("RESUMEN:")
print(f"  ✅ Colaboradores vinculados: {vinculados}")
print(f"  ➕ Colaboradores creados: {creados}")
print(f"  ❌ Errores: {errores}")
print("="*80 + "\n")
