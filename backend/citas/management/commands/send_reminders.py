from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from citas.models import Cita

class Command(BaseCommand):
    help = 'Sends email reminders for upcoming appointments.'

    def handle(self, *args, **options):
        # Get appointments scheduled between 5 hours and 5 hours and 15 minutes from now
        now = timezone.now()
        reminder_start = now + timedelta(hours=5)
        reminder_end = reminder_start + timedelta(minutes=15)
        appointments = Cita.objects.filter(fecha__range=(reminder_start, reminder_end), estado__in=['Pendiente', 'Confirmada'])

        for appointment in appointments:
            subject = f"Recordatorio de Cita: {appointment.servicio.nombre}"
            context = {
                'appointment': appointment,
            }
            html_message = render_to_string('emails/appointment_reminder.html', context)
            plain_message = f"Hola {appointment.nombre},\n\nEste es un recordatorio de tu cita de {appointment.servicio.nombre} el {appointment.fecha.strftime('%Y-%m-%d a las %H:%M')}.\n\n¡Te esperamos!"
            
            # Assuming the user model has an email field
            recipient_list = [appointment.user.email] if appointment.user and appointment.user.email else []

            if recipient_list:
                try:
                    send_mail(
                        subject,
                        plain_message,
                        None, # Use DEFAULT_FROM_EMAIL from settings
                        recipient_list,
                        html_message=html_message,
                        fail_silently=False,
                    )
                    self.stdout.write(self.style.SUCCESS(f'Successfully sent reminder to {appointment.nombre} for appointment {appointment.id}'))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error sending reminder to {appointment.nombre} for appointment {appointment.id}: {e}'))
            else:
                self.stdout.write(self.style.WARNING(f'Skipping reminder for appointment {appointment.id}: No email address found for user.'))

        self.stdout.write(self.style.SUCCESS('Email reminders sent successfully!'))
