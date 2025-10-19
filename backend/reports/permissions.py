from rest_framework import permissions

# MULTI-TENANT: Import helper for profile management
from usuarios.utils import get_perfil_or_first


class IsAdminOrSedeAdmin(permissions.BasePermission):
    """
    Permiso personalizado que permite acceso a:
    - Superusuarios (acceso completo a todas las organizaciones)
    - Administradores de organización (acceso solo a su organización)
    - Administradores de sede (acceso solo a su organización)
    """

    def has_permission(self, request, view):
        # Usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios tienen acceso completo
        if request.user.is_superuser:
            return True

        # Verificar si es administrador de organización
        perfil = get_perfil_or_first(request.user)
        if perfil and perfil.organizacion:
            return True

        # Verificar si es administrador de sede
        if hasattr(request.user, 'groups'):
            if request.user.groups.filter(name='SedeAdmin').exists():
                return True

        return False
