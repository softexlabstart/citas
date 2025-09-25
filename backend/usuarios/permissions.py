from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    """
    Permiso personalizado que solo permite acceso a superadministradores.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff and request.user.is_superuser
