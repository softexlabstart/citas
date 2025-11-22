"""
Comando Django para enviar recordatorios de WhatsApp programados.
Útil para testing y ejecución manual.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from citas.tasks_whatsapp import send_scheduled_reminders


class Command(BaseCommand):
    help = 'Envía recordatorios de WhatsApp programados que están pendientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se enviaría sin enviar realmente',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN: No se enviarán mensajes'))
            from citas.models_whatsapp import WhatsAppReminderSchedule

            now = timezone.now()
            pending = WhatsAppReminderSchedule.objects.filter(
                is_sent=False,
                scheduled_time__lte=now
            ).select_related('cita__sede__organizacion')

            self.stdout.write(f"\nRecordatorios pendientes: {pending.count()}")

            for reminder in pending[:20]:  # Mostrar solo los primeros 20
                self.stdout.write(
                    f"  - Cita #{reminder.cita_id}: {reminder.get_reminder_type_display()} "
                    f"para {reminder.cita.nombre} - "
                    f"Programado: {reminder.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
                )

            if pending.count() > 20:
                self.stdout.write(f"  ... y {pending.count() - 20} más")

        else:
            self.stdout.write('Enviando recordatorios programados...')

            result = send_scheduled_reminders()

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Completado: {result['sent']} enviados, "
                    f"{result['failed']} fallidos"
                )
            )
