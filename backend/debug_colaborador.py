"""
Script de diagnóstico para verificar por qué los colaboradores no ven sus citas
Ejecutar con: python manage.py shell < debug_colaborador.py
"""

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from citas.models import Colaborador, Cita

print("\n" + "="*80)
print("DIAGNÓSTICO: Colaboradores sin citas")
print("="*80)

# Obtener todos los usuarios con rol de colaborador
perfiles_colaborador = PerfilUsuario.all_objects.filter(role='colaborador') | PerfilUsuario.all_objects.filter(additional_roles__contains=['colaborador'])

print(f"\n📊 Total de perfiles con rol 'colaborador': {perfiles_colaborador.count()}")

for perfil in perfiles_colaborador:
    print(f"\n{'─'*80}")
    print(f"👤 Usuario: {perfil.user.username} ({perfil.user.email})")
    print(f"   Rol principal: {perfil.role}")
    print(f"   Roles adicionales: {perfil.additional_roles}")
    print(f"   Organización: {perfil.organizacion.nombre if perfil.organizacion else 'Sin organización'}")
    print(f"   Sede: {perfil.sede.nombre if perfil.sede else 'Sin sede'}")

    # Verificar si existe un Colaborador vinculado
    colaborador_exists = Colaborador.all_objects.filter(usuario=perfil.user).exists()
    print(f"\n   ¿Existe registro en Colaborador? {colaborador_exists}")

    if colaborador_exists:
        colaborador = Colaborador.all_objects.get(usuario=perfil.user)
        print(f"   Colaborador ID: {colaborador.id}")
        print(f"   Colaborador nombre: {colaborador.nombre}")
        print(f"   Colaborador sede: {colaborador.sede.nombre if colaborador.sede else 'Sin sede'}")

        # Contar citas asignadas
        citas_count = Cita.all_objects.filter(colaboradores__id=colaborador.id).count()
        print(f"\n   📅 Citas asignadas (total): {citas_count}")

        if citas_count > 0:
            print(f"\n   Detalle de citas:")
            citas = Cita.all_objects.filter(colaboradores__id=colaborador.id)[:5]
            for cita in citas:
                print(f"      - ID: {cita.id}, Cliente: {cita.nombre}, Fecha: {cita.fecha}, Estado: {cita.estado}, Sede: {cita.sede.nombre}")

            if citas_count > 5:
                print(f"      ... y {citas_count - 5} citas más")
    else:
        print(f"   ⚠️  NO existe registro en tabla Colaborador para este usuario")
        print(f"   Esto significa que no puede ver ninguna cita asignada")

print("\n" + "="*80)
print("FIN DEL DIAGNÓSTICO")
print("="*80 + "\n")
