from django.core.mail import send_mail
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

class SendMarketingEmailView(APIView):
    """
    API view to send marketing emails to clients.
    Only accessible by admin users.
    """
    permission_classes = [permissions.IsAdminUser]

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
            # Otherwise, get all non-admin users (clients)
            client_users = User.objects.filter(
                is_staff=False, is_superuser=False
            ).exclude(groups__name='SedeAdmin')
            recipient_list = [user.email for user in client_users if user.email]

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