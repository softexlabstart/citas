#!/usr/bin/env python
"""
Script para verificar datos en la base de datos
Ejecutar con: python check_data.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from citas.models import Servicio, Colaborador
from organizacion.models import Sede, Organizacion
from usuarios.models import User, PerfilUsuario

print("=" * 60)
print("VERIFICACIÓN DE DATOS")
print("=" * 60)

# Verificar organizaciones
print("\n1. ORGANIZACIONES:")
orgs = Organizacion.objects.all()
print(f"   Total: {orgs.count()}")
for org in orgs:
    print(f"   - {org.nombre}")

# Verificar sedes
print("\n2. SEDES:")
sedes = Sede.objects.all()
print(f"   Total: {sedes.count()}")
for sede in sedes:
    print(f"   - {sede.nombre} (Org: {sede.organizacion.nombre if sede.organizacion else 'N/A'})")

# Verificar servicios
print("\n3. SERVICIOS:")
servicios = Servicio.all_objects.all()
print(f"   Total: {servicios.count()}")
for servicio in servicios[:10]:  # Mostrar solo los primeros 10
    print(f"   - {servicio.nombre} (Sede: {servicio.sede.nombre if servicio.sede else 'N/A'})")
if servicios.count() > 10:
    print(f"   ... y {servicios.count() - 10} más")

# Verificar colaboradores
print("\n4. COLABORADORES:")
colaboradores = Colaborador.all_objects.all()
print(f"   Total: {colaboradores.count()}")
for colab in colaboradores[:10]:  # Mostrar solo los primeros 10
    print(f"   - {colab.nombre} (Sede: {colab.sede.nombre if colab.sede else 'N/A'})")
if colaboradores.count() > 10:
    print(f"   ... y {colaboradores.count() - 10} más")

# Verificar usuario administrador
print("\n5. USUARIO ADMINISTRADOR:")
try:
    admin = User.objects.get(username='administrador')
    print(f"   Username: {admin.username}")
    print(f"   is_staff: {admin.is_staff}")
    print(f"   is_superuser: {admin.is_superuser}")
    try:
        perfil = admin.perfil
        print(f"   Perfil existe: Sí")
        print(f"   Organización: {perfil.organizacion.nombre if perfil.organizacion else 'NO ASIGNADA'}")
        print(f"   is_sede_admin: {perfil.is_sede_admin}")
    except AttributeError:
        print(f"   Perfil existe: NO")
except User.DoesNotExist:
    print("   ¡Usuario 'administrador' NO EXISTE!")

print("\n" + "=" * 60)
print("FIN DE VERIFICACIÓN")
print("=" * 60)
