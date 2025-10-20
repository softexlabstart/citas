from django.urls import resolve
from .thread_locals import set_current_organization, set_current_user
from .models import Organizacion
import logging

logger = logging.getLogger(__name__)


class OrganizacionMiddleware:
    """
    Middleware that sets the organization for the current request.
    Priority order:
    1. HTTP Header X-Organization-ID (for multi-tenant users)
    2. Authenticated user's profile (single organization)
    3. URL slug parameter (for public pages)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user if request.user.is_authenticated else None
        set_current_user(user)

        organizacion = None

        # MULTI-TENANT: Priority 1 - Check HTTP Header X-Organization-ID
        org_id = request.META.get('HTTP_X_ORGANIZATION_ID')
        if org_id:
            try:
                organizacion = Organizacion.objects.get(id=int(org_id))
                logger.debug(f"[OrgMiddleware] Org from header: {organizacion}")
            except (ValueError, TypeError, Organizacion.DoesNotExist) as e:
                logger.warning(f"[OrgMiddleware] Invalid organization ID in header: {org_id} - {e}")

        # Priority 2 - Get organization from authenticated user's profile
        if organizacion is None and request.user.is_authenticated:
            logger.debug(f"[OrgMiddleware] User: {request.user.username}, is_staff: {request.user.is_staff}, is_superuser: {request.user.is_superuser}")
            try:
                # MULTI-TENANT: Check if user has multiple profiles
                # CRITICAL: Use PerfilUsuario.all_objects to bypass OrganizacionManager filtering
                # because at this point no organization is set yet (we're setting it now!)
                from usuarios.models import PerfilUsuario
                perfiles = PerfilUsuario.all_objects.filter(user=request.user).select_related('organizacion')
                perfiles_count = perfiles.count()

                if perfiles_count == 1:
                    # Single profile: use that organization
                    perfil = perfiles.first()
                    if perfil:
                        organizacion = perfil.organizacion
                        logger.debug(f"[OrgMiddleware] Org from single profile: {organizacion}")
                elif perfiles_count > 1:
                    # Multiple profiles but no header: use the first active profile as fallback
                    logger.warning(f"[OrgMiddleware] User {request.user.username} has {perfiles_count} profiles but no X-Organization-ID header. Using first active profile.")
                    perfil = perfiles.filter(is_active=True).first()
                    if perfil:
                        organizacion = perfil.organizacion
                        logger.debug(f"[OrgMiddleware] Org from first active profile (fallback): {organizacion}")
                else:
                    logger.debug(f"[OrgMiddleware] User {request.user.username} has no profiles")

            except AttributeError as e:
                # User might not have perfiles attribute
                logger.warning(f"[OrgMiddleware] User has no perfiles: {e}")

        # Priority 3 - Get organization from URL slug (public pages)
        if organizacion is None:
            try:
                resolver_match = resolve(request.path_info)
                if 'organizacion_slug' in resolver_match.kwargs:
                    slug = resolver_match.kwargs['organizacion_slug']
                    organizacion = Organizacion.objects.get(nombre__iexact=slug)
                    logger.debug(f"[OrgMiddleware] Org from URL slug: {organizacion}")
            except Exception as e:
                logger.debug(f"[OrgMiddleware] No org from URL: {e}")

        set_current_organization(organizacion)

        response = self.get_response(request)
        return response
