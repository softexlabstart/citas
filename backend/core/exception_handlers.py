"""
Custom exception handlers for Django REST Framework.
SECURITY: Prevent information disclosure in production by sanitizing error responses.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.conf import settings

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that sanitizes error responses in production.

    In DEBUG mode: Shows full error details for development
    In PRODUCTION mode: Hides sensitive information and stack traces
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Log the full error for debugging
        request = context.get('request')
        user = request.user if request and hasattr(request, 'user') else 'Anonymous'
        logger.error(
            f"[API ERROR] User: {user}, Path: {request.path if request else 'N/A'}, "
            f"Status: {response.status_code}, Error: {exc.__class__.__name__}: {str(exc)}"
        )

        # SECURITY: In production, sanitize error responses
        if not settings.DEBUG:
            # For validation errors, keep the field-specific messages
            if isinstance(exc, ValidationError):
                # These are safe to show to users
                pass
            else:
                # For other errors, provide generic message
                if response.status_code >= 500:
                    response.data = {
                        'error': 'Ha ocurrido un error en el servidor. Por favor, intenta de nuevo más tarde.',
                        'status_code': response.status_code
                    }
                elif response.status_code == 404:
                    response.data = {
                        'error': 'El recurso solicitado no fue encontrado.',
                        'status_code': 404
                    }
                elif response.status_code == 403:
                    response.data = {
                        'error': 'No tienes permiso para acceder a este recurso.',
                        'status_code': 403
                    }
                elif response.status_code == 401:
                    response.data = {
                        'error': 'Debes iniciar sesión para acceder a este recurso.',
                        'status_code': 401
                    }
                # For 400 errors, keep original validation messages if they exist
                # as they don't reveal sensitive server information

    else:
        # If DRF couldn't handle it, log it and return generic error
        logger.exception(f"[UNHANDLED EXCEPTION] {exc.__class__.__name__}: {str(exc)}")

        if not settings.DEBUG:
            from rest_framework.response import Response
            return Response(
                {
                    'error': 'Ha ocurrido un error inesperado. Por favor, contacta al soporte.',
                    'status_code': 500
                },
                status=500
            )

    return response
