"""
Webhook de Twilio para actualizar estados de mensajes WhatsApp.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
import logging

from .models_whatsapp import WhatsAppMessage

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TwilioWhatsAppWebhook(APIView):
    """
    Webhook para recibir actualizaciones de estado de Twilio.

    Twilio envía POST requests cuando cambia el estado del mensaje:
    - sent: Mensaje enviado a Twilio
    - delivered: Mensaje entregado al destinatario
    - read: Mensaje leído por el destinatario
    - failed: Mensaje falló

    POST /api/citas/whatsapp-webhook/
    """

    # No requiere autenticación porque es llamado por Twilio
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
        Procesa actualización de estado desde Twilio.

        Parámetros que envía Twilio:
        - MessageSid: ID del mensaje en Twilio
        - MessageStatus: Estado actual (sent, delivered, read, failed, undelivered)
        - ErrorCode: Código de error si falló
        - ErrorMessage: Mensaje de error si falló
        """

        # Obtener datos del webhook
        message_sid = request.data.get('MessageSid') or request.POST.get('MessageSid')
        message_status = request.data.get('MessageStatus') or request.POST.get('MessageStatus')
        error_code = request.data.get('ErrorCode') or request.POST.get('ErrorCode')
        error_message = request.data.get('ErrorMessage') or request.POST.get('ErrorMessage')

        logger.info(
            f"[Twilio Webhook] SID: {message_sid}, Status: {message_status}, "
            f"Error: {error_code} - {error_message}"
        )

        if not message_sid or not message_status:
            logger.warning("[Twilio Webhook] Missing MessageSid or MessageStatus")
            return Response(
                {'error': 'MessageSid and MessageStatus are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Buscar mensaje por SID de Twilio
            whatsapp_msg = WhatsAppMessage.objects.get(twilio_sid=message_sid)

            # Actualizar según el estado
            if message_status == 'delivered':
                whatsapp_msg.status = 'delivered'
                whatsapp_msg.delivered_at = timezone.now()
                whatsapp_msg.save(update_fields=['status', 'delivered_at', 'updated_at'])
                logger.info(f"[Twilio Webhook] Message {message_sid} marked as delivered")

            elif message_status == 'read':
                whatsapp_msg.status = 'read'
                if not whatsapp_msg.delivered_at:
                    whatsapp_msg.delivered_at = timezone.now()
                whatsapp_msg.save(update_fields=['status', 'delivered_at', 'updated_at'])
                logger.info(f"[Twilio Webhook] Message {message_sid} marked as read")

            elif message_status in ['failed', 'undelivered']:
                whatsapp_msg.status = 'failed'
                if error_code:
                    whatsapp_msg.error_code = error_code
                if error_message:
                    whatsapp_msg.error_message = error_message
                whatsapp_msg.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])
                logger.warning(
                    f"[Twilio Webhook] Message {message_sid} failed: "
                    f"{error_code} - {error_message}"
                )

            elif message_status == 'sent':
                # Ya está marcado como sent cuando se envía
                # Pero actualizamos twilio_status por si acaso
                whatsapp_msg.twilio_status = message_status
                whatsapp_msg.save(update_fields=['twilio_status', 'updated_at'])
                logger.info(f"[Twilio Webhook] Message {message_sid} confirmed as sent")

            return Response({'status': 'success'}, status=status.HTTP_200_OK)

        except WhatsAppMessage.DoesNotExist:
            logger.error(f"[Twilio Webhook] Message with SID {message_sid} not found in database")
            return Response(
                {'error': 'Message not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"[Twilio Webhook] Error processing webhook: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
