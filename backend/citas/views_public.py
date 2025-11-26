"""
Vistas públicas para el sistema de citas.
Permiten a usuarios no autenticados agendar citas como invitados.

SEGURIDAD: Implementa rate limiting para prevenir spam y ataques DoS.
"""
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

from .models import Cita
from .serializers import GuestCitaSerializer

# SECURITY: Import custom throttles
from core.throttling import PublicBookingIPThrottle, PublicBookingEmailThrottle

logger = logging.getLogger(__name__)


class PublicCitaViewSet(viewsets.ModelViewSet):
    """
    Endpoint público para que invitados puedan agendar citas.
    No requiere autenticación.

    SEGURIDAD - Rate Limiting:
    - Por IP: Máximo 5 citas por hora (previene spam desde una IP)
    - Por Email: Máximo 3 citas por día (previene abuso de un mismo email)
    - Previene: spam, DoS, flooding de emails, saturación de BD

    POST /api/citas/public-booking/
    {
        "nombre": "Juan Pérez",
        "email_cliente": "juan@example.com",
        "telefono_cliente": "+57123456789",
        "fecha": "2025-10-05T10:00:00Z",
        "servicios_ids": [1, 2],
        "colaboradores_ids": [1],
        "sede_id": 1,
        "comentario": "Comentario opcional"
    }
    """
    queryset = Cita.objects.all()
    serializer_class = GuestCitaSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']  # Solo permitir POST (crear citas)

    # SECURITY: Rate limiting para prevenir spam y ataques DoS
    throttle_classes = [PublicBookingIPThrottle, PublicBookingEmailThrottle]

    def create(self, request, *args, **kwargs):
        """
        Crea una cita para un invitado y envía un magic link por email.
        """
        # ARQUITECTURA: Forzar search_path a public antes de validar el serializer
        # El serializer valida que existan los servicios, colaboradores y sede
        # consultando sus querysets, que deben buscar en el schema public
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # VALIDAR: Verificar si la organización permite agendamiento público
        organizacion = serializer.validated_data['sede'].organizacion

        if not organizacion.permitir_agendamiento_publico:
            return Response(
                {
                    'error': 'Esta organización requiere iniciar sesión para agendar citas.',
                    'code': 'public_booking_disabled',
                    'login_url': f'/login?org={organizacion.slug}'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # CREAR CITA DE INVITADO (sin crear usuario)
        import secrets
        cita = serializer.save(
            user=None,  # No asignar usuario
            tipo_cita='invitado',
            token_invitado=secrets.token_urlsafe(32)  # Token único para gestionar cita
        )

        # Enviar notificaciones de WhatsApp de forma asíncrona
        try:
            from .tasks_whatsapp import send_whatsapp_confirmation, schedule_appointment_reminders

            # Enviar confirmación inmediata
            send_whatsapp_confirmation.delay(cita.id)

            # Programar recordatorios (24h y 1h antes)
            schedule_appointment_reminders.delay(cita.id)
        except Exception as e:
            # No fallar la creación de la cita si el WhatsApp falla
            logger.warning(f"Error al programar WhatsApp para cita {cita.id}: {str(e)}")

        # Enviar email de confirmación con link para gestionar cita
        email = cita.email_cliente
        if email:
            try:
                # Preparar link para gestionar cita (ver/cancelar)
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                manage_link = f"{frontend_url}/cita/{cita.id}?token={cita.token_invitado}"

                # Preparar mensaje de email
                servicios_nombres = ', '.join([s.nombre for s in cita.servicios.all()])
                fecha_formateada = cita.fecha.strftime('%d/%m/%Y a las %H:%M')

                subject = f'Cita Confirmada - {cita.sede.nombre}'
                message = f"""
Hola {cita.nombre},

¡Tu cita ha sido confirmada exitosamente!

📅 Fecha: {fecha_formateada}
📍 Sede: {cita.sede.nombre}
💼 Servicios: {servicios_nombres}

Para ver los detalles de tu cita o cancelarla, usa este enlace:
{manage_link}

Este enlace es personal e intransferible.

Por favor, llega 10 minutos antes de tu cita.

Si no solicitaste esta cita, puedes ignorar este correo.

¡Te esperamos!
{cita.sede.organizacion.nombre}
                """.strip()

                # Enviar email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    recipient_list=[email],
                    fail_silently=True
                )

                logger.info(f"Cita de invitado creada y email enviado a {email} (ID cita: {cita.id})")

            except Exception as e:
                logger.error(f"Error enviando magic link para cita {cita.id}: {str(e)}")
                # No fallar la creación de la cita si el email falla

        return Response(
            {
                'message': 'Cita creada exitosamente',
                'cita_id': cita.id,
                'email_enviado': True if email else False,
                'detalle': 'Se ha enviado un enlace a tu email para gestionar tu cita' if email else 'Cita creada sin email'
            },
            status=status.HTTP_201_CREATED
        )


class InvitadoCitaView(APIView):
    """
    Permite a invitados ver y cancelar su cita usando el token único.

    GET /api/citas/invitado/{cita_id}/?token={token}
    DELETE /api/citas/invitado/{cita_id}/?token={token}

    SEGURIDAD:
    - No requiere autenticación
    - Requiere token único generado al crear la cita
    - Token es único por cita (no reutilizable)
    """
    permission_classes = [AllowAny]

    def get(self, request, cita_id):
        """Obtener detalles de una cita de invitado"""
        # ARQUITECTURA: Forzar search_path a public donde están los datos
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")

        token = request.query_params.get('token')

        if not token:
            return Response(
                {'error': 'Token requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cita = Cita.objects.get(
                id=cita_id,
                tipo_cita='invitado',
                token_invitado=token
            )
        except Cita.DoesNotExist:
            return Response(
                {'error': 'Cita no encontrada o token inválido'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serializar y retornar
        serializer = GuestCitaSerializer(cita)
        return Response(serializer.data)

    def delete(self, request, cita_id):
        """Cancelar cita de invitado"""
        # ARQUITECTURA: Forzar search_path a public donde están los datos
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")

        token = request.query_params.get('token')

        if not token:
            return Response(
                {'error': 'Token requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cita = Cita.objects.get(
                id=cita_id,
                tipo_cita='invitado',
                token_invitado=token
            )
        except Cita.DoesNotExist:
            return Response(
                {'error': 'Cita no encontrada o token inválido'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar que la cita no esté ya cancelada
        if cita.estado == 'Cancelada':
            return Response(
                {'error': 'Esta cita ya fue cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que no esté muy cerca de la fecha (2 horas de anticipación)
        hours_until = (cita.fecha - timezone.now()).total_seconds() / 3600

        if hours_until < 2:
            return Response(
                {'error': 'No puedes cancelar con menos de 2 horas de anticipación. Por favor contacta directamente a la sede.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cancelar la cita
        cita.estado = 'Cancelada'
        cita.save()

        # Enviar notificación de WhatsApp de cancelación
        try:
            from .tasks_whatsapp import send_whatsapp_cancellation
            send_whatsapp_cancellation.delay(cita.id, reason="Cancelada por el cliente")
        except Exception as e:
            logger.warning(f"Error al enviar WhatsApp de cancelación para cita {cita.id}: {str(e)}")

        # Enviar email de confirmación de cancelación
        if cita.email_cliente:
            try:
                send_mail(
                    subject=f'Cita Cancelada - {cita.sede.nombre}',
                    message=f"""
Hola {cita.nombre},

Tu cita del {cita.fecha.strftime('%d/%m/%Y a las %H:%M')} ha sido cancelada exitosamente.

Si deseas reagendar, puedes visitar nuestra página de agendamiento.

{cita.sede.organizacion.nombre}
                    """.strip(),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    recipient_list=[cita.email_cliente],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Error enviando email de cancelación: {str(e)}")

        return Response({
            'message': 'Cita cancelada exitosamente',
            'cita_id': cita.id
        })
