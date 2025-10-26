"""
Middleware para configurar el PostgreSQL search_path según el tenant actual.

Este middleware se ejecuta DESPUÉS de OrganizacionMiddleware (que identifica el tenant)
y configura la conexión a PostgreSQL para usar el schema correcto.
"""

from django.db import connection
from organizacion.thread_locals import get_current_organization
import logging

logger = logging.getLogger(__name__)


class TenantSchemaMiddleware:
    """
    Middleware que configura el search_path de PostgreSQL según el tenant actual.

    El search_path determina en qué schema busca PostgreSQL primero las tablas.

    Ejemplo:
    - Sin tenant: SET search_path TO public;
    - Con tenant: SET search_path TO tenant_barberia_juan_abc123, public;

    Así, cuando Django ejecuta:
        SELECT * FROM citas_cita;

    PostgreSQL busca:
    1. tenant_barberia_juan_abc123.citas_cita (tablas del tenant)
    2. public.citas_cita (fallback, no debería existir)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtener el tenant actual del thread-local storage
        org = get_current_organization()

        if org and org.schema_name:
            # Configurar search_path: primero el schema del tenant, luego public
            schema_name = org.schema_name
            search_path = f"{schema_name}, public"

            logger.debug(f"[TenantSchema] Setting search_path to: {search_path}")

            try:
                with connection.cursor() as cursor:
                    # SET LOCAL para que solo afecte esta transacción
                    cursor.execute(f"SET search_path TO {search_path};")

            except Exception as e:
                logger.error(f"[TenantSchema] Error setting search_path: {e}")

        else:
            # Sin tenant, usar solo public
            logger.debug("[TenantSchema] No tenant, using default search_path (public)")

            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET search_path TO public;")

            except Exception as e:
                logger.error(f"[TenantSchema] Error setting default search_path: {e}")

        # Procesar la request
        response = self.get_response(request)

        # Limpiar el search_path después de la request
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public;")
        except Exception:
            pass  # Ignorar errores en cleanup

        return response
