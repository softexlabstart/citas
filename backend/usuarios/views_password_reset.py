"""
Vistas para recuperación de contraseña.
Permite a los usuarios solicitar y confirmar el reset de contraseña.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import PasswordResetToken

logger = logging.getLogger(__name__)


class RequestPasswordResetView(APIView):
    """
    Endpoint para solicitar reset de contraseña.
    No requiere autenticación.

    POST /api/usuarios/request-password-reset/
    {
        "email": "usuario@example.com"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()

        if not email:
            return Response(
                {"error": "El email es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar usuario por email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Por seguridad, no revelar si el email existe o no
            # Enviar respuesta exitosa de todos modos
            return Response(
                {"message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña."},
                status=status.HTTP_200_OK
            )

        try:
            # Eliminar tokens anteriores del usuario
            PasswordResetToken.objects.filter(user=user).delete()

            # Crear nuevo token
            reset_token = PasswordResetToken.objects.create(user=user)

            # Construir enlace de reset
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            reset_link = f"{frontend_url}/reset-password?token={reset_token.token}"

            # Preparar email
            subject = 'Recuperación de Contraseña - Sistema de Citas'
            message = f"""
Hola {user.first_name or user.username},

Recibimos una solicitud para restablecer tu contraseña.

Para crear una nueva contraseña, haz clic en el siguiente enlace:

{reset_link}

Este enlace es válido por 30 minutos y solo puede usarse una vez.

Si no solicitaste restablecer tu contraseña, puedes ignorar este correo de forma segura.

Saludos,
Equipo de {getattr(settings, 'SITE_NAME', 'Sistema de Citas')}
            """.strip()

            # Enviar email
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=[email],
                fail_silently=False
            )

            logger.info(f"Token de reset de contraseña enviado a {email}")

            return Response(
                {"message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error enviando email de reset de contraseña: {str(e)}")
            return Response(
                {"error": "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfirmPasswordResetView(APIView):
    """
    Endpoint para confirmar reset de contraseña.
    No requiere autenticación.

    POST /api/usuarios/confirm-password-reset/
    {
        "token": "uuid-token",
        "new_password": "nueva_contraseña"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token_str = request.data.get('token', '').strip()
        new_password = request.data.get('new_password', '').strip()

        if not token_str or not new_password:
            return Response(
                {"error": "El token y la nueva contraseña son requeridos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar longitud de contraseña
        if len(new_password) < 6:
            return Response(
                {"error": "La contraseña debe tener al menos 6 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Buscar token
            reset_token = PasswordResetToken.objects.get(token=token_str)

            # Verificar si el token es válido
            if not reset_token.is_valid():
                return Response(
                    {"error": "El enlace ha expirado o ya ha sido utilizado. Por favor, solicita uno nuevo."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Cambiar contraseña
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Marcar token como usado
            reset_token.used = True
            reset_token.save()

            logger.info(f"Contraseña restablecida para {user.email}")

            return Response(
                {"message": "Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesión."},
                status=status.HTTP_200_OK
            )

        except PasswordResetToken.DoesNotExist:
            return Response(
                {"error": "El enlace de recuperación es inválido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error restableciendo contraseña: {str(e)}")
            return Response(
                {"error": "Ocurrió un error al restablecer tu contraseña. Por favor, intenta nuevamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
