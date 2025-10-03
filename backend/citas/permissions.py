from rest_framework.permissions import BasePermission, SAFE_METHODS
from usuarios.models import PerfilUsuario
from .models import Colaborador

class IsSuperUser(BasePermission):
    """
    Permite acceso solo a superusuarios.
    - Superusuarios: Acceso total al panel de Django y frontend
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsSedeAdmin(BasePermission):
    """
    Permite acceso a administradores de sede.
    - Administradores de sede: Acceso al panel de administración del frontend
    - Pueden ver informes, marketing, configuración avanzada
    - Solo de las sedes que administran
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            return request.user.perfil.sedes_administradas.exists()
        except (AttributeError, PerfilUsuario.DoesNotExist):
            return False


class IsColaborador(BasePermission):
    """
    Permite acceso a colaboradores.
    - Colaboradores: Solo pueden ver citas asignadas a ellos
    - Pueden crear citas a nombre de clientes de su sede
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return Colaborador.all_objects.filter(usuario=request.user).exists()


class IsClient(BasePermission):
    """
    Permite acceso a clientes regulares.
    - Clientes: Solo pueden ver historial de sus citas
    - Pueden ver servicios y sacar citas
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Un cliente es un usuario autenticado que no es superuser, ni sede admin, ni colaborador
        if request.user.is_superuser or request.user.is_staff:
            return False

        try:
            if request.user.perfil.sedes_administradas.exists():
                return False
        except (AttributeError, PerfilUsuario.DoesNotExist):
            pass

        if Colaborador.all_objects.filter(usuario=request.user).exists():
            return False

        return True


class IsAdminOrSedeAdminOrReadOnly(BasePermission):
    """
    Permite lectura a todos (incluyendo anónimos si proporcionan sede_id),
    escritura solo a admins o administradores de sede.
    """
    def has_permission(self, request, view):
        # Lectura permitida a cualquiera (autenticado o anónimo con sede_id)
        if request.method in SAFE_METHODS:
            # Si el usuario está autenticado, permitir
            if request.user and request.user.is_authenticated:
                return True
            # Si es anónimo pero proporciona sede_id, permitir (para reservas públicas)
            if hasattr(request, 'query_params') and request.query_params.get('sede_id'):
                return True
            # También verificar GET params
            if hasattr(request, 'GET') and request.GET.get('sede_id'):
                return True
            return False

        # Escritura solo para superusers o admins de sede
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        try:
            return request.user.perfil.sedes_administradas.exists()
        except (AttributeError, PerfilUsuario.DoesNotExist):
            return False


class IsOwnerOrAdminForCita(BasePermission):
    """
    Permiso para citas:
    - Superusuarios: acceso total
    - Administradores de sede: pueden ver/editar citas de sus sedes
    - Colaboradores: pueden ver/editar citas asignadas a ellos
    - Clientes: solo pueden ver/editar sus propias citas
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Superusuarios tienen control total
        if request.user.is_superuser:
            return True

        # Administradores de sede pueden gestionar citas de sus sedes
        try:
            perfil = request.user.perfil
            if perfil.sedes_administradas.exists() and obj.sede in perfil.sedes_administradas.all():
                return True
        except (AttributeError, PerfilUsuario.DoesNotExist):
            pass

        # Colaboradores pueden gestionar citas asignadas a ellos
        try:
            colaborador = Colaborador.all_objects.get(usuario=request.user)
            if colaborador in obj.colaboradores.all():
                return True
        except Colaborador.DoesNotExist:
            pass

        # El usuario que reservó la cita puede gestionarla
        return obj.user == request.user


class IsAdminOrSedeAdmin(BasePermission):
    """
    Permite acceso solo a superusuarios o administradores de sede.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        try:
            return request.user.perfil.sedes_administradas.exists()
        except (AttributeError, PerfilUsuario.DoesNotExist):
            return False


class IsColaboradorOrAdmin(BasePermission):
    """
    Permite acceso a:
    - Superusuarios (acceso total)
    - Administradores de sede (acceso a sus sedes)
    - Colaboradores (pueden crear citas a nombre de clientes)
    - Clientes regulares (solo sus propias citas)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios siempre tienen acceso
        if request.user.is_superuser:
            return True

        # Administradores de sede tienen acceso
        try:
            if request.user.perfil.sedes_administradas.exists():
                return True
        except (AttributeError, PerfilUsuario.DoesNotExist):
            pass

        # Colaboradores tienen acceso
        if Colaborador.all_objects.filter(usuario=request.user).exists():
            return True

        # Clientes regulares también tienen acceso (limitado por object permissions)
        return True

    def has_object_permission(self, request, view, obj):
        # Superusuarios tienen control total
        if request.user.is_superuser:
            return True

        # Administradores de sede pueden gestionar citas de sus sedes
        try:
            perfil = request.user.perfil
            if perfil.sedes_administradas.exists() and obj.sede in perfil.sedes_administradas.all():
                return True
        except (AttributeError, PerfilUsuario.DoesNotExist):
            pass

        # Colaboradores pueden gestionar citas asignadas a ellos
        try:
            colaborador = Colaborador.all_objects.get(usuario=request.user)
            if colaborador in obj.colaboradores.all():
                return True
        except Colaborador.DoesNotExist:
            pass

        # El usuario que reservó la cita puede gestionarla
        return obj.user == request.user


class CanAccessOrganizationData(BasePermission):
    """
    Verifica que el usuario solo pueda acceder a datos de su organización.
    Multi-tenant: usuarios no pueden ver datos de otras organizaciones.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusuarios pueden acceder a todo
        if request.user.is_superuser:
            return True

        # Otros usuarios deben tener un perfil con organización
        try:
            return hasattr(request.user, 'perfil') and request.user.perfil.organizacion is not None
        except (AttributeError, PerfilUsuario.DoesNotExist):
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        try:
            user_org = request.user.perfil.organizacion

            # Verificar que el objeto pertenece a la misma organización
            if hasattr(obj, 'organizacion'):
                return obj.organizacion == user_org
            elif hasattr(obj, 'sede'):
                return obj.sede.organizacion == user_org
            elif hasattr(obj, 'sede__organizacion'):
                return obj.sede.organizacion == user_org

            return False
        except (AttributeError, PerfilUsuario.DoesNotExist):
            return False
