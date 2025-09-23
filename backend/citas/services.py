
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DateTimeField
from rest_framework.exceptions import ValidationError
from .models import Cita, Horario, Colaborador, Servicio, Bloqueo
from organizacion.models import Sede

def check_appointment_availability(sede, servicios, colaboradores, fecha, cita_id=None):
    """
    Verifica la disponibilidad de una cita, incluyendo horarios de colaboradores y conflictos de citas.
    Lanza una ValidationError si no está disponible.
    """
    if not servicios:
        raise ValidationError("Debe seleccionar al menos un servicio.")

    try:
        duracion_estimada = sum(s.duracion_estimada for s in servicios)
    except AttributeError:
        raise ValidationError("Uno de los servicios seleccionados no tiene una duración estimada válida.")

    cita_start_time = fecha
    cita_end_time = cita_start_time + timedelta(minutes=duracion_estimada)

    # Annotate existing appointments once outside the loop for efficiency.
    existing_appointments = Cita.objects.annotate(
        end_time=ExpressionWrapper(
            F('fecha') + F('servicios__duracion_estimada') * timedelta(minutes=1),
            output_field=DateTimeField()
        )
    )

    for colaborador in colaboradores:
        # 1. Check schedule
        dia_semana = fecha.weekday()
        horarios_colaborador = Horario.objects.filter(colaborador=colaborador, dia_semana=dia_semana)

        if not horarios_colaborador.exists():
            raise ValidationError(f"El colaborador '{colaborador.nombre}' no tiene horarios definidos para el día seleccionado en esta sede.")

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
            raise ValidationError(f"El colaborador '{colaborador.nombre}' no está disponible en el horario solicitado en esta sede.")

        # 2. Check for overlapping appointments
        day_start = timezone.make_aware(datetime.combine(fecha.date(), time.min))
        day_end = day_start + timedelta(days=1)

        potential_conflicts = Cita.objects.filter(
            colaboradores=colaborador,
            sede=sede,
            estado__in=['Pendiente', 'Confirmada'],
            fecha__gte=day_start,
            fecha__lt=day_end
        )
        if cita_id:
            potential_conflicts = potential_conflicts.exclude(id=cita_id)

        for conflict in potential_conflicts:
            conflict_start = conflict.fecha
            conflict_end = conflict_start + timedelta(minutes=sum(s.duracion_estimada for s in conflict.servicios.all()))
            # Standard overlap check: (StartA < EndB) and (EndA > StartB)
            if cita_start_time < conflict_end and cita_end_time > conflict_start:
                raise ValidationError(f"El colaborador '{colaborador.nombre}' ya tiene una cita agendada que se superpone con el horario solicitado.")

        # 3. Check for overlapping blocks
        bloqueos_conflictivos = Bloqueo.objects.filter(
            colaborador=colaborador,
            fecha_inicio__lt=cita_end_time,
            fecha_fin__gt=cita_start_time
        )
        if bloqueos_conflictivos.exists():
            raise ValidationError(f"El colaborador '{colaborador.nombre}' tiene un bloqueo de tiempo en el horario solicitado: {bloqueos_conflictivos.first().motivo}")

    return True

def get_available_slots(colaborador_id, fecha_str, servicio_ids):
    """
    Obtiene los slots de tiempo disponibles para un colaborador en una fecha específica,
    considerando la duración del servicio.
    """
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        colaborador = Colaborador.objects.get(id=colaborador_id)
        servicios = Servicio.objects.filter(id__in=servicio_ids)
        if not servicios.exists():
            raise ValueError('IDs de servicio inválidos.')
        duracion_total_servicios = sum(s.duracion_estimada for s in servicios)
        intervalo = timedelta(minutes=duracion_total_servicios)
        # Define a smaller step for generating potential slots
        step = timedelta(minutes=15)
    except (ValueError, Colaborador.DoesNotExist, Servicio.DoesNotExist):
        raise ValueError('Formato de fecha, ID de colaborador o ID de servicio inválido.')

    dia_semana = fecha.weekday()
    horarios_colaborador = Horario.objects.filter(colaborador=colaborador, dia_semana=dia_semana).order_by('hora_inicio')
    if not horarios_colaborador.exists():
        return []

    citas_del_dia = Cita.objects.filter(colaboradores=colaborador, fecha__date=fecha, estado__in=['Pendiente', 'Confirmada']).prefetch_related('servicios').order_by('fecha')
    
    day_start = timezone.make_aware(datetime.combine(fecha, time.min))
    day_end = timezone.make_aware(datetime.combine(fecha, time.max))
    bloqueos_del_dia = Bloqueo.objects.filter(
        colaborador=colaborador,
        fecha_inicio__lte=day_end,
        fecha_fin__gte=day_start
    ).order_by('fecha_inicio')
    
    available_slots = []
    processed_slots = set()

    for horario in horarios_colaborador:
        schedule_start = timezone.make_aware(datetime.combine(fecha, horario.hora_inicio))
        schedule_end = timezone.make_aware(datetime.combine(fecha, horario.hora_fin))

        if schedule_end <= schedule_start:
            schedule_end += timedelta(days=1)

        busy_times = []
        for cita in citas_del_dia:
            start = cita.fecha
            end = start + timedelta(minutes=sum(s.duracion_estimada for s in cita.servicios.all()))
            if start < schedule_end and end > schedule_start:
                busy_times.append((start, end))
        for bloqueo in bloqueos_del_dia:
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
            for busy_start, busy_end in busy_times:
                if slot_start < busy_end and slot_end > busy_start:
                    is_available = False
                    # Move current_time to the end of the busy slot to avoid redundant checks
                    current_time = busy_end
                    break
            
            if is_available:
                if slot_start not in processed_slots:
                    available_slots.append({
                        'start': slot_start.isoformat(),
                        'end': slot_end.isoformat(),
                        'status': 'disponible'
                    })
                    processed_slots.add(slot_start)
                current_time += step
            # If not available, current_time was already moved to the end of the conflict
    
    # Sort the final list of slots
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
        sede = Sede.objects.get(id=sede_id)
    except Sede.DoesNotExist:
        raise ValueError(f"La sede con id={sede_id} no existe.")

    servicios = Servicio.objects.filter(id__in=servicio_ids)
    if not servicios.exists():
        raise ValueError(f"Alguno de los servicios con ids={servicio_ids} no existe.")

    # Check if all services belong to the selected sede
    for servicio in servicios:
        if servicio.sede.id != sede.id:
            raise ValueError(f"El servicio '{servicio.nombre}' (id={servicio.id}) pertenece a la sede '{servicio.sede.nombre}' (id={servicio.sede.id}), no a la sede seleccionada '{sede.nombre}' (id={sede.id}).")

    duracion_total_servicios = sum(s.duracion_estimada for s in servicios)
    intervalo = timedelta(minutes=duracion_total_servicios)
    step = timedelta(minutes=15)

    # Get collaborators who are associated with the given services and the sede.
    colaboradores = Colaborador.objects.filter(
        sede_id=sede_id,
        servicios__id__in=servicio_ids
    ).distinct()
    if not colaboradores.exists():
        return []

    colaborador_ids = [c.id for c in colaboradores]
    all_found_slots = []
    current_date = timezone.now().date()
    days_to_check = 30

    # Pre-fetch all necessary data for the entire period
    end_date = current_date + timedelta(days=days_to_check)
    day_start = timezone.make_aware(datetime.combine(current_date, time.min))
    day_end = timezone.make_aware(datetime.combine(end_date, time.max))

    all_horarios = Horario.objects.filter(colaborador_id__in=colaborador_ids).order_by('hora_inicio')
    all_citas = Cita.objects.filter(colaboradores__id__in=colaborador_ids, fecha__gte=day_start, fecha__lt=day_end, estado__in=['Pendiente', 'Confirmada']).prefetch_related('servicios', 'colaboradores').order_by('fecha')
    all_bloqueos = Bloqueo.objects.filter(colaborador_id__in=colaborador_ids, fecha_inicio__lte=day_end, fecha_fin__gte=day_start).order_by('fecha_inicio')

    # Group data by collaborator
    horarios_by_colaborador = {cid: [] for cid in colaborador_ids}
    for h in all_horarios:
        horarios_by_colaborador[h.colaborador_id].append(h)

    citas_by_colaborador = {cid: [] for cid in colaborador_ids}
    for c in all_citas:
        for col in c.colaboradores.all():
            if col.id in citas_by_colaborador:
                citas_by_colaborador[col.id].append(c)

    bloqueos_by_colaborador = {cid: [] for cid in colaborador_ids}
    for b in all_bloqueos:
        bloqueos_by_colaborador[b.colaborador_id].append(b)

    for _ in range(days_to_check):
        dia_semana = current_date.weekday()
        
        daily_slots_for_all_colaboradores = []
        for colaborador in colaboradores:
            # Get data for this collaborator for this day
            horarios_colaborador = [h for h in horarios_by_colaborador[colaborador.id] if h.dia_semana == dia_semana]
            if not horarios_colaborador:
                continue

            citas_del_dia = [c for c in citas_by_colaborador[colaborador.id] if c.fecha.date() == current_date]
            bloqueos_del_dia = [b for b in bloqueos_by_colaborador[colaborador.id] if b.fecha_inicio.date() <= current_date and b.fecha_fin.date() >= current_date]

            # Now, the logic from get_available_slots
            processed_slots = set()
            for horario in horarios_colaborador:
                schedule_start = timezone.make_aware(datetime.combine(current_date, horario.hora_inicio))
                schedule_end = timezone.make_aware(datetime.combine(current_date, horario.hora_fin))

                if schedule_end <= schedule_start:
                    schedule_end += timedelta(days=1)

                busy_times = []
                for cita in citas_del_dia:
                    start = cita.fecha
                    end = start + timedelta(minutes=sum(s.duracion_estimada for s in cita.servicios.all()))
                    if start < schedule_end and end > schedule_start:
                        busy_times.append((start, end))
                for bloqueo in bloqueos_del_dia:
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
                    for busy_start, busy_end in busy_times:
                        if slot_start < busy_end and slot_end > busy_start:
                            is_available = False
                            break
                    
                    if is_available:
                        if slot_start not in processed_slots and slot_start > timezone.now():
                            daily_slots_for_all_colaboradores.append({
                                'recurso': { 'id': colaborador.id, 'nombre': colaborador.nombre },
                                'start': slot_start.isoformat(),
                                'end': slot_end.isoformat()
                            })
                            processed_slots.add(slot_start)
                    
                    current_time += step

        daily_slots_for_all_colaboradores.sort(key=lambda x: x['start'])
        all_found_slots.extend(daily_slots_for_all_colaboradores)

        if len(all_found_slots) >= limit:
            break
        
        current_date += timedelta(days=1)

    return all_found_slots[:limit]
