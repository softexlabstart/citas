"""
Custom throttling classes para proteger endpoints públicos.

IMPORTANTE: Estas clases previenen:
- Spam de citas por bots
- Flooding de emails
- Saturación de base de datos
- Ataques DoS
"""
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle
import logging

logger = logging.getLogger(__name__)


class PublicBookingIPThrottle(AnonRateThrottle):
    """
    Throttle para creación de citas públicas por IP.

    Límite: 5 requests por hora por IP

    Esto previene que un solo atacante desde una IP:
    - Cree citas en masa
    - Sature el sistema con requests
    """
    scope = 'public_booking_ip'
    rate = '5/hour'

    def throttle_failure(self):
        """Log intentos de throttle para análisis de seguridad"""
        logger.warning(
            "[SECURITY] Public booking IP throttle limit exceeded"
        )
        return super().throttle_failure()


class PublicBookingEmailThrottle(SimpleRateThrottle):
    """
    Throttle para creación de citas públicas por email.

    Límite: 3 requests por día por email

    Esto previene que un atacante:
    - Use el mismo email para spam
    - Abuse del sistema de magic links
    - Sature el buzón del usuario
    """
    scope = 'public_booking_email'
    rate = '3/day'

    def get_cache_key(self, request, view):
        """
        Usar el email del cliente como clave de cache.
        Si no hay email en el request, usar IP como fallback.
        """
        email = None

        # Intentar obtener email del request data
        if hasattr(request, 'data') and isinstance(request.data, dict):
            email = request.data.get('email_cliente')

        if not email:
            # Fallback a IP si no hay email
            return None

        # Normalizar email (lowercase, trim)
        email = email.lower().strip()

        return self.cache_format % {
            'scope': self.scope,
            'ident': email
        }

    def throttle_failure(self):
        """Log intentos de throttle por email"""
        logger.warning(
            f"[SECURITY] Public booking email throttle limit exceeded. "
            f"Check logs for email address."
        )
        return super().throttle_failure()


class MagicLinkThrottle(SimpleRateThrottle):
    """
    Throttle para solicitudes de magic link.

    Límite: 3 requests por hora por email

    Previene:
    - Enumeración de emails válidos
    - Flooding de emails a usuarios
    - Ataques de fuerza bruta para descubrir usuarios
    """
    scope = 'magic_link'
    rate = '3/hour'

    def get_cache_key(self, request, view):
        """Usar email como clave de cache"""
        email = None

        if hasattr(request, 'data') and isinstance(request.data, dict):
            email = request.data.get('email')

        if not email:
            # Fallback a IP
            ident = self.get_ident(request)
            return self.cache_format % {
                'scope': self.scope,
                'ident': ident
            }

        email = email.lower().strip()
        return self.cache_format % {
            'scope': self.scope,
            'ident': email
        }

    def throttle_failure(self):
        """Log intentos sospechosos de magic link"""
        logger.warning(
            f"[SECURITY] Magic link throttle limit exceeded"
        )
        return super().throttle_failure()
