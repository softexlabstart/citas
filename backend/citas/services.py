

from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DateTimeField, Sum
from rest_framework.exceptions import ValidationError
from .models import Cita, Horario, Colaborador, Servicio, Bloqueo
from organizacion.models import Sede

def check_appointment_availability(sede, servicios, colaboradores, fecha, cita_id=None):
    """
    Verifica la disponibilidad de una cita, incluyendo horarios de colaboradores y conflictos de citas.
    Lanza una ValidationError si no está disponible.
    """
    if not servicios:
        raise ValidationError({
            'detail': "Debe seleccionar al menos un servicio.",
            'code': 'no_service_selected'
        })

    try:
        duracion_estimada = sum(s.duracion_estimada for s in servicios)
    except AttributeError:
        raise ValidationError({
            'detail': "Uno de los servicios seleccionados no tiene una duración estimada válida.",
            'code': 'invalid_service_duration'
        })

    cita_start_time = fecha
    cita_end_time = cita_start_time + timedelta(minutes=duracion_estimada)

    for colaborador in colaboradores:
        # 1. Check schedule
        dia_semana = fecha.weekday()
        horarios_colaborador = Horario.all_objects.filter(colaborador=colaborador, dia_semana=dia_semana)

        if not horarios_colaborador.exists():
            raise ValidationError({
                'detail': f"El colaborador '{colaborador.nombre}' no tiene horarios definidos para el día seleccionado en esta sede.",
                'code': 'no_schedule_defined'
            })

        is_within_schedule = False
        for horario in horarios_colaborador:
            horario_start_same_day = timezone.make_aware(datetime.combine(cita_start_time.date(), horario.hora_inicio))
            horario_end_same_day = timezone.make_aware(datetime.combine(cita_start_time.date(), horario.hora_fin))

            if horario_end_same_day < horario_start_same_day:
                horario_end_same_day += timedelta(days=1)

            if (horario_start_same_day <= cita_start_time and cita_end_time <= horario_end_same_day):
                is_within_schedule = True
                break
        
        if not is_within_schedule:
            raise ValidationError({
                'detail': f"El colaborador '{colaborador.nombre}' no está disponible en el horario solicitado en esta sede.",
                'code': 'outside_schedule'
            })

        # 2. Check for overlapping appointments
        day_start = timezone.make_aware(datetime.combine(fecha.date(), time.min))
        day_end = day_start + timedelta(days=1)

        potential_conflicts = Cita.all_objects.filter(
            colaboradores=colaborador,
            sede=sede,
            estado__in=['Pendiente', 'Confirmada'],
            fecha__gte=day_start,
            fecha__lt=day_end
        ).annotate(duracion_total=Sum('servicios__duracion_estimada'))
        if cita_id:
            potential_conflicts = potential_conflicts.exclude(id=cita_id)

        for conflict in potential_conflicts:
            conflict_start = conflict.fecha
            conflict_end = conflict_start + timedelta(minutes=conflict.duracion_total or 0)
            if cita_start_time < conflict_end and cita_end_time > conflict_start:
                raise ValidationError({
                    'detail': f"El colaborador '{colaborador.nombre}' ya tiene una cita agendada que se superpone con el horario solicitado.",
                    'code': 'appointment_conflict'
                })

        # 3. Check for overlapping blocks
        bloqueos_conflictivos = Bloqueo.all_objects.filter(
            colaborador=colaborador,
            fecha_inicio__lt=cita_end_time,
            fecha_fin__gt=cita_start_time
        )
        if bloqueos_conflictivos.exists():
            raise ValidationError({
                'detail': f"El colaborador '{colaborador.nombre}' tiene un bloqueo de tiempo en el horario solicitado: {bloqueos_conflictivos.first().motivo}",
                'code': 'block_conflict'
            })

    return True

def _generate_slots(current_date, horarios, citas, bloqueos, intervalo, step, colaborador=None):
    processed_slots = set()
    
    daily_slots = []

    for horario in horarios:
        schedule_start = timezone.make_aware(datetime.combine(current_date, horario.hora_inicio))
        schedule_end = timezone.make_aware(datetime.combine(current_date, horario.hora_fin))

        if schedule_end <= schedule_start:
            schedule_end += timedelta(days=1)

        busy_times = []
        for cita in citas:
            start = cita.fecha
            # Ensure duracion_total is not None
            duration = cita.duracion_total if hasattr(cita, 'duracion_total') and cita.duracion_total is not None else sum(s.duracion_estimada for s in cita.servicios.all())
            end = start + timedelta(minutes=duration)
            if start < schedule_end and end > schedule_start:
                busy_times.append((start, end))

        for bloqueo in bloqueos:
            start = max(bloqueo.fecha_inicio, schedule_start)
            end = min(bloqueo.fecha_fin, schedule_end)
            if start < end:
                busy_times.append((start, end))
        
        busy_times.sort()

        current_time = schedule_start
        while current_time < schedule_end:
            slot_start = current_time
            slot_end = slot_start + intervalo

            if slot_end > schedule_end:
                break

            is_available = True
            # Find the first conflict if any
            conflict = next((busy for busy in busy_times if slot_start < busy[1] and slot_end > busy[0]), None)

            if conflict:
                is_available = False
                # Jump to the end of the conflict to start searching for the next slot
                current_time = conflict[1]
            
            if is_available:
                if slot_start not in processed_slots and slot_start > timezone.now():
                    slot_info = {
                        'start': slot_start.isoformat(),
                        'end': slot_end.isoformat(),
                    }
                    if colaborador:
                        slot_info['recurso'] = {'id': colaborador.id, 'nombre': colaborador.nombre}
                    else:
                        slot_info['status'] = 'disponible'
                    
                    daily_slots.append(slot_info)
                    processed_slots.add(slot_start)
                
                current_time += step
    
    return daily_slots

def get_available_slots(colaborador_id, fecha_str, servicio_ids):
    """
    Obtiene los slots de tiempo disponibles para un colaborador en una fecha específica,
    considerando la duración del servicio.
    """
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        colaborador = Colaborador.all_objects.get(id=colaborador_id)
        servicios = Servicio.all_objects.filter(id__in=servicio_ids)
        if not servicios.exists():
            raise ValueError('IDs de servicio inválidos.')
        duracion_total_servicios = sum(s.duracion_estimada for s in servicios)
        intervalo = timedelta(minutes=duracion_total_servicios)
        step = timedelta(minutes=15)
    except (ValueError, Colaborador.DoesNotExist, Servicio.DoesNotExist):
        raise ValueError('Formato de fecha, ID de colaborador o ID de servicio inválido.')

    dia_semana = fecha.weekday()
    horarios_colaborador = Horario.all_objects.filter(colaborador=colaborador, dia_semana=dia_semana).order_by('hora_inicio')
    if not horarios_colaborador.exists():
        return []

    citas_del_dia = Cita.all_objects.filter(
        colaboradores=colaborador, fecha__date=fecha, estado__in=['Pendiente', 'Confirmada']
    ).prefetch_related('servicios').annotate(
        duracion_total=Sum('servicios__duracion_estimada')
    ).order_by('fecha')
    
    day_start = timezone.make_aware(datetime.combine(fecha, time.min))
    day_end = timezone.make_aware(datetime.combine(fecha, time.max))
    bloqueos_del_dia = Bloqueo.all_objects.filter(
        colaborador=colaborador,
        fecha_inicio__lte=day_end,
        fecha_fin__gte=day_start
    ).order_by('fecha_inicio')
    
    available_slots = _generate_slots(fecha, horarios_colaborador, citas_del_dia, bloqueos_del_dia, intervalo, step)
    available_slots.sort(key=lambda x: x['start'])
    return available_slots

def find_next_available_slots(servicio_ids, sede_id, limit=5):
    """
    Finds the next available slots for a given service at a specific location,
    across all available resources.
    """
    if not servicio_ids:
        raise ValueError("Debe proporcionar al menos un ID de servicio.")

    try:
        sede = Sede.all_objects.get(id=sede_id)
    except Sede.DoesNotExist:
        raise ValueError(f"La sede con id={sede_id} no existe.")

    servicios = Servicio.all_objects.filter(id__in=servicio_ids)
    if not servicios.exists():
        raise ValueError(f"Alguno de los servicios con ids={servicio_ids} no existe.")

    for servicio in servicios:
        if servicio.sede.id != sede.id:
            raise ValueError(f"El servicio '{servicio.nombre}' (id={servicio.id}) pertenece a la sede '{servicio.sede.nombre}' (id={servicio.sede.id}), no a la sede seleccionada '{sede.nombre}' (id={sede.id}).")

    duracion_total_servicios = sum(s.duracion_estimada for s in servicios)
    intervalo = timedelta(minutes=duracion_total_servicios)
    step = timedelta(minutes=15)

    colaboradores = Colaborador.all_objects.filter(
        sede_id=sede_id,
        servicios__id__in=servicio_ids
    ).distinct()
    if not colaboradores.exists():
        raise ValidationError("No se encontraron colaboradores para el servicio seleccionado en esta sede.")

    colaborador_ids = [c.id for c in colaboradores]
    all_found_slots = []
    
    days_to_check = 30

    end_date = timezone.now().date() + timedelta(days=days_to_check)
    day_start = timezone.make_aware(datetime.combine(timezone.now().date(), time.min))
    day_end = timezone.make_aware(datetime.combine(end_date, time.max))

    all_horarios = Horario.all_objects.filter(colaborador_id__in=colaborador_ids).order_by('hora_inicio')
    all_citas = Cita.all_objects.filter(
        colaboradores__id__in=colaborador_ids, fecha__gte=day_start, fecha__lt=day_end, estado__in=['Pendiente', 'Confirmada']
    ).prefetch_related('servicios', 'colaboradores').annotate(
        duracion_total=Sum('servicios__duracion_estimada')
    ).order_by('fecha')
    all_bloqueos = Bloqueo.all_objects.filter(colaborador_id__in=colaborador_ids, fecha_inicio__lte=day_end, fecha_fin__gte=day_start).order_by('fecha_inicio')

    horarios_by_colaborador = {cid: list(filter(lambda h: h.colaborador_id == cid, all_horarios)) for cid in colaborador_ids}
    citas_by_colaborador = {cid: list(filter(lambda c: cid in [col.id for col in c.colaboradores.all()], all_citas)) for cid in colaborador_ids}
    bloqueos_by_colaborador = {cid: list(filter(lambda b: b.colaborador_id == cid, all_bloqueos)) for cid in colaborador_ids}

    for i in range(days_to_check):
        current_date = timezone.now().date() + timedelta(days=i)
        dia_semana = current_date.weekday()
        
        daily_slots_for_all_colaboradores = []
        for colaborador in colaboradores:
            horarios_colaborador = [h for h in horarios_by_colaborador.get(colaborador.id, []) if h.dia_semana == dia_semana]
            if not horarios_colaborador:
                continue

            citas_del_dia = [c for c in citas_by_colaborador.get(colaborador.id, []) if c.fecha.date() == current_date]
            bloqueos_del_dia = [b for b in bloqueos_by_colaborador.get(colaborador.id, []) if b.fecha_inicio.date() <= current_date and b.fecha_fin.date() >= current_date]

            slots = _generate_slots(current_date, horarios_colaborador, citas_del_dia, bloqueos_del_dia, intervalo, step, colaborador=colaborador)
            daily_slots_for_all_colaboradores.extend(slots)

        daily_slots_for_all_colaboradores.sort(key=lambda x: x['start'])
        
        for slot in daily_slots_for_all_colaboradores:
            if len(all_found_slots) < limit:
                all_found_slots.append(slot)
            else:
                break
        
        if len(all_found_slots) >= limit:
            break
    
    return all_found_slots
