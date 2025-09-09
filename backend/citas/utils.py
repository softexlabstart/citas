from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_appointment_email(appointment, subject, template_name, context=None):
    """
    A utility function to build recipient lists and send appointment-related emails.
    """
    if context is None:
        context = {}
    # Ensure the appointment is always in the context
    context['appointment'] = appointment

    html_message = render_to_string(f'emails/{template_name}.html', context)
    # Generate a simple plain text message as a fallback
    plain_message = f"Detalles de su cita para {appointment.servicio.nombre} el {appointment.fecha.strftime('%Y-%m-%d a las %H:%M')}."

    recipient_list = []
    if appointment.user and appointment.user.email:
        recipient_list.append(appointment.user.email)

    for recurso in appointment.recursos.all():
        if recurso.usuario and recurso.usuario.email:
            recipient_list.append(recurso.usuario.email)
        if isinstance(recurso.metadata, dict) and recurso.metadata.get("Correo"):
            recipient_list.append(recurso.metadata.get("Correo"))

    if recipient_list:
        try:
            send_mail(
                subject, plain_message, settings.DEFAULT_FROM_EMAIL,
                list(set(recipient_list)), html_message=html_message, fail_silently=False
            )
        except Exception as e:
            # In a real application, you would log this error more robustly
            print(f"Error sending email for appointment {appointment.id} (Subject: {subject}): {e}")