"""
Servicio centralizado para envío de mensajes de WhatsApp usando Twilio.
"""
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from ..models_whatsapp import WhatsAppMessage
from organizacion.models import Organizacion
from citas.models import Cita

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Servicio para envío de mensajes de WhatsApp mediante Twilio.
    Soporta cuenta compartida (por defecto) y cuentas propias (futuro).
    """

    def __init__(self):
        """Inicializa el cliente de Twilio con credenciales del settings"""
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)

        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning(
                "Twilio WhatsApp no configurado correctamente. "
                "Verifica TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_WHATSAPP_FROM"
            )
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)

    def is_configured(self) -> bool:
        """Verifica si Twilio está configurado"""
        return self.client is not None

    def format_phone_number(self, phone: str) -> str:
        """
        Formatea número de teléfono para WhatsApp.

        Args:
            phone: Número en cualquier formato

        Returns:
            Número en formato WhatsApp: whatsapp:+573001234567
        """
        # Remover espacios, guiones, paréntesis
        cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Si no empieza con +, asumir que es Colombia (+57)
        if not cleaned.startswith('+'):
            cleaned = f'+57{cleaned}'

        # Formato WhatsApp de Twilio
        if not cleaned.startswith('whatsapp:'):
            cleaned = f'whatsapp:{cleaned}'

        return cleaned

    def send_appointment_confirmation(self, cita: Cita) -> Optional[WhatsAppMessage]:
        """
        Envía confirmación de cita por WhatsApp.

        Args:
            cita: Instancia de la cita creada

        Returns:
            WhatsAppMessage instance o None si falla
        """
        org = cita.sede.organizacion

        # Verificar si WhatsApp está habilitado
        if not org.whatsapp_enabled or not org.whatsapp_confirmation_enabled:
            logger.debug(f"WhatsApp deshabilitado para organización {org.nombre}")
            return None

        # Verificar que la cita tenga teléfono
        phone = cita.telefono_cliente
        if not phone:
            logger.warning(f"Cita #{cita.id} no tiene teléfono, no se puede enviar WhatsApp")
            return None

        # Preparar mensaje
        sender_name = org.whatsapp_sender_name or org.nombre
        fecha_formateada = cita.fecha.strftime('%d/%m/%Y a las %H:%M')
        servicios_nombres = ', '.join([s.nombre for s in cita.servicios.all()])

        message_body = f"""🔔 *{sender_name}*

¡Hola {cita.nombre}!

Tu cita ha sido confirmada:

📅 *Fecha:* {fecha_formateada}
📍 *Sede:* {cita.sede.nombre}
💼 *Servicios:* {servicios_nombres}

Te esperamos 10 minutos antes de tu cita.

Si necesitas cancelar o reprogramar, por favor contáctanos lo antes posible.

¡Gracias por preferirnos!"""

        return self._send_message(
            cita=cita,
            organizacion=org,
            message_type='confirmation',
            recipient_phone=phone,
            recipient_name=cita.nombre,
            message_body=message_body
        )

    def send_appointment_reminder_24h(self, cita: Cita) -> Optional[WhatsAppMessage]:
        """
        Envía recordatorio 24h antes de la cita.

        Args:
            cita: Instancia de la cita

        Returns:
            WhatsAppMessage instance o None si falla
        """
        org = cita.sede.organizacion

        if not org.whatsapp_enabled or not org.whatsapp_reminder_24h_enabled:
            return None

        phone = cita.telefono_cliente
        if not phone:
            return None

        sender_name = org.whatsapp_sender_name or org.nombre
        fecha_formateada = cita.fecha.strftime('%d/%m/%Y a las %H:%M')

        message_body = f"""⏰ *Recordatorio - {sender_name}*

Hola {cita.nombre},

Te recordamos que mañana tienes tu cita:

📅 *Fecha:* {fecha_formateada}
📍 *Sede:* {cita.sede.nombre}

Nos vemos mañana. ¡No faltes! 😊"""

        return self._send_message(
            cita=cita,
            organizacion=org,
            message_type='reminder_24h',
            recipient_phone=phone,
            recipient_name=cita.nombre,
            message_body=message_body
        )

    def send_appointment_reminder_1h(self, cita: Cita) -> Optional[WhatsAppMessage]:
        """
        Envía recordatorio 1h antes de la cita.

        Args:
            cita: Instancia de la cita

        Returns:
            WhatsAppMessage instance o None si falla
        """
        org = cita.sede.organizacion

        if not org.whatsapp_enabled or not org.whatsapp_reminder_1h_enabled:
            return None

        phone = cita.telefono_cliente
        if not phone:
            return None

        sender_name = org.whatsapp_sender_name or org.nombre
        hora_formateada = cita.fecha.strftime('%H:%M')

        message_body = f"""🔔 *Recordatorio - {sender_name}*

Hola {cita.nombre},

Tu cita es en 1 hora:

🕐 *Hora:* {hora_formateada}
📍 *Sede:* {cita.sede.nombre}

Te esperamos. Por favor llega a tiempo. ⏰"""

        return self._send_message(
            cita=cita,
            organizacion=org,
            message_type='reminder_1h',
            recipient_phone=phone,
            recipient_name=cita.nombre,
            message_body=message_body
        )

    def send_appointment_cancellation(self, cita: Cita, reason: str = '') -> Optional[WhatsAppMessage]:
        """
        Envía notificación de cancelación de cita.

        Args:
            cita: Instancia de la cita cancelada
            reason: Razón de cancelación (opcional)

        Returns:
            WhatsAppMessage instance o None si falla
        """
        org = cita.sede.organizacion

        if not org.whatsapp_enabled or not org.whatsapp_cancellation_enabled:
            return None

        phone = cita.telefono_cliente
        if not phone:
            return None

        sender_name = org.whatsapp_sender_name or org.nombre
        fecha_formateada = cita.fecha.strftime('%d/%m/%Y a las %H:%M')

        reason_text = f"\n\n*Razón:* {reason}" if reason else ""

        message_body = f"""❌ *Cancelación - {sender_name}*

Hola {cita.nombre},

Tu cita ha sido cancelada:

📅 *Fecha que tenías:* {fecha_formateada}
📍 *Sede:* {cita.sede.nombre}{reason_text}

Si deseas reagendar, por favor contáctanos.

Gracias por tu comprensión."""

        return self._send_message(
            cita=cita,
            organizacion=org,
            message_type='cancellation',
            recipient_phone=phone,
            recipient_name=cita.nombre,
            message_body=message_body
        )

    def _send_message(
        self,
        cita: Cita,
        organizacion: Organizacion,
        message_type: str,
        recipient_phone: str,
        recipient_name: str,
        message_body: str
    ) -> Optional[WhatsAppMessage]:
        """
        Método interno para enviar mensaje vía Twilio.

        Args:
            cita: Cita relacionada
            organizacion: Organización que envía
            message_type: Tipo de mensaje
            recipient_phone: Teléfono destino
            recipient_name: Nombre del destinatario
            message_body: Cuerpo del mensaje

        Returns:
            WhatsAppMessage instance
        """
        if not self.is_configured():
            logger.error("Twilio no está configurado, no se puede enviar mensaje")
            return None

        # Crear registro en BD
        whatsapp_msg = WhatsAppMessage.objects.create(
            cita=cita,
            organizacion=organizacion,
            message_type=message_type,
            recipient_phone=recipient_phone,
            recipient_name=recipient_name,
            message_body=message_body,
            status='pending'
        )

        try:
            # Formatear número
            to_number = self.format_phone_number(recipient_phone)

            # Enviar via Twilio
            message = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=message_body
            )

            # Actualizar registro con éxito
            whatsapp_msg.mark_as_sent(
                twilio_sid=message.sid,
                twilio_status=message.status
            )

            logger.info(
                f"WhatsApp enviado: {message_type} a {recipient_name} "
                f"(Cita #{cita.id}) - SID: {message.sid}"
            )

            return whatsapp_msg

        except TwilioRestException as e:
            # Error de Twilio
            whatsapp_msg.mark_as_failed(
                error_code=str(e.code),
                error_message=e.msg
            )
            logger.error(
                f"Error Twilio enviando WhatsApp a {recipient_name}: "
                f"[{e.code}] {e.msg}"
            )
            return whatsapp_msg

        except Exception as e:
            # Error genérico
            whatsapp_msg.mark_as_failed(
                error_code='UNKNOWN',
                error_message=str(e)
            )
            logger.error(
                f"Error enviando WhatsApp a {recipient_name}: {str(e)}",
                exc_info=True
            )
            return whatsapp_msg


# Instancia singleton del servicio
whatsapp_service = WhatsAppService()
