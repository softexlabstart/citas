from django.core.mail import send_mail
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from citas.permissions import IsOwnerAdminOrSedeAdmin
from usuarios.utils import get_perfil_or_first

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