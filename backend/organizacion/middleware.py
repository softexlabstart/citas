from django.urls import resolve
from django.contrib.auth.models import AnonymousUser
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

    NOTE: For JWT authentication, this middleware needs to extract the user
    from the JWT token since DRF's JWT authentication happens at the view level,
    not at the middleware level.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def _get_jwt_user(self, request):
        """
        Extract and validate JWT token to get the authenticated user.
        This is necessary because DRF's JWT authentication happens at view level.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth import get_user_model

            # Validate and decode token
            access_token = AccessToken(token)
            user_id = access_token['user_id']

            # Get user from database
            User = get_user_model()
            user = User.objects.get(id=user_id)
            return user

        except Exception as e:
            logger.debug(f"[OrgMiddleware] JWT validation failed: {e}")
            return None

    def __call__(self, request):
        # Try to get user from JWT token first (for API requests)
        jwt_user = self._get_jwt_user(request)

        # Use JWT user if available, otherwise fall back to session user
        if jwt_user:
            user = jwt_user
        else:
            user = request.user if request.user.is_authenticated else None

        set_current_user(user)

        organizacion = None

        # MULTI-TENANT: Priority 1 - Check HTTP Header X-Organization-ID
        org_id = request.META.get('HTTP_X_ORGANIZATION_ID')
        if org_id and user:
            try:
                requested_org = Organizacion.objects.get(id=int(org_id))

                # SECURITY: Validate that user has permission to access this organization
                # Check if user has an active profile in the requested organization
                from usuarios.models import PerfilUsuario
                has_access = PerfilUsuario.all_objects.filter(
                    user=user,
                    organizacion=requested_org,
                    is_active=True
                ).exists()

                if has_access or user.is_superuser:
                    organizacion = requested_org
                    logger.debug(f"[OrgMiddleware] Org from header (validated): {organizacion}")
                else:
                    # User attempting to access unauthorized organization
                    logger.warning(
                        f"[SECURITY] User {user.username} attempted to access "
                        f"unauthorized organization {requested_org.id} ({requested_org.nombre}) "
                        f"via X-Organization-ID header. Access denied."
                    )
                    # Do not set organization - fall through to next priority

            except (ValueError, TypeError, Organizacion.DoesNotExist) as e:
                logger.warning(f"[OrgMiddleware] Invalid organization ID in header: {org_id} - {e}")

        # Priority 2 - Get organization from authenticated user's profile
        if organizacion is None and user:
            logger.debug(f"[OrgMiddleware] User: {user.username}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
            try:
                # MULTI-TENANT: Check if user has multiple profiles
                # CRITICAL: Use PerfilUsuario.all_objects to bypass OrganizacionManager filtering
                # because at this point no organization is set yet (we're setting it now!)
                from usuarios.models import PerfilUsuario
                perfiles = PerfilUsuario.all_objects.filter(user=user).select_related('organizacion')
                perfiles_count = perfiles.count()

                if perfiles_count == 1:
                    # Single profile: use that organization
                    perfil = perfiles.first()
                    if perfil:
                        organizacion = perfil.organizacion
                        logger.debug(f"[OrgMiddleware] Org from single profile: {organizacion}")
                elif perfiles_count > 1:
                    # Multiple profiles but no header: use the first active profile as fallback
                    logger.info(f"[OrgMiddleware] User {user.username} has {perfiles_count} profiles but no X-Organization-ID header. Using first active profile.")
                    perfil = perfiles.filter(is_active=True).first()
                    if perfil:
                        organizacion = perfil.organizacion
                        logger.debug(f"[OrgMiddleware] Org from first active profile (fallback): {organizacion}")
                else:
                    logger.debug(f"[OrgMiddleware] User {user.username} has no profiles")

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
