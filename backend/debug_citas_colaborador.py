"""
Script para verificar las citas asignadas a un colaborador específico
Ejecutar con: python manage.py shell < debug_citas_colaborador.py
"""

from citas.models import Colaborador, Cita
from django.db.models import Count

print("\n" + "="*80)
print("DEBUG: Citas por colaborador")
print("="*80)

# Obtener todos los colaboradores
colaboradores = Colaborador.all_objects.all()

print(f"\n📊 Total de colaboradores: {colaboradores.count()}")

for colaborador in colaboradores:
    print(f"\n{'─'*80}")
    print(f"👤 Colaborador ID: {colaborador.id}")
    print(f"   Nombre: {colaborador.nombre}")
    print(f"   Email: {colaborador.email}")
    print(f"   Usuario: {colaborador.usuario.username if colaborador.usuario else 'Sin usuario'}")
    print(f"   Sede: {colaborador.sede.nombre if colaborador.sede else 'Sin sede'}")

    # Contar citas por estado
    citas = Cita.all_objects.filter(colaboradores__id=colaborador.id)
    total_citas = citas.count()

    print(f"\n   📅 Total de citas asignadas: {total_citas}")

    if total_citas > 0:
        estados = citas.values('estado').annotate(cantidad=Count('id')).order_by('-cantidad')
        print(f"   Distribución por estado:")
        for estado in estados:
            print(f"      - {estado['estado']}: {estado['cantidad']} citas")

        # Mostrar primeras 3 citas
        print(f"\n   Ejemplo de citas:")
        for cita in citas[:3]:
            print(f"      - ID: {cita.id}, Cliente: {cita.nombre}, Fecha: {cita.fecha}, Estado: {cita.estado}")

print("\n" + "="*80)
print("FIN")
print("="*80 + "\n")
