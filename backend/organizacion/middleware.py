from django.urls import resolve
from .thread_locals import set_current_organization, set_current_user
from .models import Organizacion

class OrganizacionMiddleware:
    """
    Middleware that sets the organization for the current request.
    It tries to determine the organization from the authenticated user first.
    If the user is not authenticated, it looks for an 'organizacion_slug'
    in the URL.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(request.user if request.user.is_authenticated else None)

        organizacion = None
        
        # 1. Try to get organization from the authenticated user
        if request.user.is_authenticated:
            print(f"[OrgMiddleware] User: {request.user.username}")
            try:
                # The related_name in PerfilUsuario is 'perfil'
                organizacion = request.user.perfil.organizacion
                print(f"[OrgMiddleware] Org from profile: {organizacion}")
            except AttributeError:
                # User might not have a profile or organization assigned
                print("[OrgMiddleware] User has no profile or organization")
                pass

        # 2. If no organization yet, try to get it from the URL
        # This is for public pages like booking forms.
        # Assumes you have a URL pattern like: path('<slug:organizacion_slug>/...', ...)
        if organizacion is None:
            try:
                # Use resolve to get URL kwargs from the path
                resolver_match = resolve(request.path_info)
                if 'organizacion_slug' in resolver_match.kwargs:
                    slug = resolver_match.kwargs['organizacion_slug']
                    # Use .get() to avoid DoesNotExist exception
                    organizacion = Organizacion.objects.get(nombre__iexact=slug)
            except Exception:
                # URL might not match or organization doesn't exist
                pass

        set_current_organization(organizacion)

        response = self.get_response(request)
        return response
