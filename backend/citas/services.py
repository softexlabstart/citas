
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DateTimeField
from rest_framework.exceptions import ValidationError
from .models import Cita, Horario, Colaborador, Servicio, Bloqueo
from organizacion.models import Sede

def check_appointment_availability(sede, servicio, colaboradores, fecha, cita_id=None):
    """
    Verifica la disponibilidad de una cita, incluyendo horarios de colaboradores y conflictos de citas.
    Lanza una ValidationError si no está disponible.
    """
    try:
        duracion_estimada = servicio.duracion_estimada
    except AttributeError:
        raise ValidationError("El servicio seleccionado no tiene una duración estimada válida.")

    cita_start_time = fecha
    cita_end_time = cita_start_time + timedelta(minutes=duracion_estimada)

    # Annotate existing appointments once outside the loop for efficiency.
    existing_appointments = Cita.objects.annotate(
        end_time=ExpressionWrapper(
            F('fecha') + F('servicio__duracion_estimada') * timedelta(minutes=1),
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
            conflict_end = conflict_start + timedelta(minutes=conflict.servicio.duracion_estimada)
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

def get_available_slots(colaborador_id, fecha_str, servicio_id):
    """
    Obtiene los slots de tiempo disponibles para un colaborador en una fecha específica,
    considerando la duración del servicio.
    """
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        colaborador = Colaborador.objects.get(id=colaborador_id)
        servicio = Servicio.objects.get(id=servicio_id)
        intervalo = timedelta(minutes=servicio.duracion_estimada)
    except (ValueError, Colaborador.DoesNotExist, Servicio.DoesNotExist):
        raise ValueError('Formato de fecha, ID de colaborador o ID de servicio inválido.')

    dia_semana = fecha.weekday()
    horarios_colaborador = Horario.objects.filter(colaborador=colaborador, dia_semana=dia_semana).order_by('hora_inicio')
    if not horarios_colaborador.exists():
        return []

    citas_del_dia = Cita.objects.filter(colaboradores=colaborador, fecha__date=fecha, estado__in=['Pendiente', 'Confirmada']).order_by('fecha')
    
    day_start = timezone.make_aware(datetime.combine(fecha, time.min))
    day_end = timezone.make_aware(datetime.combine(fecha, time.max))
    bloqueos_del_dia = Bloqueo.objects.filter(
        colaborador=colaborador,
        fecha_inicio__lte=day_end,
        fecha_fin__gte=day_start
    ).order_by('fecha_inicio')
    
    available_slots = []

    for horario in horarios_colaborador:
        schedule_start = timezone.make_aware(datetime.combine(fecha, horario.hora_inicio))
        schedule_end = timezone.make_aware(datetime.combine(fecha, horario.hora_fin))

        if schedule_end <= schedule_start:
            schedule_end += timedelta(days=1)

        busy_times = []
        for cita in citas_del_dia:
            start = cita.fecha
            end = start + timedelta(minutes=cita.servicio.duracion_estimada)
            if start < schedule_end and end > schedule_start:
                busy_times.append((start, end))
        for bloqueo in bloqueos_del_dia:
            start = max(bloqueo.fecha_inicio, schedule_start)
            end = min(bloqueo.fecha_fin, schedule_end)
            if start < end:
                busy_times.append((start, end))
        busy_times.sort()

        last_busy_end = schedule_start
        for busy_start, busy_end in busy_times:
            current_time = last_busy_end
            while current_time + intervalo <= busy_start:
                available_slots.append({
                    'start': current_time.isoformat(),
                    'end': (current_time + intervalo).isoformat(),
                    'status': 'disponible'
                })
                current_time += intervalo
            last_busy_end = max(last_busy_end, busy_end)

        current_time = last_busy_end
        while current_time + intervalo <= schedule_end:
            available_slots.append({
                'start': current_time.isoformat(),
                'end': (current_time + intervalo).isoformat(),
                'status': 'disponible'
            })
            current_time += intervalo
            
    return available_slots

def find_next_available_slots(servicio_id, sede_id, limit=5):
    """
    Finds the next available slots for a given service at a specific location,
    across all available resources.
    """
    try:
        sede = Sede.objects.get(id=sede_id)
    except Sede.DoesNotExist:
        raise ValueError(f"La sede con id={sede_id} no existe.")

    try:
        servicio = Servicio.objects.get(id=servicio_id)
    except Servicio.DoesNotExist:
        raise ValueError(f"El servicio con id={servicio_id} no existe.")

    if servicio.sede.id != sede.id:
        raise ValueError(f"El servicio '{servicio.nombre}' (id={servicio.id}) pertenece a la sede '{servicio.sede.nombre}' (id={servicio.sede.id}), no a la sede seleccionada '{sede.nombre}' (id={sede.id}).")

    colaboradores = Colaborador.objects.filter(sede_id=sede_id)
    if not colaboradores.exists():
        return []

    found_slots = []
    current_date = timezone.now().date()
    days_to_check = 30 # Search limit to avoid infinite loops

    for _ in range(days_to_check):
        if len(found_slots) >= limit:
            break

        for colaborador in colaboradores:
            if len(found_slots) >= limit:
                break
            
            date_str = current_date.strftime('%Y-%m-%d')
            daily_slots = get_available_slots(colaborador.id, date_str, servicio_id)
            
            for slot in daily_slots:
                if slot['status'] == 'disponible' and datetime.fromisoformat(slot['start']) > timezone.now():
                    found_slots.append({ 'recurso': { 'id': colaborador.id, 'nombre': colaborador.nombre }, 'start': slot['start'], 'end': slot['end'] })
                    if len(found_slots) >= limit:
                        break
        
        current_date += timedelta(days=1)

    return found_slots
