from django.contrib.auth import authenticate, login
from django.core.exceptions import PermissionDenied
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from organizacion.models import Sede
from .models import PerfilUsuario, MagicLinkToken, Invitation
from .serializers import UserSerializer, MyTokenObtainPairSerializer, ClientSerializer, ClientEmailSerializer, MultiTenantRegistrationSerializer, InvitationSerializer, OrganizacionSerializer, SedeDetailSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from .permissions import IsSuperAdmin
import pytz
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User, Group # Added Group
from citas.permissions import IsAdminOrSedeAdmin
from rest_framework.decorators import action
from django.db.models import Count, Q, Sum
from citas.models import Cita
from citas.serializers import CitaSerializer
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

# MULTI-TENANT: Import helpers for profile management
from .utils import get_user_perfil_for_current_org, get_perfil_or_first

# SECURITY: Import throttles
from core.throttling import MagicLinkThrottle

logger = logging.getLogger(__name__)

class ClientEmailListView(generics.ListAPIView):
    """
    Vista optimizada para obtener emails de clientes.
    Soporta filtrado por IDs y retorna todos los resultados sin paginación cuando ?all=true.
    """
    serializer_class = ClientEmailSerializer
    permission_classes = [IsAdminOrSedeAdmin]
    pagination_class = None  # Deshabilitar paginación por defecto

    def get_queryset(self):
        """
        Retorna queryset de clientes filtrado por parámetros.
        Toda la lógica de filtrado está aquí, siguiendo el patrón DRF.
        """
        # Base queryset: usuarios activos que no son staff, sede admin o colaboradores
        queryset = User.objects.filter(
            is_active=True,
            is_staff=False
        ).exclude(
            groups__name__in=['SedeAdmin', 'Recurso']
        )

        # Filtrar por IDs específicos si se proporcionan
        client_ids = self.request.query_params.get('ids')
        if client_ids:
            try:
                client_ids = [int(id.strip()) for id in client_ids.split(',')]
                queryset = queryset.filter(id__in=client_ids)
            except (ValueError, TypeError):
                # Si los IDs son inválidos, retornar queryset vacío
                return User.objects.none()

        return queryset.order_by('first_name', 'last_name')

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class LogoutView(APIView):
    """
    SEGURIDAD: Endpoint de logout que blacklistea el refresh token.

    Esto previene que tokens robados puedan ser usados después del logout.

    POST /api/logout/
    Body: {"refresh": "refresh_token_aqui"}

    Returns:
        200: Logout exitoso, token blacklisteado
        400: Token inválido o ya blacklisteado
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from rest_framework_simplejwt.tokens import RefreshToken

            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {"error": "Se requiere el refresh token"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Blacklistear el token
            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"[SECURITY] User {request.user.username} logged out successfully")

            return Response(
                {"message": "Logout exitoso"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.warning(f"[SECURITY] Logout failed for user {request.user.username}: {str(e)}")
            return Response(
                {"error": "Token inválido o expirado"},
                status=status.HTTP_400_BAD_REQUEST
            )


class TimezoneView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response(pytz.common_timezones)

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            refresh = RefreshToken.for_user(user)

            # MULTI-TENANT: Contar perfiles del usuario
            perfiles_count = user.perfiles.count()

            # Preparar respuesta base
            response_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            # Si el usuario tiene múltiples perfiles, enviar lista de organizaciones
            if perfiles_count > 1:
                organizaciones = []
                for perfil in user.perfiles.select_related('organizacion').all():
                    if perfil.organizacion:  # Solo incluir perfiles con organización
                        organizaciones.append({
                            'id': perfil.organizacion.id,
                            'nombre': perfil.organizacion.nombre,
                            'slug': perfil.organizacion.slug,
                            'perfil_id': perfil.id
                        })

                response_data['organizations'] = organizaciones
                response_data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
                logger.info(f'Usuario {user.username} con {perfiles_count} organizaciones inicia sesión')
            else:
                # Usuario con una sola organización: flujo normal
                try:
                    user_data = UserSerializer(user).data
                except AttributeError:
                    # Si no hay perfil, devolver datos básicos
                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                    }

                response_data['user'] = user_data

            return Response(response_data)
        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if User.objects.filter(username=username).exists():
            return Response({'error': 'El usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)
        if email and User.objects.filter(email=email).exists():
            return Response({'error': 'El email ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', '')
        )
        PerfilUsuario.objects.create(user=user) # Create a default profile

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegisterByOrganizacionView(generics.CreateAPIView):
    """
    Vista para registro de usuarios asociados a una organización específica.
    La organización se identifica mediante su slug en la URL.
    """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        from organizacion.models import Organizacion

        organizacion_slug = kwargs.get('organizacion_slug')

        # Validar que la organización existe
        try:
            organizacion = Organizacion.objects.get(slug=organizacion_slug)
        except Organizacion.DoesNotExist:
            # SECURITY: Log detallado para debugging, mensaje genérico al cliente
            logger.warning(
                f"[SEGURIDAD] Intento de registro con slug inválido: {organizacion_slug}"
            )
            return Response({
                'error': 'El enlace de registro no es válido'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validar datos del usuario
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not email:
            return Response({
                'error': 'El campo email es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # MULTI-TENANT: Buscar usuario existente por email
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username or email.split('@')[0],
                'first_name': request.data.get('first_name', ''),
                'last_name': request.data.get('last_name', '')
            }
        )

        if created:
            # Usuario nuevo: validar y establecer contraseña
            if not password:
                return Response({
                    'error': 'La contraseña es requerida para usuarios nuevos'
                }, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.save()
            logger.info(f'Nuevo usuario creado: {user.username} ({user.email}) - Registro directo')
        else:
            # Usuario existente: verificar que no tenga ya un perfil en esta org
            if PerfilUsuario.objects.filter(user=user, organizacion=organizacion).exists():
                # SECURITY: Log detallado para debugging
                logger.info(
                    f"Usuario existente {user.username} intentó re-registrarse en {organizacion.nombre}"
                )
                return Response({
                    'error': 'Ya tienes una cuenta registrada. Por favor inicia sesión.'
                }, status=status.HTTP_400_BAD_REQUEST)
            logger.info(f'Usuario existente {user.username} registrándose en nueva organización: {organizacion.nombre}')

        # Crear perfil asociado a la organización
        perfil = PerfilUsuario.objects.create(
            user=user,
            organizacion=organizacion,
            telefono=request.data.get('telefono', ''),
            ciudad=request.data.get('ciudad', ''),
            barrio=request.data.get('barrio', ''),
            genero=request.data.get('genero', ''),
            fecha_nacimiento=request.data.get('fecha_nacimiento', None),
            has_consented_data_processing=request.data.get('has_consented_data_processing', False)
        )

        # Generar tokens JWT para login automático
        refresh = RefreshToken.for_user(user)

        serializer = UserSerializer(user)

        return Response({
            'message': f'Registro exitoso en {organizacion.nombre}',
            'user': serializer.data,
            'organizacion': {
                'id': organizacion.id,
                'nombre': organizacion.nombre,
                'slug': organizacion.slug
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # MULTI-TENANT: Preload related data for user's profiles (plural)
        user = User.objects.prefetch_related(
            'perfiles__sedes_administradas',
            'perfiles__organizacion',
            'perfiles__sede'
        ).get(pk=user.pk)

        # Devuelve solo datos públicos, nunca información sensible
        # El contexto de organización se maneja en UserSerializer.to_representation()
        data = UserSerializer(user, context={'request': request}).data

        # Elimina campos sensibles si existen
        data.pop('password', None)
        data.pop('last_login', None)
        # NO eliminamos is_superuser - lo necesita el frontend para validaciones
        return Response(data)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=False, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # MULTI-TENANT: Reload user with prefetch to avoid OrganizationManager issues
            user = User.objects.prefetch_related(
                'perfiles__sedes_administradas',
                'perfiles__organizacion',
                'perfiles__sede'
            ).get(pk=user.pk)
            response_data = UserSerializer(user, context={'request': request}).data
            response_data.pop('password', None)
            return Response(response_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # MULTI-TENANT: Reload user with prefetch to avoid OrganizationManager issues
            user = User.objects.prefetch_related(
                'perfiles__sedes_administradas',
                'perfiles__organizacion',
                'perfiles__sede'
            ).get(pk=user.pk)
            response_data = UserSerializer(user, context={'request': request}).data
            response_data.pop('password', None)
            return Response(response_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

class PersonalDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        user_data = UserSerializer(user).data
        # Remove sensitive fields before returning
        user_data.pop('password', None)
        user_data.pop('last_login', None)
        user_data.pop('is_superuser', None)
        
        # You might want to include other related data here, e.g., appointments
        # citas = Cita.objects.filter(user=user)
        # user_data['citas'] = CitaSerializer(citas, many=True).data

        return Response(user_data)

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.is_active = False  # Soft delete: deactivate the user
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestión de clientes con aislamiento multi-tenant.

    Regla principal: Un usuario autenticado (no superusuario) solo puede ver
    clientes de su propia organización.

    Roles soportados:
    - Superusuario: ve todos los clientes
    - Administrador de Sede: ve clientes de su organización
    - Colaborador: ve clientes de su organización/sede
    - Cliente regular: no ve otros clientes
    """
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna queryset de clientes con filtrado multi-tenant.
        Optimizado para usar ORM de Django en lugar de SQL directo.

        IMPORTANTE: Solo muestra usuarios con rol 'cliente'.
        Excluye: owner, admin, sede_admin, colaborador
        """
        user = self.request.user

        # Base queryset: SOLO usuarios con rol 'cliente' en su perfil
        # MULTI-TENANT: prefetch_related para relación 1:N (perfiles plural)
        base_queryset = User.objects.filter(
            perfiles__role='cliente'  # Filtrar solo clientes por el nuevo sistema de roles
        ).exclude(
            Q(email__isnull=True) | Q(email__exact='')
        ).prefetch_related('perfiles__organizacion', 'perfiles__sede').distinct()

        # Filtrar por consentimiento si se especifica
        # LÓGICA: Un usuario tiene consentimiento si:
        # 1. has_consented_data_processing=True (aceptó checkbox al registrarse), O
        # 2. data_processing_opt_out=False (NO se opone al procesamiento)
        # Un usuario NO tiene consentimiento si:
        # 1. data_processing_opt_out=True (se opone al procesamiento), Y
        # 2. has_consented_data_processing=False (nunca aceptó)
        consent_filter = self.request.query_params.get('consent')
        if consent_filter is not None and consent_filter != 'all':
            if consent_filter.lower() == 'true':
                # Con consentimiento: ha aceptado O NO se opone
                base_queryset = base_queryset.filter(
                    Q(perfiles__has_consented_data_processing=True) |
                    Q(perfiles__data_processing_opt_out=False)
                )
            else:
                # Sin consentimiento: se opone Y nunca aceptó
                base_queryset = base_queryset.filter(
                    perfiles__data_processing_opt_out=True,
                    perfiles__has_consented_data_processing=False
                )

        # SUPERUSUARIO: acceso completo
        if user.is_superuser:
            return base_queryset

        # MULTI-TENANT: Obtener perfil del usuario usando helper
        perfil = get_perfil_or_first(user)
        if not perfil or not perfil.organizacion:
            return User.objects.none()

        user_org = perfil.organizacion

        # REGLA PRINCIPAL: Filtrar por organización
        # Esto cubre tanto administradores de sede como colaboradores
        queryset = base_queryset.filter(perfiles__organizacion=user_org)

        # COLABORADOR: filtrado adicional por sede si es necesario
        # Verificar si es colaborador usando ORM en lugar de SQL directo
        from citas.models import Colaborador

        try:
            colaborador = Colaborador.all_objects.select_related('sede__organizacion').get(usuario=user)
            # Si es colaborador, también permitir clientes de su sede específica
            # que puedan no tener organización pero sí sede
            queryset = base_queryset.filter(
                Q(perfiles__organizacion=user_org) | Q(perfiles__sede=colaborador.sede)
            )
        except Colaborador.DoesNotExist:
            # No es colaborador, usar filtrado por organización únicamente
            pass

        return queryset

    def perform_create(self, serializer):
        """Crear cliente asegurando aislamiento de organización."""
        serializer.save()

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Retorna el historial de citas de un cliente con validación de organización.

        SEGURIDAD: Verifica que el usuario solicitante y el cliente pertenezcan
        a la misma organización (excepto superusuarios).
        """
        from django.db.models import Prefetch
        from citas.models import Servicio, Colaborador
        from rest_framework.exceptions import PermissionDenied

        client = self.get_object()
        user = request.user

        # VALIDACIÓN DE SEGURIDAD MULTI-TENANT
        # Superusuarios tienen acceso completo
        if not user.is_superuser:
            # MULTI-TENANT: Verificar que ambos usuarios tienen perfil usando helpers
            user_perfil = get_perfil_or_first(user)
            if not user_perfil:
                raise PermissionDenied("Tu cuenta no tiene un perfil asignado.")

            client_perfil = get_perfil_or_first(client)
            if not client_perfil:
                raise PermissionDenied("El cliente solicitado no tiene un perfil asignado.")

            # Verificar que pertenecen a la misma organización
            user_org = user_perfil.organizacion
            client_org = client_perfil.organizacion

            if not user_org:
                raise PermissionDenied("Tu cuenta no está asociada a ninguna organización.")

            if user_org != client_org:
                raise PermissionDenied(
                    "No tienes permiso para ver el historial de este cliente. "
                    "Solo puedes acceder a clientes de tu organización."
                )

        # CRITICAL FIX: Use Prefetch with _base_manager to bypass OrganizacionManager
        # This ensures servicios and colaboradores are fetched correctly
        servicios_prefetch = Prefetch('servicios', queryset=Servicio._base_manager.all())
        colaboradores_prefetch = Prefetch('colaboradores', queryset=Colaborador._base_manager.all())

        # Usar all_objects para evitar filtrado por OrganizacionManager
        citas = Cita.all_objects.filter(
            Q(user=client) | Q(nombre=client.username)
        ).select_related(
            'user__perfil',
            'sede'
        ).prefetch_related(
            servicios_prefetch,
            colaboradores_prefetch,
            'user__groups',
            'user__perfil__sedes_administradas'
        ).distinct().order_by('-fecha')

        # Calcular estadísticas generales
        stats = citas.aggregate(
            total=Count('id'),
            asistidas=Count('id', filter=Q(estado='Asistio')),
            canceladas=Count('id', filter=Q(estado='Cancelada')),
            no_asistidas=Count('id', filter=Q(estado='No Asistio'))
        )

        # Calcular el Lifetime Value (LTV) del cliente
        # LTV = suma de precios de todos los servicios en citas con estado 'Asistio'
        ltv_result = citas.filter(
            estado='Asistio'
        ).aggregate(
            ltv=Sum('servicios__precio')
        )

        # Asegurar que LTV sea 0 si no hay citas asistidas o si el resultado es None
        stats['ltv'] = ltv_result['ltv'] or 0

        servicios_usados = citas.values('servicios__nombre').annotate(count=Count('servicios__id')).order_by('-count')

        # Incluir datos del cliente en la respuesta para evitar llamada adicional en el frontend
        return Response({
            'client': ClientSerializer(client).data,
            'citas': CitaSerializer(citas, many=True).data,
            'stats': stats,
            'servicios_mas_usados': list(servicios_usados)
        })


# Vistas para registro multi-tenant
class MultiTenantRegistrationView(APIView):
    """Vista para registro de usuario con organización."""
    permission_classes = [IsSuperAdmin]
    
    def post(self, request, *args, **kwargs):
        serializer = MultiTenantRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = serializer.save()
                user = result['user']
                
                # Generar tokens JWT
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'message': 'Usuario y organización creados exitosamente',
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'user': UserSerializer(user).data,
                    'organizacion': OrganizacionSerializer(result['organizacion']).data,
                    'sede': SedeDetailSerializer(result['sede']).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': f'Error al crear la cuenta: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationManagementView(APIView):
    """Vista para gestión de la organización del usuario."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Obtener información de la organización del usuario."""
        # SUPERUSUARIO: Puede ver todas las organizaciones
        if request.user.is_superuser:
            from organizacion.models import Organizacion
            organizaciones = Organizacion.objects.all()

            if not organizaciones.exists():
                return Response({
                    'error': 'No hay organizaciones creadas en el sistema'
                }, status=status.HTTP_404_NOT_FOUND)

            # Retornar todas las organizaciones y sedes
            all_sedes = []
            org_data = []
            for org in organizaciones:
                org_data.append(OrganizacionSerializer(org).data)
                all_sedes.extend(org.sedes.all())

            return Response({
                'organizacion': org_data[0] if org_data else None,  # Primera org por compatibilidad
                'organizaciones': org_data,  # Todas las organizaciones
                'sedes': SedeDetailSerializer(all_sedes, many=True).data,
                'user_role': 'superuser',
                'is_superuser': True
            })

        # USUARIO NORMAL: Usar perfil de organización
        try:
            # MULTI-TENANT: Usar helper para obtener perfil
            perfil = get_user_perfil_for_current_org(request.user)
            organizacion = perfil.organizacion

            if not organizacion:
                return Response({
                    'error': 'Usuario no pertenece a ninguna organización'
                }, status=status.HTTP_404_NOT_FOUND)

            # Obtener sedes de la organización
            sedes = organizacion.sedes.all()

            return Response({
                'organizacion': OrganizacionSerializer(organizacion).data,
                'sedes': SedeDetailSerializer(sedes, many=True).data,
                'user_role': self._get_user_role(request.user)
            })
        except PermissionDenied as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    def _get_user_role(self, user):
        """Determinar el rol del usuario en la organización."""
        if user.is_staff:
            return 'super_admin'

        # MULTI-TENANT: Usar helper con fallback seguro
        perfil = get_perfil_or_first(user)
        if perfil and perfil.sedes_administradas.exists():
            return 'sede_admin'
        return 'member'


class InvitationView(APIView):
    """
    Vista para crear y enviar invitaciones a la organización.
    Crea el objeto Invitation, genera token único y envía email.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Crear y enviar invitación a un usuario."""
        try:
            # SUPERUSUARIO: Puede invitar a cualquier organización
            if request.user.is_superuser:
                from organizacion.models import Organizacion

                # El superusuario debe especificar la organización
                org_id = request.data.get('organization_id')
                if not org_id:
                    return Response({
                        'error': 'Los superusuarios deben especificar organization_id al enviar invitaciones'
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    organizacion = Organizacion.objects.get(id=org_id)
                except Organizacion.DoesNotExist:
                    # SECURITY: Log para debugging, mensaje genérico al cliente
                    logger.warning(
                        f"[SEGURIDAD] Superusuario {request.user.username} intentó invitar a org_id={org_id} inexistente"
                    )
                    return Response({
                        'error': 'No se pudo procesar la invitación'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # USUARIO NORMAL: Usar helper para obtener perfil
                perfil = get_user_perfil_for_current_org(request.user)
                organizacion = perfil.organizacion

                if not organizacion:
                    return Response({
                        'error': 'Usuario no pertenece a ninguna organización'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Verificar que el usuario puede invitar (es admin o sede admin)
                if not (request.user.is_staff or perfil.sedes_administradas.exists()):
                    return Response({
                        'error': 'No tienes permisos para enviar invitaciones'
                    }, status=status.HTTP_403_FORBIDDEN)

            serializer = InvitationSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                role = serializer.validated_data['role']
                first_name = serializer.validated_data.get('first_name', '')
                last_name = serializer.validated_data.get('last_name', '')
                sede_id = serializer.validated_data.get('sede_id')

                # Validar que la sede pertenece a la organización
                sede = None
                if sede_id:
                    try:
                        sede = Sede.objects.get(id=sede_id, organizacion=organizacion)
                    except Sede.DoesNotExist:
                        return Response({
                            'error': 'La sede especificada no pertenece a tu organización'
                        }, status=status.HTTP_400_BAD_REQUEST)

                # Verificar si ya existe una invitación pendiente para este email
                existing_invitation = Invitation.objects.filter(
                    email=email,
                    organization=organizacion,
                    is_accepted=False,
                    expires_at__gt=timezone.now()
                ).first()

                if existing_invitation:
                    return Response({
                        'error': f'Ya existe una invitación pendiente para {email}. Por favor, espera a que expire o sea aceptada.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Crear la invitación
                invitation = Invitation.objects.create(
                    email=email,
                    organization=organizacion,
                    sender=request.user,
                    sede=sede,
                    role=role,
                    first_name=first_name,
                    last_name=last_name
                )

                # Construir URL de aceptación
                frontend_url = settings.FRONTEND_URL
                accept_url = f"{frontend_url}/accept-invitation/{invitation.token}"

                # Preparar contexto para el email
                role_display_map = {
                    'admin': 'Administrador',
                    'sede_admin': 'Administrador de Sede',
                    'colaborador': 'Colaborador',
                    'miembro': 'Miembro'
                }

                context = {
                    'organization_name': organizacion.nombre,
                    'role_display': role_display_map.get(role, role),
                    'sede_name': sede.nombre if sede else None,
                    'sender_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                    'sender_email': request.user.email,
                    'first_name': first_name,
                    'accept_url': accept_url,
                    'expiration_date': invitation.expires_at.strftime('%d de %B de %Y a las %H:%M'),
                    'current_year': timezone.now().year
                }

                # Enviar email de forma asíncrona usando Celery
                try:
                    from .tasks import send_invitation_email_task

                    # Ejecutar tarea asíncrona (no bloqueante)
                    send_invitation_email_task.delay(
                        invitation_id=invitation.id,
                        email=email,
                        context=context
                    )

                    logger.info(f'Tarea de envío de invitación encolada para {email} por {request.user.username}')

                    return Response({
                        'message': 'Invitación creada y el correo será enviado en breve',
                        'invitation': {
                            'id': invitation.id,
                            'email': invitation.email,
                            'role': invitation.role,
                            'sede': sede.nombre if sede else None,
                            'expires_at': invitation.expires_at.isoformat(),
                            'token': str(invitation.token)
                        }
                    }, status=status.HTTP_201_CREATED)

                except Exception as email_error:
                    # Si falla encolar la tarea, eliminar la invitación
                    invitation.delete()
                    logger.error(f'Error al encolar tarea de invitación: {str(email_error)}')
                    return Response({
                        'error': f'Error al enviar el correo de invitación: {str(email_error)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except PermissionDenied as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f'Error inesperado en InvitationView: {str(e)}')
            return Response({
                'error': f'Error inesperado: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcceptInvitationView(APIView):
    """
    Vista para aceptar invitaciones y registrar nuevos usuarios.
    Permite a usuarios invitados crear su cuenta y unirse a la organización.
    """
    permission_classes = [AllowAny]

    def get(self, request, token, *args, **kwargs):
        """Obtener detalles de la invitación por token."""
        try:
            invitation = Invitation.objects.select_related(
                'organization', 'sender', 'sede'
            ).get(token=token)

            if not invitation.is_valid():
                return Response({
                    'error': 'Esta invitación ha expirado o ya ha sido aceptada',
                    'is_valid': False
                }, status=status.HTTP_400_BAD_REQUEST)

            role_display_map = {
                'admin': 'Administrador',
                'sede_admin': 'Administrador de Sede',
                'colaborador': 'Colaborador',
                'miembro': 'Miembro'
            }

            return Response({
                'is_valid': True,
                'invitation': {
                    'email': invitation.email,
                    'organization_name': invitation.organization.nombre,
                    'role': invitation.role,
                    'role_display': role_display_map.get(invitation.role, invitation.role),
                    'sede_name': invitation.sede.nombre if invitation.sede else None,
                    'sender_name': f"{invitation.sender.first_name} {invitation.sender.last_name}".strip() or invitation.sender.username,
                    'first_name': invitation.first_name,
                    'last_name': invitation.last_name,
                    'expires_at': invitation.expires_at.isoformat()
                }
            }, status=status.HTTP_200_OK)

        except Invitation.DoesNotExist:
            return Response({
                'error': 'Invitación no encontrada',
                'is_valid': False
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, token, *args, **kwargs):
        """Aceptar invitación y crear cuenta de usuario."""
        try:
            invitation = Invitation.objects.select_related(
                'organization', 'sender', 'sede'
            ).get(token=token)

            if not invitation.is_valid():
                return Response({
                    'error': 'Esta invitación ha expirado o ya ha sido aceptada'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar datos de registro
            username = request.data.get('username')
            password = request.data.get('password')
            first_name = request.data.get('first_name', invitation.first_name)
            last_name = request.data.get('last_name', invitation.last_name)

            # MULTI-TENANT: Buscar usuario existente por email
            user, created = User.objects.get_or_create(
                email=invitation.email,
                defaults={
                    'username': username or invitation.email.split('@')[0],
                    'first_name': first_name,
                    'last_name': last_name
                }
            )

            if created:
                # Usuario nuevo: validar y establecer contraseña
                if not password:
                    return Response({
                        'error': 'La contraseña es requerida para usuarios nuevos'
                    }, status=status.HTTP_400_BAD_REQUEST)

                user.set_password(password)
                user.save()
                logger.info(f'Nuevo usuario creado: {user.username} ({user.email})')
            else:
                # Usuario existente: solo verificar que no haya perfil en esta org
                if PerfilUsuario.objects.filter(user=user, organizacion=invitation.organization).exists():
                    return Response({
                        'error': 'Ya tienes acceso a esta organización'
                    }, status=status.HTTP_400_BAD_REQUEST)
                logger.info(f'Usuario existente {user.username} agregado a nueva organización')

            # Crear perfil en la nueva organización (o primera)
            perfil = PerfilUsuario.objects.create(
                user=user,
                organizacion=invitation.organization,
                sede=invitation.sede
            )

            # Asignar rol
            if invitation.role == 'admin':
                user.is_staff = True
                user.save()
            elif invitation.role == 'sede_admin':
                try:
                    sede_admin_group, _ = Group.objects.get_or_create(name='SedeAdmin')
                    user.groups.add(sede_admin_group)
                    if invitation.sede:
                        perfil.sedes_administradas.add(invitation.sede)
                except Exception as e:
                    logger.error(f'Error al asignar grupo SedeAdmin: {str(e)}')
            elif invitation.role == 'colaborador':
                try:
                    colaborador_group, _ = Group.objects.get_or_create(name='Recurso')
                    user.groups.add(colaborador_group)
                    # Crear el colaborador en citas.models
                    from citas.models import Colaborador
                    if invitation.sede:
                        Colaborador.objects.create(
                            usuario=user,
                            nombre=f"{first_name} {last_name}".strip(),
                            email=invitation.email,
                            sede=invitation.sede
                        )
                except Exception as e:
                    logger.error(f'Error al crear colaborador: {str(e)}')

            # Marcar invitación como aceptada
            invitation.accept()

            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)

            logger.info(f'Usuario {user.username} registrado exitosamente mediante invitación')

            return Response({
                'message': f'Cuenta creada exitosamente. Bienvenido/a a {invitation.organization.nombre}',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        except Invitation.DoesNotExist:
            return Response({
                'error': 'Invitación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Error al aceptar invitación: {str(e)}')
            return Response({
                'error': f'Error al procesar la invitación: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrganizationMembersView(APIView):
    """Vista para listar miembros de la organización."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Listar miembros de la organización del usuario."""
        # SUPERUSUARIO: Puede ver todos los miembros de todas las organizaciones
        if request.user.is_superuser:
            from organizacion.models import Organizacion

            # Filtrar por organización si se especifica
            org_id = request.query_params.get('organizacion_id')
            if org_id:
                try:
                    organizacion = Organizacion.objects.get(id=org_id)
                    miembros = User.objects.filter(perfiles__organizacion=organizacion)
                except Organizacion.DoesNotExist:
                    # SECURITY: Log para debugging, mensaje genérico al cliente
                    logger.warning(
                        f"[SEGURIDAD] Superusuario {request.user.username} intentó acceder a org_id={org_id} inexistente"
                    )
                    return Response({
                        'error': 'No se pudo obtener la información solicitada'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Todos los miembros de todas las organizaciones
                miembros = User.objects.filter(perfiles__isnull=False)

            miembros = miembros.prefetch_related(
                'perfiles__sedes_administradas',
                'perfiles__organizacion',
                'perfiles__sede'
            ).distinct()

            return Response({
                'miembros': UserSerializer(miembros, many=True, context={'request': request}).data,
                'total': miembros.count()
            })

        # USUARIO NORMAL: Usar perfil de organización
        try:
            # MULTI-TENANT: Usar helper para obtener perfil
            perfil = get_user_perfil_for_current_org(request.user)
            organizacion = perfil.organizacion

            if not organizacion:
                return Response({
                    'error': 'Usuario no pertenece a ninguna organización'
                }, status=status.HTTP_404_NOT_FOUND)

            # MULTI-TENANT: Obtener todos los usuarios de la organización (filtrar por perfiles plural)
            miembros = User.objects.filter(
                perfiles__organizacion=organizacion
            ).prefetch_related(
                'perfiles__sedes_administradas',
                'perfiles__organizacion',
                'perfiles__sede'
            ).distinct()

            # Filtrar por sede si se especifica
            sede_id = request.query_params.get('sede_id')
            if sede_id:
                try:
                    sede = Sede.objects.get(id=sede_id, organizacion=organizacion)
                    miembros = miembros.filter(perfiles__sede=sede)
                except Sede.DoesNotExist:
                    return Response({
                        'error': 'La sede especificada no pertenece a tu organización'
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'miembros': UserSerializer(miembros, many=True, context={'request': request}).data,
                'total': miembros.count()
            })

        except PermissionDenied as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)


class RequestHistoryLinkView(APIView):
    """
    Vista para solicitar un Magic Link de acceso al historial de citas.
    Permite a cualquier usuario (incluidos invitados) solicitar acceso mediante email.

    SEGURIDAD - Rate Limiting:
    - Máximo 3 requests por hora por email
    - Previene: enumeración de emails, flooding, fuerza bruta
    """
    permission_classes = [AllowAny]

    # SECURITY: Rate limiting para prevenir enumeración y flooding
    throttle_classes = [MagicLinkThrottle]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        if not email:
            return Response({
                'error': 'El campo email es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Por seguridad, siempre devolver la misma respuesta genérica
        # sin revelar si el usuario existe o no
        generic_response = {
            'message': 'Si el email existe en nuestro sistema, se ha enviado un enlace de acceso.'
        }

        try:
            # Buscar TODOS los usuarios con este email (puede haber múltiples en diferentes orgs)
            users = User.objects.filter(email=email)

            if users.exists():
                # Enviar magic link a cada usuario (uno por organización)
                for user in users:
                    # Eliminar tokens antiguos del usuario
                    MagicLinkToken.objects.filter(user=user).delete()

                    # Crear nuevo token
                    magic_token = MagicLinkToken.objects.create(user=user)

                    # Construir el enlace mágico
                    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                    magic_link = f"{frontend_url}/magic-link-auth?token={magic_token.token}"

                    # MULTI-TENANT: Obtener info de la organización del usuario
                    org_name = ""
                    perfil = get_perfil_or_first(user)
                    if perfil and perfil.organizacion:
                        org_name = f" - {perfil.organizacion.nombre}"

                    # Enviar email
                    try:
                        subject = f'Accede a tu historial de citas{org_name}'

                        # Mensaje de texto plano
                        plain_message = f"""
Hola {user.first_name or user.username},

Has solicitado acceso a tu historial de citas{org_name}.

Para acceder, haz clic en el siguiente enlace (válido por 15 minutos):

{magic_link}

Si no solicitaste este acceso, puedes ignorar este correo.

Saludos,
El equipo de {getattr(settings, 'SITE_NAME', 'Citas')}
                        """.strip()

                        send_mail(
                            subject=subject,
                            message=plain_message,
                            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                            recipient_list=[email],
                            fail_silently=False
                        )

                        logger.info(f"Magic link enviado a {email} para usuario {user.username}{org_name}")

                    except Exception as e:
                        logger.error(f"Error al enviar magic link a {email}: {str(e)}")
                        # No revelar el error al usuario por seguridad

        except Exception as e:
            logger.error(f"Error en RequestHistoryLinkView: {str(e)}")
            # Continuar y devolver respuesta genérica

        # Siempre devolver la misma respuesta
        return Response(generic_response, status=status.HTTP_200_OK)


class AccessHistoryWithTokenView(APIView):
    """
    Vista para validar un Magic Link token y generar tokens JWT de acceso.
    El token se consume (se elimina) después de ser usado exitosamente.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        token_value = request.data.get('token')

        if not token_value:
            return Response({
                'error': 'El campo token es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Buscar el token
            magic_token = MagicLinkToken.objects.select_related('user').get(token=token_value)

            # Verificar si el token es válido (no expirado)
            if not magic_token.is_valid():
                # Eliminar token expirado
                magic_token.delete()
                return Response({
                    'error': 'El token ha expirado. Por favor, solicita un nuevo enlace.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Token válido: generar tokens JWT
            user = magic_token.user
            refresh = RefreshToken.for_user(user)

            # Eliminar el token para que solo se pueda usar una vez
            magic_token.delete()

            # Preparar datos del usuario
            try:
                user_data = UserSerializer(user).data
            except Exception as e:
                logger.warning(f"Error al serializar usuario: {str(e)}")
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }

            logger.info(f"Acceso exitoso con magic link para usuario {user.email}")

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_data,
                'message': 'Autenticación exitosa'
            }, status=status.HTTP_200_OK)

        except MagicLinkToken.DoesNotExist:
            return Response({
                'error': 'Token inválido o ya utilizado'
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error en AccessHistoryWithTokenView: {str(e)}")
            return Response({
                'error': 'Error al procesar el token'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== NUEVO SISTEMA DE ROLES ====================

class CreateUserWithRoleView(APIView):
    """
    Endpoint simplificado para crear usuarios con roles.

    POST /api/usuarios/create-user/
    {
        "email": "ana@example.com",
        "first_name": "Ana",
        "last_name": "García",
        "password": "secure123",
        "role": "colaborador",
        "additional_roles": ["cliente"],
        "sede_principal_id": 1,
        "sedes_trabajo_ids": [1, 2],
        "permissions": {"can_view_reports": true}
    }

    Permisos: Solo propietarios y administradores pueden crear usuarios.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .serializers import CreateUserWithRoleSerializer
        from .permissions import IsOwnerOrAdmin

        # Verificar permisos manualmente
        permission = IsOwnerOrAdmin()
        if not permission.has_permission(request, self):
            return Response({
                'error': 'No tienes permisos para crear usuarios. Solo propietarios y administradores.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateUserWithRoleSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            try:
                perfil = serializer.save()

                return Response({
                    'id': perfil.user.id,
                    'email': perfil.user.email,
                    'role': perfil.role,
                    'additional_roles': perfil.additional_roles,
                    'display_badge': perfil.display_badge,
                    'message': f'Usuario creado exitosamente como {perfil.get_role_display()}'
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Error al crear usuario con rol: {str(e)}")
                return Response({
                    'error': f'Error al crear usuario: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserOrganizationsView(APIView):
    """
    Lista todas las organizaciones donde el usuario tiene membresía.

    GET /api/usuarios/my-organizations/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .utils import get_user_organizations

        organizations = get_user_organizations(request.user)
        org_data = []
        
        for org in organizations:
            try:
                perfil = PerfilUsuario.all_objects.get(
                    user=request.user,
                    organizacion=org,
                    is_active=True
                )
                org_data.append({
                    'id': org.id,
                    'nombre': org.nombre,
                    'slug': org.slug,
                    'role': perfil.role,
                    'all_roles': perfil.all_roles,
                    'display_badge': perfil.display_badge,
                })
            except PerfilUsuario.DoesNotExist:
                continue

        return Response({
            'count': len(org_data),
            'organizations': org_data
        }, status=status.HTTP_200_OK)


class SwitchOrganizationView(APIView):
    """
    Cambia la organización activa en la sesión del usuario.

    POST /api/usuarios/switch-organization/
    {"organization_id": 123}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .utils import switch_organization_context

        organization_id = request.data.get('organization_id')
        if not organization_id:
            return Response({
                'error': 'Se requiere organization_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        success = switch_organization_context(request, organization_id)

        if success:
            return Response({
                'message': 'Organización cambiada exitosamente',
                'organization_id': organization_id
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'No tienes acceso a esta organización o no existe'
            }, status=status.HTTP_403_FORBIDDEN)

