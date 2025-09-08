from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Cita

@receiver(post_save, sender=Cita)
def send_appointment_confirmation_email(sender, instance, created, **kwargs):
    if created:
        subject = f"Confirmación de Cita: {instance.servicio.nombre}"
        context = {
            'appointment': instance,
        }
        html_message = render_to_string('emails/appointment_confirmation.html', context)
        plain_message = (
            f"Hola {instance.nombre},\n\n" +
            f"Tu cita para {instance.servicio.nombre} ha sido agendada exitosamente para el " +
            f"{instance.fecha.strftime('%Y-%m-%d a las %H:%M')}.\n\n" +
            f"¡Gracias por tu preferencia!"
        )

        recipient_list = []
        if instance.user and instance.user.email:
            recipient_list.append(instance.user.email)

        for recurso in instance.recursos.all():
            # Add email from linked user
            if recurso.usuario and recurso.usuario.email:
                recipient_list.append(recurso.usuario.email)
            
            # Also add email from metadata
            if isinstance(recurso.metadata, dict) and recurso.metadata.get("Correo"):
                recipient_list.append(recurso.metadata.get("Correo"))

        if recipient_list:
            try:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    list(set(recipient_list)), # Use set to avoid sending duplicate emails
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                # Log the error, or handle it as appropriate for your application
                print(f"Error sending confirmation email for appointment {instance.id}: {e}")


