"""
Permisos personalizados para el sistema multi-tenant con roles.

Este módulo define las clases de permisos que se usan en las vistas de la API
para controlar el acceso basado en roles de usuario.

Sistema de Roles:
- owner: Propietario de la organización (acceso total)
- admin: Administrador global de la organización
- sede_admin: Administrador de sedes específicas
- colaborador: Empleado/recurso que atiende citas
- cliente: Usuario final que agenda citas
"""

from rest_framework.permissions import BasePermission
from organizacion.thread_locals import get_current_organization
from .utils import (
    get_perfil_or_first,
    user_has_role,
    user_can_access_sede,
    get_all_user_roles_in_org
)


class IsSuperAdmin(BasePermission):
    """
    LEGACY: Permiso que solo permite acceso a superadministradores.
    Mantenido por compatibilidad con código existente.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff and request.user.is_superuser


class HasRoleInCurrentOrg(BasePermission):
    """
    Verifica si el usuario tiene uno de los roles requeridos en la organización actual.

    Uso en vistas:
        class MyView(APIView):
            permission_classes = [HasRoleInCurrentOrg]
            required_roles = ['owner', 'admin', 'sede_admin']

    El atributo 'required_roles' debe estar definido en la vista.
    Si no se define, permite acceso a cualquier usuario autenticado con perfil activo.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Superusuarios siempre tienen acceso
        if request.user.is_superuser:
            return True

        org = get_current_organization()
        if not org:
            return False

        # Obtener roles requeridos de la vista
        required_roles = getattr(view, 'required_roles', [])

        # Si no hay roles específicos requeridos, permitir acceso autenticado
        if not required_roles:
            try:
                perfil = get_perfil_or_first(request.user)
                return perfil and perfil.is_active
            except:
                return False

        # Verificar si tiene alguno de los roles requeridos
        user_roles = get_all_user_roles_in_org(request.user, org)
        return any(role in required_roles for role in user_roles)


class IsOwnerOrAdmin(BasePermission):
    """
    Solo propietarios o administradores de la organización.
    Usado para operaciones críticas como gestión de usuarios, configuración, etc.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        org = get_current_organization()
        if not org:
            return False

        return user_has_role(request.user, 'owner', org) or user_has_role(request.user, 'admin', org)


class IsSedeAdmin(BasePermission):
    """
    Permite acceso a administradores de sede (y superiores).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        org = get_current_organization()
        if not org:
            return False

        # Owner, admin o sede_admin pueden acceder
        return (
            user_has_role(request.user, 'owner', org) or
            user_has_role(request.user, 'admin', org) or
            user_has_role(request.user, 'sede_admin', org)
        )


class IsColaborador(BasePermission):
    """
    Permite acceso a colaboradores (y superiores).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        org = get_current_organization()
        if not org:
            return False

        # Cualquier rol que no sea solo cliente puede acceder
        user_roles = get_all_user_roles_in_org(request.user, org)
        return bool(user_roles) and user_roles != ['cliente']


class CanAccessSede(BasePermission):
    """
    Verifica si el usuario puede acceder a una sede específica.
    Se usa como permission a nivel de objeto.

    Uso:
        permission_classes = [IsAuthenticated, CanAccessSede]

        def get_object(self):
            obj = super().get_object()
            self.check_object_permissions(self.request, obj)
            return obj
    """

    def has_object_permission(self, request, view, obj):
        # obj puede ser una Sede o un objeto con atributo 'sede'
        from organizacion.models import Sede

        if isinstance(obj, Sede):
            sede = obj
        else:
            sede = getattr(obj, 'sede', None)

        if not sede:
            return False

        return user_can_access_sede(request.user, sede)


class IsOwnerOrReadOnly(BasePermission):
    """
    Permiso de escritura solo para propietarios/admins.
    Lectura permitida para todos los miembros activos de la organización.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        org = get_current_organization()
        if not org:
            return False

        # Verificar que tenga perfil activo
        perfil = get_perfil_or_first(request.user)
        if not perfil or not perfil.is_active:
            return False

        # GET, HEAD, OPTIONS siempre permitidos
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Escritura solo para owner/admin
        return user_has_role(request.user, 'owner', org) or user_has_role(request.user, 'admin', org)


class HasCustomPermission(BasePermission):
    """
    Verifica si el usuario tiene un permiso personalizado específico.

    Uso en vistas:
        class MyView(APIView):
            permission_classes = [HasCustomPermission]
            required_permission = 'can_view_reports'

    El permiso se busca en el campo JSON 'permissions' del PerfilUsuario.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True  # Si no se especifica permiso, permitir acceso

        try:
            perfil = get_perfil_or_first(request.user)
            if not perfil or not perfil.is_active:
                return False

            return perfil.has_permission(required_permission)
        except:
            return False
