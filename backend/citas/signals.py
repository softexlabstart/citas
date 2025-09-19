from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cita
from .utils import send_appointment_email

@receiver(post_save, sender=Cita)
def send_appointment_confirmation_email(sender, instance, created, **kwargs):
    """
    Sends a confirmation email when a new appointment is created.
    This uses the centralized email utility function.
    """
    if created:
        send_appointment_email(
            appointment=instance,
            subject=f"Confirmación de Cita: {', '.join([s.nombre for s in instance.servicios.all()])}",
            template_name='appointment_confirmation'
        )
