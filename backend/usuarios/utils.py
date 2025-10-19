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


# ==================== NUEVOS HELPERS PARA SISTEMA DE ROLES ====================

def get_user_role_in_org(user, organizacion):
    """
    Obtiene el rol principal de un usuario en una organización específica.

    Args:
        user: Usuario Django
        organizacion: Instancia de Organizacion

    Returns:
        str: 'owner', 'admin', 'sede_admin', 'colaborador', 'cliente', o None
    """
    from usuarios.models import PerfilUsuario

    try:
        perfil = PerfilUsuario.all_objects.get(user=user, organizacion=organizacion, is_active=True)
        return perfil.role
    except PerfilUsuario.DoesNotExist:
        return None


def get_all_user_roles_in_org(user, organizacion):
    """
    Obtiene TODOS los roles de un usuario en una organización (principal + adicionales).

    Args:
        user: Usuario Django
        organizacion: Instancia de Organizacion

    Returns:
        list: Lista de roles, ej: ['colaborador', 'cliente']
    """
    from usuarios.models import PerfilUsuario

    try:
        perfil = PerfilUsuario.all_objects.get(user=user, organizacion=organizacion, is_active=True)
        return perfil.all_roles
    except PerfilUsuario.DoesNotExist:
        return []


def user_has_role(user, role, organizacion=None):
    """
    Verifica si un usuario tiene un rol específico.

    Args:
        user: Usuario Django
        role: Rol a verificar ('owner', 'admin', 'sede_admin', 'colaborador', 'cliente')
        organizacion: Instancia de Organizacion (opcional, usa contexto actual si no se provee)

    Returns:
        bool: True si tiene el rol
    """
    from usuarios.models import PerfilUsuario

    if not organizacion:
        organizacion = get_current_organization()

    if not organizacion:
        return False

    try:
        perfil = PerfilUsuario.all_objects.get(user=user, organizacion=organizacion, is_active=True)
        return perfil.has_role(role)
    except PerfilUsuario.DoesNotExist:
        return False


def user_can_access_sede(user, sede):
    """
    Verifica si un usuario puede acceder a una sede específica.

    Args:
        user: Usuario Django
        sede: Instancia de Sede

    Returns:
        bool: True si tiene acceso
    """
    from usuarios.models import PerfilUsuario

    if user.is_superuser:
        return True

    try:
        perfil = PerfilUsuario.all_objects.get(
            user=user,
            organizacion=sede.organizacion,
            is_active=True
        )
        return sede in perfil.accessible_sedes
    except PerfilUsuario.DoesNotExist:
        return False


def get_user_accessible_sedes(user, organizacion=None):
    """
    Retorna todas las sedes accesibles para un usuario.

    Args:
        user: Usuario Django
        organizacion: Instancia de Organizacion (opcional, usa contexto actual si no se provee)

    Returns:
        QuerySet: Sedes accesibles
    """
    from usuarios.models import PerfilUsuario
    from organizacion.models import Sede

    if user.is_superuser:
        if organizacion:
            return Sede.all_objects.filter(organizacion=organizacion)
        return Sede.all_objects.all()

    if not organizacion:
        organizacion = get_current_organization()

    if not organizacion:
        return Sede.all_objects.none()

    try:
        perfil = PerfilUsuario.all_objects.get(
            user=user,
            organizacion=organizacion,
            is_active=True
        )
        return perfil.accessible_sedes
    except PerfilUsuario.DoesNotExist:
        return Sede.all_objects.none()


def get_user_organizations(user):
    """
    Retorna todas las organizaciones donde el usuario tiene membresía activa.

    Args:
        user: Usuario Django

    Returns:
        QuerySet: Organizaciones con perfiles activos
    """
    from organizacion.models import Organizacion

    return Organizacion.objects.filter(
        miembros__user=user,
        miembros__is_active=True
    ).distinct()


def switch_organization_context(request, organizacion_id):
    """
    Cambia el contexto de organización del usuario en la sesión.
    Útil para el selector de organización en el frontend.

    Args:
        request: HttpRequest
        organizacion_id: ID de la organización

    Returns:
        bool: True si el cambio fue exitoso
    """
    from organizacion.models import Organizacion
    from usuarios.models import PerfilUsuario
    from organizacion.thread_locals import set_current_organization

    try:
        org = Organizacion.objects.get(id=organizacion_id)

        # Verificar que el usuario tiene acceso
        perfil = PerfilUsuario.all_objects.get(
            user=request.user,
            organizacion=org,
            is_active=True
        )

        # Cambiar contexto
        set_current_organization(org)
        request.session['current_organization_id'] = org.id

        return True
    except (Organizacion.DoesNotExist, PerfilUsuario.DoesNotExist):
        return False
