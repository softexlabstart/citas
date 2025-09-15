from rest_framework.permissions import BasePermission, SAFE_METHODS
from usuarios.models import PerfilUsuario

class IsAdminOrSedeAdminOrReadOnly(BasePermission):
    """
    Allows read-only access to anyone, but write access only to admins or sede admins.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to authenticated staff or sede admins.
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_staff:
            return True
            
        try:
            # Check if the user has a profile and administers any sedes
            return request.user.perfil.sedes_administradas.exists()
        except (AttributeError, PerfilUsuario.DoesNotExist):
            # Catches cases where user has no 'perfil' attribute or profile
            return False

class IsOwnerOrAdminForCita(BasePermission):
    """
    Custom permission to only allow owners of a Cita or relevant admins to interact with it.
    """
    def has_object_permission(self, request, view, obj):
        # Staff users have full control.
        if request.user.is_staff:
            return True

        # Sede administrators can manage appointments in their sedes.
        try:
            perfil = request.user.perfil
            if perfil.sedes_administradas.exists() and obj.sede in perfil.sedes_administradas.all():
                return True
        except (AttributeError, PerfilUsuario.DoesNotExist):
            pass

        # The user who booked the appointment can manage it.
        return obj.user == request.user

class IsAdminOrSedeAdmin(BasePermission):
    """
    Allows access only to admin users or sede administrators.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_staff:
            return True
            
        try:
            return request.user.perfil.sedes_administradas.exists()
        except (AttributeError, PerfilUsuario.DoesNotExist):
            return False