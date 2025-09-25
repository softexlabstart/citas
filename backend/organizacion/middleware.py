from .thread_locals import set_current_organization

class OrganizacionMiddleware:
    """
    Middleware that sets the organization for the current request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                # Assuming the user has a related PerfilUsuario with an organizacion
                organizacion = request.user.perfilusuario.organizacion
                set_current_organization(organizacion)
            except AttributeError:
                # Handle cases where PerfilUsuario or organizacion might not exist
                set_current_organization(None)
        else:
            set_current_organization(None)

        response = self.get_response(request)
        return response
