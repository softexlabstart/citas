"""
Celery tasks for asynchronous operations in usuarios app.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_invitation_email_task(self, invitation_id, email, context):
    """
    Env�a un correo de invitaci�n de forma as�ncrona.

    Args:
        invitation_id: ID de la invitaci�n
        email: Email del destinatario
        context: Diccionario con los datos para renderizar la plantilla

    Returns:
        str: Mensaje de �xito o error
    """
    try:
        logger.info(f'[Celery] Iniciando env�o de invitaci�n a {email} (invitation_id: {invitation_id})')

        # Renderizar plantilla HTML
        html_message = render_to_string(
            'emails/invitation_email.html',
            context
        )

        # Enviar email
        send_mail(
            subject=f'Invitaci�n a {context["organization_name"]}',
            message=f'Has sido invitado a {context["organization_name"]}. Visita {context["accept_url"]} para aceptar.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f'[Celery] Invitaci�n enviada exitosamente a {email}')
        return f'Email sent successfully to {email}'

    except Exception as exc:
        logger.error(f'[Celery] Error enviando invitaci�n a {email}: {str(exc)}')

        # Reintentar la tarea si falla
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f'[Celery] Max retries exceeded para invitaci�n {invitation_id}')
            return f'Failed to send email to {email} after {self.max_retries} retries'
