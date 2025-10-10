#!/usr/bin/env python
"""Script para debuggear el problema de disponibilidad directamente"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from citas.models import Cita, Colaborador, Servicio, Sede
from django.utils import timezone
from datetime import timedelta, time, datetime

print("=" * 70)
print("DEBUG: Verificando disponibilidad")
print("=" * 70)

# Parámetros de prueba (ajusta según tus datos)
sede_id = 8
servicio_ids = [30]

print(f"\nBuscando para Sede ID: {sede_id}, Servicio IDs: {servicio_ids}")

# 1. Verificar Sede
try:
    sede = Sede._base_manager.get(id=sede_id)
    print(f"✓ Sede encontrada: {sede.nombre}")
except Sede.DoesNotExist:
    print(f"✗ ERROR: Sede {sede_id} no existe")
    sys.exit(1)

# 2. Verificar Servicios
servicios = Servicio._base_manager.filter(id__in=servicio_ids)
print(f"✓ Servicios encontrados: {servicios.count()}")
for s in servicios:
    print(f"  - {s.nombre} (duración: {s.duracion_estimada} min)")

# 3. Verificar Colaboradores
colaboradores = Colaborador._base_manager.filter(
    sede_id=sede_id,
    servicios__id__in=servicio_ids
).distinct()
print(f"✓ Colaboradores encontrados: {colaboradores.count()}")
for c in colaboradores:
    print(f"  - {c.nombre} (ID: {c.id})")

if not colaboradores.exists():
    print("✗ ERROR: No hay colaboradores para este servicio")
    sys.exit(1)

# 4. Verificar Citas existentes
colaborador_ids = [c.id for c in colaboradores]
days_to_check = 30
day_start = timezone.make_aware(datetime.combine(timezone.now().date(), time.min))
day_end = timezone.make_aware(datetime.combine(timezone.now().date() + timedelta(days=days_to_check), time.max))

all_citas = list(Cita._base_manager.filter(
    colaboradores__id__in=colaborador_ids,
    fecha__gte=day_start,
    fecha__lt=day_end,
    estado__in=['Pendiente', 'Confirmada']
).distinct().prefetch_related('servicios', 'colaboradores').order_by('fecha'))

print(f"\n✓ Citas encontradas en rango ({timezone.now().date()} a {timezone.now().date() + timedelta(days=days_to_check)}): {len(all_citas)}")

for cita in all_citas:
    duracion = sum(s.duracion_estimada for s in cita.servicios.all())
    colaboradores_cita = [c.id for c in cita.colaboradores.all()]
    print(f"  - Cita #{cita.id}: {cita.fecha} | Colaboradores: {colaboradores_cita} | Duración: {duracion} min | Estado: {cita.estado}")

# 5. Mapear citas por colaborador
print(f"\nMapeando citas por colaborador...")
citas_by_colaborador = {cid: [] for cid in colaborador_ids}
for cita in all_citas:
    for colaborador in cita.colaboradores.all():
        if colaborador.id in citas_by_colaborador:
            citas_by_colaborador[colaborador.id].append(cita)

for cid in colaborador_ids:
    nombre = next((c.nombre for c in colaboradores if c.id == cid), f"ID:{cid}")
    print(f"  - Colaborador {nombre} (ID: {cid}): {len(citas_by_colaborador[cid])} citas")

# 6. Verificar para hoy
today = timezone.now().date()
print(f"\nCitas para HOY ({today}):")
for cid in colaborador_ids:
    citas_hoy = [c for c in citas_by_colaborador[cid] if c.fecha.date() == today]
    nombre = next((c.nombre for c in colaboradores if c.id == cid), f"ID:{cid}")
    print(f"  - Colaborador {nombre}: {len(citas_hoy)} citas")
    for cita in citas_hoy:
        print(f"      {cita.fecha} (ID: {cita.id})")

print("\n" + "=" * 70)
