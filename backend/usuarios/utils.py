"""
Utilidades para manejo de perfiles en arquitectura multi-tenant.

Después del cambio de OneToOneField a ForeignKey, un usuario puede tener
múltiples perfiles (uno por organización). Estas funciones ayudan a obtener
el perfil correcto basado en el contexto del request.
"""

from django.core.exceptions import PermissionDenied
from organizacion.thread_locals import get_current_organization
import logging

logger = logging.getLogger(__name__)


def get_user_perfil_for_current_org(user, raise_exception=True):
    """
    Obtiene el perfil del usuario para la organización del request actual.

    Usa el thread-local seteado por OrganizacionMiddleware para determinar
    qué perfil retornar cuando el usuario tiene múltiples organizaciones.

    Args:
        user: Usuario de Django
        raise_exception: Si True, lanza PermissionDenied si no hay contexto de org.
                        Si False, retorna None.

    Returns:
        PerfilUsuario | None

    Raises:
        PermissionDenied: Si no hay organización en contexto y raise_exception=True

    Ejemplos:
        # En una vista con middleware activo
        perfil = get_user_perfil_for_current_org(request.user)

        # En contexto donde falla silenciosamente es aceptable
        perfil = get_user_perfil_for_current_org(request.user, raise_exception=False)
    """
    from usuarios.models import PerfilUsuario

    # Obtener organización del contexto (seteada por middleware)
    org = get_current_organization()

    if not org:
        if raise_exception:
            raise PermissionDenied(
                "No se pudo determinar la organización del request. "
                "Asegúrate de que el middleware OrganizacionMiddleware esté activo."
            )
        # Fallback: retornar primer perfil si solo tiene uno
        perfiles = user.perfiles.all()
        if perfiles.count() == 1:
            return perfiles.first()
        return None

    # Buscar perfil específico de la organización
    try:
        return user.perfiles.select_related('organizacion', 'sede').get(
            organizacion=org
        )
    except PerfilUsuario.DoesNotExist:
        if raise_exception:
            raise PermissionDenied(
                f"El usuario {user.username} no tiene acceso a la organización {org.nombre}"
            )
        return None
    except PerfilUsuario.MultipleObjectsReturned:
        # No debería pasar por unique_together, pero loguear si pasa
        logger.error(
            f"CRITICAL: Usuario {user.id} tiene múltiples perfiles para org {org.id}. "
            f"Revisar constraint unique_together."
        )
        return user.perfiles.filter(organizacion=org).first()


def get_perfil_or_first(user):
    """
    Versión segura que retorna el primer perfil si no hay contexto de organización.

    USAR SOLO en casos donde:
    - El usuario es conocido por tener 1 solo perfil
    - Es aceptable trabajar con cualquiera de sus perfiles
    - Contexto de admin/superuser donde no importa la org

    Args:
        user: Usuario de Django

    Returns:
        PerfilUsuario | None

    Ejemplos:
        # Caso: Usuario que sabemos tiene 1 perfil
        perfil = get_perfil_or_first(user)

        # Caso: Admin viendo datos generales
        if request.user.is_superuser:
            perfil = get_perfil_or_first(some_user)
    """
    from usuarios.models import PerfilUsuario

    # Intentar obtener perfil de la organización actual
    org = get_current_organization()

    if org:
        try:
            return user.perfiles.select_related('organizacion', 'sede').get(
                organizacion=org
            )
        except PerfilUsuario.DoesNotExist:
            pass

    # Fallback: primer perfil disponible
    return user.perfiles.select_related('organizacion', 'sede').first()


def has_perfil_in_current_org(user):
    """
    Verifica si el usuario tiene perfil en la organización actual.

    Útil para validaciones de permisos.

    Args:
        user: Usuario de Django

    Returns:
        bool

    Ejemplo:
        if not has_perfil_in_current_org(request.user):
            raise PermissionDenied("No tienes acceso a esta organización")
    """
    try:
        get_user_perfil_for_current_org(user, raise_exception=True)
        return True
    except PermissionDenied:
        return False
