"""
Webhook de Twilio para actualizar estados de mensajes WhatsApp.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import connection
import logging

from .models_whatsapp import WhatsAppMessage
from organizacion.thread_locals import set_current_organization

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
            # Buscar mensaje por SID de Twilio en todos los schemas
            # Primero intentamos encontrarlo y establecer el tenant correcto
            whatsapp_msg = None

            # Buscar en todos los schemas de tenants
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name LIKE 'tenant_%' OR schema_name = 'public'
                    ORDER BY schema_name
                """)
                schemas = [row[0] for row in cursor.fetchall()]

            for schema in schemas:
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {schema}")

                try:
                    msg = WhatsAppMessage.objects.get(twilio_sid=message_sid)
                    whatsapp_msg = msg
                    # Establecer el tenant correcto
                    if msg.organizacion:
                        set_current_organization(msg.organizacion)
                        logger.info(f"[Twilio Webhook] Found message in schema {schema}, org: {msg.organizacion.nombre}")
                    break
                except WhatsAppMessage.DoesNotExist:
                    continue

            if not whatsapp_msg:
                logger.error(f"[Twilio Webhook] Message with SID {message_sid} not found in any schema")
                return Response(
                    {'error': 'Message not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

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

        except Exception as e:
            logger.error(f"[Twilio Webhook] Error processing webhook: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
