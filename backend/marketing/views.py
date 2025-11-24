from django.core.mail import send_mail
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from citas.permissions import IsOwnerAdminOrSedeAdmin
from usuarios.utils import get_perfil_or_first
from citas.whatsapp.whatsapp_service import whatsapp_service
from django.core.files.storage import default_storage
from django.conf import settings
import os

class SendMarketingEmailView(APIView):
    """
    API view to send marketing emails to clients.
    Only accessible by users with administrative roles:
    - Superusers
    - Propietarios (owner)
    - Administradores (admin)
    - Administradores de Sede (sede_admin)
    """
    permission_classes = [IsOwnerAdminOrSedeAdmin]

    def post(self, request, *args, **kwargs):
        subject = request.data.get('subject')
        message = request.data.get('message')

        if not subject or not message:
            return Response(
                {'error': 'Subject and message are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recipient_emails = request.data.get('recipient_emails')

        if recipient_emails:
            # If specific recipients are provided, use them
            recipient_list = recipient_emails
        else:
            # Otherwise, get all users with role 'cliente' from the new role system
            # Filter by organization if user is not superuser
            user = request.user

            if user.is_superuser:
                # Superusers can email clients from all organizations
                client_users = User.objects.filter(perfiles__role='cliente')
            else:
                # Regular admins can only email clients from their organization
                perfil = get_perfil_or_first(user)
                if not perfil or not perfil.organizacion:
                    return Response(
                        {'error': 'No se pudo determinar tu organización.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                client_users = User.objects.filter(
                    perfiles__role='cliente',
                    perfiles__organizacion=perfil.organizacion
                )

            recipient_list = [user.email for user in client_users.distinct() if user.email]

        if not recipient_list:
            return Response(
                {'message': 'No client recipients found.'},
                status=status.HTTP_200_OK
            )

        try:
            send_mail(
                subject,
                message,
                None,  # Uses DEFAULT_FROM_EMAIL from settings
                recipient_list,
                fail_silently=False,
            )
            return Response(
                {'message': f'Email sent successfully to {len(recipient_list)} recipients.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SendMarketingWhatsAppView(APIView):
    """
    API view to send marketing WhatsApp messages to clients.
    Supports media/image attachments.

    Only accessible by users with administrative roles:
    - Superusers
    - Propietarios (owner)
    - Administradores (admin)
    - Administradores de Sede (sede_admin)
    """
    permission_classes = [IsOwnerAdminOrSedeAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        message = request.data.get('message')

        if not message:
            return Response(
                {'error': 'Message is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si WhatsApp está configurado
        if not whatsapp_service.is_configured():
            return Response(
                {'error': 'WhatsApp no está configurado. Contacte al administrador.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Obtener organización del usuario
        user = request.user
        if user.is_superuser:
            return Response(
                {'error': 'Los superusuarios deben especificar una organización.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        perfil = get_perfil_or_first(user)
        if not perfil or not perfil.organizacion:
            return Response(
                {'error': 'No se pudo determinar tu organización.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        organizacion = perfil.organizacion

        # Verificar si WhatsApp está habilitado para la organización
        if not organizacion.whatsapp_enabled:
            return Response(
                {'error': 'WhatsApp no está habilitado para tu organización.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Manejar imagen/media si está presente
        media_url = None
        if 'image' in request.FILES:
            image_file = request.FILES['image']

            # Validar tamaño (max 5MB)
            if image_file.size > 5 * 1024 * 1024:
                return Response(
                    {'error': 'La imagen no puede superar 5MB.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar tipo de archivo
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_ext = os.path.splitext(image_file.name)[1].lower()
            if file_ext not in allowed_extensions:
                return Response(
                    {'error': f'Tipo de archivo no permitido. Use: {", ".join(allowed_extensions)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Guardar archivo
            file_path = f'whatsapp_marketing/{organizacion.id}/{image_file.name}'
            saved_path = default_storage.save(file_path, image_file)

            # Generar URL completa (públicamente accesible)
            media_url = request.build_absolute_uri(default_storage.url(saved_path))

        # Obtener destinatarios
        recipient_phones = request.data.getlist('recipient_phones')

        # Obtener clientes (usuarios con rol 'cliente') de la organización
        client_users = User.objects.filter(
            perfiles__role='cliente',
            perfiles__organizacion=organizacion
        ).prefetch_related('perfiles').distinct()

        if recipient_phones:
            # Si se proporcionan teléfonos específicos, filtrar por esos teléfonos
            client_users = client_users.filter(perfiles__telefono__in=recipient_phones)

        # Construir listas de teléfonos y nombres
        recipient_phones_list = []
        recipient_names_list = []

        for user in client_users:
            # Obtener perfil de la organización actual
            perfil = get_perfil_or_first(user)
            if perfil and perfil.telefono:
                recipient_phones_list.append(perfil.telefono)
                nombre_completo = f"{user.first_name} {user.last_name}".strip()
                if not nombre_completo:
                    nombre_completo = user.email.split('@')[0]
                recipient_names_list.append(nombre_completo)

        if not recipient_phones_list:
            return Response(
                {'message': 'No se encontraron clientes con número de teléfono.'},
                status=status.HTTP_200_OK
            )

        try:
            # Enviar mensajes
            sent_count, failed_count, messages = whatsapp_service.send_bulk_marketing_message(
                organizacion=organizacion,
                recipient_phones=recipient_phones_list,
                recipient_names=recipient_names_list,
                message_body=message,
                media_url=media_url
            )

            return Response({
                'message': f'WhatsApp enviado exitosamente.',
                'sent': sent_count,
                'failed': failed_count,
                'total': len(recipient_phones_list)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Error al enviar WhatsApp: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )