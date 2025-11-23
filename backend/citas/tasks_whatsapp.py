"""
Tareas Celery para envío de notificaciones WhatsApp.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import Cita
from .models_whatsapp import WhatsAppReminderSchedule
from .whatsapp.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_whatsapp_confirmation(self, cita_id: int):
    """
    Tarea para enviar confirmación de cita por WhatsApp.

    Args:
        cita_id: ID de la cita creada
    """
    try:
        cita = Cita.all_objects.select_related('sede__organizacion').get(id=cita_id)

        logger.info(f"[WhatsApp] Enviando confirmación para cita #{cita_id}")
        result = whatsapp_service.send_appointment_confirmation(cita)

        if result:
            logger.info(f"[WhatsApp] Confirmación enviada exitosamente para cita #{cita_id}")
        else:
            logger.warning(f"[WhatsApp] No se envió confirmación para cita #{cita_id} (deshabilitado o sin teléfono)")

    except Cita.DoesNotExist:
        logger.error(f"[WhatsApp] Cita #{cita_id} no encontrada")
    except Exception as exc:
        logger.error(f"[WhatsApp] Error enviando confirmación para cita #{cita_id}: {str(exc)}")
        # Reintentar en 5 minutos
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def send_whatsapp_cancellation(self, cita_id: int, reason: str = ''):
    """
    Tarea para enviar notificación de cancelación por WhatsApp.

    Args:
        cita_id: ID de la cita cancelada
        reason: Razón de la cancelación
    """
    try:
        cita = Cita.all_objects.select_related('sede__organizacion').get(id=cita_id)

        logger.info(f"[WhatsApp] Enviando cancelación para cita #{cita_id}")
        result = whatsapp_service.send_appointment_cancellation(cita, reason)

        if result:
            logger.info(f"[WhatsApp] Cancelación enviada exitosamente para cita #{cita_id}")
        else:
            logger.warning(f"[WhatsApp] No se envió cancelación para cita #{cita_id}")

    except Cita.DoesNotExist:
        logger.error(f"[WhatsApp] Cita #{cita_id} no encontrada")
    except Exception as exc:
        logger.error(f"[WhatsApp] Error enviando cancelación para cita #{cita_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task
def send_scheduled_reminders():
    """
    Tarea periódica que envía recordatorios programados.
    Se ejecuta cada 5 minutos vía Celery Beat.
    """
    now = timezone.now()

    # Buscar recordatorios pendientes que ya deberían enviarse
    pending_reminders = WhatsAppReminderSchedule.objects.filter(
        is_sent=False,
        scheduled_time__lte=now
    ).select_related('cita__sede__organizacion')[:100]  # Procesar máximo 100 por ejecución

    sent_count = 0
    failed_count = 0

    for reminder in pending_reminders:
        try:
            cita = reminder.cita

            # Verificar que la cita no esté cancelada
            if cita.estado == 'Cancelada':
                logger.info(f"[WhatsApp] Saltando recordatorio para cita cancelada #{cita.id}")
                reminder.is_sent = True
                reminder.save()
                continue

            # Enviar según tipo de recordatorio
            if reminder.reminder_type == '24h':
                result = whatsapp_service.send_appointment_reminder_24h(cita)
            elif reminder.reminder_type == '1h':
                result = whatsapp_service.send_appointment_reminder_1h(cita)
            else:
                logger.warning(f"[WhatsApp] Tipo de recordatorio desconocido: {reminder.reminder_type}")
                continue

            if result:
                reminder.mark_as_sent(result)
                sent_count += 1
                logger.info(
                    f"[WhatsApp] Recordatorio {reminder.reminder_type} enviado para cita #{cita.id}"
                )
            else:
                # No se envió pero no es un error (ej: deshabilitado)
                reminder.is_sent = True
                reminder.save()
                logger.debug(
                    f"[WhatsApp] Recordatorio {reminder.reminder_type} no enviado para cita #{cita.id}"
                )

        except Exception as e:
            failed_count += 1
            logger.error(
                f"[WhatsApp] Error procesando recordatorio {reminder.id}: {str(e)}",
                exc_info=True
            )

    logger.info(
        f"[WhatsApp] Tarea de recordatorios completada: "
        f"{sent_count} enviados, {failed_count} fallidos"
    )

    return {
        'sent': sent_count,
        'failed': failed_count,
        'total_processed': sent_count + failed_count
    }


@shared_task
def schedule_appointment_reminders(cita_id: int):
    """
    Programa los recordatorios para una cita nueva.
    Crea los registros de WhatsAppReminderSchedule.

    Args:
        cita_id: ID de la cita
    """
    try:
        cita = Cita.all_objects.select_related('sede__organizacion').get(id=cita_id)
        org = cita.sede.organizacion

        # Verificar que WhatsApp esté habilitado
        if not org.whatsapp_enabled:
            logger.debug(f"[WhatsApp] WhatsApp deshabilitado para org {org.nombre}")
            return

        # Verificar que la cita tenga teléfono
        if not cita.telefono_cliente:
            logger.debug(f"[WhatsApp] Cita #{cita_id} sin teléfono")
            return

        now = timezone.now()

        # Programar recordatorio 24h antes
        if org.whatsapp_reminder_24h_enabled:
            reminder_24h_time = cita.fecha - timedelta(hours=24)

            # Solo programar si falta más de 24h
            if reminder_24h_time > now:
                WhatsAppReminderSchedule.objects.get_or_create(
                    cita=cita,
                    reminder_type='24h',
                    defaults={'scheduled_time': reminder_24h_time}
                )
                logger.info(f"[WhatsApp] Recordatorio 24h programado para cita #{cita_id}")

        # Programar recordatorio 1h antes
        if org.whatsapp_reminder_1h_enabled:
            reminder_1h_time = cita.fecha - timedelta(hours=1)

            # Solo programar si falta más de 1h
            if reminder_1h_time > now:
                WhatsAppReminderSchedule.objects.get_or_create(
                    cita=cita,
                    reminder_type='1h',
                    defaults={'scheduled_time': reminder_1h_time}
                )
                logger.info(f"[WhatsApp] Recordatorio 1h programado para cita #{cita_id}")

    except Cita.DoesNotExist:
        logger.error(f"[WhatsApp] Cita #{cita_id} no encontrada al programar recordatorios")
    except Exception as e:
        logger.error(
            f"[WhatsApp] Error programando recordatorios para cita #{cita_id}: {str(e)}",
            exc_info=True
        )


@shared_task
def cleanup_old_whatsapp_messages():
    """
    Tarea de limpieza: elimina mensajes WhatsApp antiguos (> 90 días).
    Se ejecuta diariamente.
    """
    from .models_whatsapp import WhatsAppMessage

    cutoff_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = WhatsAppMessage.objects.filter(
        created_at__lt=cutoff_date
    ).delete()

    logger.info(f"[WhatsApp] Limpieza completada: {deleted_count} mensajes antiguos eliminados")

    return {'deleted': deleted_count}
