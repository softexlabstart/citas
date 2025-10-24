"""
Script para ver TODOS los perfiles y sus roles
Ejecutar con: python manage.py shell < debug_todos_perfiles.py
"""

from usuarios.models import PerfilUsuario

print("\n" + "="*80)
print("TODOS LOS PERFILES Y SUS ROLES")
print("="*80)

perfiles = PerfilUsuario.all_objects.all()

print(f"\n📊 Total de perfiles: {perfiles.count()}")

for perfil in perfiles:
    print(f"\n{'─'*60}")
    print(f"ID: {perfil.id}")
    print(f"Usuario: {perfil.user.username} ({perfil.user.email})")
    print(f"Rol principal: {perfil.role}")
    print(f"Roles adicionales: {perfil.additional_roles}")
    print(f"Organización: {perfil.organizacion.nombre if perfil.organizacion else 'Sin organización'}")
    print(f"Sede: {perfil.sede.nombre if perfil.sede else 'Sin sede'}")
    print(f"Activo: {perfil.is_active}")

print("\n" + "="*80)
print("FIN")
print("="*80 + "\n")
