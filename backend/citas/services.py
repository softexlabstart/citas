
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DateTimeField
from rest_framework.exceptions import ValidationError
from .models import Cita, Horario, Recurso, Servicio, Bloqueo
from organizacion.models import Sede

def check_appointment_availability(sede, servicio, recursos, fecha, cita_id=None):
    """
    Verifica la disponibilidad de una cita, incluyendo horarios de recursos y conflictos de citas.
    Lanza una ValidationError si no está disponible.
    """
    try:
        duracion_estimada = servicio.duracion_estimada
    except AttributeError:
        raise ValidationError("El servicio seleccionado no tiene una duración estimada válida.")

    cita_start_time = fecha
    cita_end_time = cita_start_time + timedelta(minutes=duracion_estimada)

    for recurso in recursos:
        # 1. Check schedule
        dia_semana = fecha.weekday()
        horarios_recurso = Horario.objects.filter(recurso=recurso, dia_semana=dia_semana)

        if not horarios_recurso.exists():
            raise ValidationError(f"El recurso '{recurso.nombre}' no tiene horarios definidos para el día seleccionado en esta sede.")

        is_within_schedule = False
        for horario in horarios_recurso:
            horario_start_same_day = timezone.make_aware(datetime.combine(cita_start_time.date(), horario.hora_inicio))
            horario_end_same_day = timezone.make_aware(datetime.combine(cita_start_time.date(), horario.hora_fin))

            if horario_end_same_day < horario_start_same_day:
                horario_end_same_day += timedelta(days=1)

            if (horario_start_same_day <= cita_start_time and cita_end_time <= horario_end_same_day):
                is_within_schedule = True
                break
        
        if not is_within_schedule:
            raise ValidationError(f"El recurso '{recurso.nombre}' no está disponible en el horario solicitado en esta sede.")

        # 2. Check for overlapping appointments
        # Annotate existing appointments with their calculated end time for a precise overlap check.
        existing_appointments = Cita.objects.annotate(
            end_time=ExpressionWrapper(
                F('fecha') + F('servicio__duracion_estimada') * timedelta(minutes=1),
                output_field=DateTimeField()
            )
        )

        # An overlap occurs if an existing appointment starts before the new one ends,
        # AND it ends after the new one starts.
        conflictos = existing_appointments.filter(
            recursos=recurso,
            sede=sede,
            estado__in=['Pendiente', 'Confirmada'],
            fecha__lt=cita_end_time,
            end_time__gt=cita_start_time
        ).exclude(id=cita_id)

        if conflictos.exists():
            raise ValidationError(f"El recurso '{recurso.nombre}' ya tiene una cita agendada que se superpone con el horario solicitado.")

        # 3. Check for overlapping blocks
        bloqueos_conflictivos = Bloqueo.objects.filter(
            recurso=recurso,
            sede=sede,
            fecha_inicio__lt=cita_end_time,
            fecha_fin__gt=cita_start_time
        )
        if bloqueos_conflictivos.exists():
            raise ValidationError(f"El recurso '{recurso.nombre}' tiene un bloqueo de tiempo en el horario solicitado: {bloqueos_conflictivos.first().motivo}")

    return True

def get_available_slots(recurso_id, fecha_str):
    """
    Obtiene los slots de tiempo disponibles para un recurso en una fecha específica.
    """
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        recurso = Recurso.objects.get(id=recurso_id)
    except (ValueError, Recurso.DoesNotExist):
        raise ValueError('Formato de fecha o ID de recurso inválido.')

    dia_semana = fecha.weekday()
    horarios_recurso = Horario.objects.filter(recurso=recurso, dia_semana=dia_semana)
    citas_del_dia = Cita.objects.filter(recursos=recurso, fecha__date=fecha, estado__in=['Pendiente', 'Confirmada']).order_by('fecha')
    bloqueos_del_dia = Bloqueo.objects.filter(recurso=recurso, fecha_inicio__date=fecha).order_by('fecha_inicio')

    slots_del_dia = []
    intervalo_minutos = 30
    start_of_day = datetime.combine(fecha, time(0, 0))
    end_of_day = timezone.make_aware(datetime.combine(fecha, time(23, 59, 59)))

    current_slot_start = timezone.make_aware(start_of_day)
    while current_slot_start < end_of_day:
        current_slot_end = current_slot_start + timedelta(minutes=intervalo_minutos)
        slot_time = current_slot_start.time()

        in_schedule = any(
            horario.hora_inicio <= slot_time < horario.hora_fin
            for horario in horarios_recurso
        )

        overlap = False
        if in_schedule:
            for cita in citas_del_dia:
                cita_start = cita.fecha
                cita_end = cita.fecha + timedelta(minutes=cita.servicio.duracion_estimada)
                if not (current_slot_end <= cita_start or current_slot_start >= cita_end):
                    overlap = True
                    break
            
            # Also check for block overlap
            if not overlap:
                for bloqueo in bloqueos_del_dia:
                    bloqueo_start = bloqueo.fecha_inicio
                    bloqueo_end = bloqueo.fecha_fin
                    if not (current_slot_end <= bloqueo_start or current_slot_start >= bloqueo_end):
                        overlap = True
                        break
        
        status = 'disponible' if in_schedule and not overlap else 'no disponible'

        slots_del_dia.append({
            'start': current_slot_start.isoformat(),
            'end': current_slot_end.isoformat(),
            'status': status
        })
        
        current_slot_start = current_slot_end
    
    return slots_del_dia

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

    recursos = Recurso.objects.filter(sede_id=sede_id)
    if not recursos.exists():
        return []

    found_slots = []
    current_date = timezone.now().date()
    days_to_check = 30 # Search limit to avoid infinite loops

    for _ in range(days_to_check):
        if len(found_slots) >= limit:
            break

        for recurso in recursos:
            if len(found_slots) >= limit:
                break
            
            date_str = current_date.strftime('%Y-%m-%d')
            daily_slots = get_available_slots(recurso.id, date_str)
            
            for slot in daily_slots:
                if slot['status'] == 'disponible' and datetime.fromisoformat(slot['start']) > timezone.now():
                    found_slots.append({ 'recurso': { 'id': recurso.id, 'nombre': recurso.nombre }, 'start': slot['start'], 'end': slot['end'] })
                    if len(found_slots) >= limit:
                        break
        
        current_date += timedelta(days=1)

    return found_slots
