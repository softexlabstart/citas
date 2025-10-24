"""
Script para normalizar los estados de las citas (quitar acentos)
Ejecutar con: python manage.py shell < normalizar_estados.py
"""

from citas.models import Cita

print("\n" + "="*80)
print("NORMALIZACIÓN: Quitar acentos de los estados de las citas")
print("="*80)

# Mapeo de estados con acento a sin acento
estados_mapeo = {
    'Asistió': 'Asistio',
    'No Asistió': 'No Asistio',
}

total_actualizados = 0

for estado_viejo, estado_nuevo in estados_mapeo.items():
    print(f"\n📝 Actualizando '{estado_viejo}' → '{estado_nuevo}'")

    # Contar cuántas citas tienen este estado
    citas_con_estado = Cita.all_objects.filter(estado=estado_viejo)
    cantidad = citas_con_estado.count()

    if cantidad > 0:
        # Actualizar todas las citas
        citas_actualizadas = citas_con_estado.update(estado=estado_nuevo)
        print(f"   ✅ Actualizadas {citas_actualizadas} citas")
        total_actualizados += citas_actualizadas
    else:
        print(f"   ℹ️  No se encontraron citas con este estado")

print("\n" + "="*80)
print(f"RESUMEN: Total de citas actualizadas: {total_actualizados}")
print("="*80)

# Mostrar estadísticas de estados actuales
print("\n📊 Estados actuales en la base de datos:")
estados_actuales = Cita.all_objects.values('estado').annotate(
    cantidad=Count('id')
).order_by('-cantidad')

from django.db.models import Count
estados_actuales = Cita.all_objects.values('estado').annotate(
    cantidad=Count('id')
).order_by('-cantidad')

for item in estados_actuales:
    print(f"   - {item['estado']}: {item['cantidad']} citas")

print("\n")
