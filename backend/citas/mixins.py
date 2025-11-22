from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class SedeFilteredMixin:
    """
    A mixin to filter a queryset by 'sede_id' from query parameters.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        sede_id = self.request.query_params.get('sede_id')
        if sede_id:
            queryset = queryset.filter(sede_id=sede_id)
        return queryset


class OrganizationIsolationMixin:
    """
    Mixin para validar acceso a recursos según organización del usuario.
    Reutilizable en múltiples ViewSets para evitar código duplicado.
    """

    def _check_organization_permission(self, obj, action='view'):
        """
        Valida que el usuario tenga permiso para acceder al objeto según organización.

        Args:
            obj: El objeto a validar
            action: La acción que se está realizando ('view', 'edit', 'delete')

        Raises:
            PermissionDenied: Si el usuario no tiene permiso
        """
        user = self.request.user
        obj_org = self._get_object_organization(obj)

        if not obj_org:
            return  # Si no hay organización, permitir acceso

        user_org = getattr(user, 'organization', None)

        if not user_org or user_org.id != obj_org.id:
            raise PermissionDenied(
                _("No tienes permiso para {} este recurso.").format(action)
            )

    def _get_object_organization(self, obj):
        """
        Obtiene la organización del objeto.
        Override este método si la relación es diferente.
        """
        # Intentar diferentes formas comunes de obtener la organización
        if hasattr(obj, 'organization'):
            return obj.organization
        elif hasattr(obj, 'sede') and hasattr(obj.sede, 'organization'):
            return obj.sede.organization
        elif hasattr(obj, 'servicio') and hasattr(obj.servicio, 'organization'):
            return obj.servicio.organization
        return None


class SedeAdminPermissionMixin:
    """
    Mixin para validar permisos específicos de administradores de sede.
    Un sede_admin solo puede acceder a recursos de sus sedes asignadas.
    """

    def _check_sede_admin_permission(self, obj):
        """
        Valida que un sede_admin solo pueda acceder a recursos de sus sedes.

        Args:
            obj: El objeto a validar (debe tener un atributo 'sede')

        Raises:
            PermissionDenied: Si el sede_admin no tiene acceso a la sede del objeto
        """
        user = self.request.user

        # Solo aplicar para sede_admin
        if user.role != 'sede_admin':
            return

        obj_sede = self._get_object_sede(obj)

        if not obj_sede:
            return  # Si no hay sede, permitir acceso

        # Verificar que el sede_admin tenga acceso a esta sede
        if not user.sedes.filter(id=obj_sede.id).exists():
            raise PermissionDenied(
                _("No tienes permiso para acceder a recursos de esta sede.")
            )

    def _get_object_sede(self, obj):
        """
        Obtiene la sede del objeto.
        Override este método si la relación es diferente.
        """
        if hasattr(obj, 'sede'):
            return obj.sede
        return None