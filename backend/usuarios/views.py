from django.contrib.auth import authenticate, login
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from organizacion.models import Sede
from .models import PerfilUsuario, MagicLinkToken
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
import logging

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
            
            # Manejar el caso donde el perfil no existe
            try:
                user_data = UserSerializer(user).data
            except AttributeError: # O podría ser PerfilUsuario.DoesNotExist dependiendo del serializer
                # Si no hay perfil, devolvemos los datos básicos del usuario
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data
            })
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
            return Response({
                'error': 'Organización no encontrada. Verifica el enlace de registro.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validar datos del usuario
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not email or not password:
            return Response({
                'error': 'Los campos username, email y password son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({
                'error': 'El nombre de usuario ya existe'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'El email ya está registrado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', '')
        )

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
        # Preload related data for the user's profile
        user = User.objects.prefetch_related('perfil__sedes_administradas', 'perfil__organizacion').get(pk=user.pk)
        # Devuelve solo datos públicos, nunca información sensible
        data = UserSerializer(user).data
        # Elimina campos sensibles si existen
        data.pop('password', None)
        data.pop('last_login', None)
        # NO eliminamos is_superuser - lo necesita el frontend para validaciones
        return Response(data)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            # Reload user with prefetch to avoid OrganizationManager issues
            user = User.objects.prefetch_related('perfil__sedes_administradas', 'perfil__organizacion').get(pk=user.pk)
            response_data = UserSerializer(user).data
            response_data.pop('password', None)
            return Response(response_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Reload user with prefetch to avoid OrganizationManager issues
            user = User.objects.prefetch_related('perfil__sedes_administradas', 'perfil__organizacion').get(pk=user.pk)
            response_data = UserSerializer(user).data
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
        """
        user = self.request.user

        # Base queryset: usuarios que NO son staff, ni admins de sede, ni colaboradores
        # Optimización: usar exclude con lista en lugar de múltiples exclude
        base_queryset = User.objects.filter(
            is_staff=False
        ).exclude(
            Q(email__isnull=True) | Q(email__exact='')
        ).exclude(
            groups__name__in=['SedeAdmin', 'Recurso']
        ).select_related('perfil__organizacion', 'perfil__sede').distinct()

        # Filtrar por consentimiento si se especifica
        consent_filter = self.request.query_params.get('consent')
        if consent_filter == 'true':
            base_queryset = base_queryset.filter(perfil__has_consented_data_processing=True)
        elif consent_filter == 'false':
            base_queryset = base_queryset.filter(perfil__has_consented_data_processing=False)

        # SUPERUSUARIO: acceso completo
        if user.is_superuser:
            return base_queryset

        # Verificar si el usuario tiene perfil
        if not hasattr(user, 'perfil') or not user.perfil:
            return User.objects.none()

        user_org = user.perfil.organizacion

        # Si no tiene organización, no puede ver clientes
        if not user_org:
            return User.objects.none()

        # REGLA PRINCIPAL: Filtrar por organización
        # Esto cubre tanto administradores de sede como colaboradores
        queryset = base_queryset.filter(perfil__organizacion=user_org)

        # COLABORADOR: filtrado adicional por sede si es necesario
        # Verificar si es colaborador usando ORM en lugar de SQL directo
        from citas.models import Colaborador

        try:
            colaborador = Colaborador.all_objects.select_related('sede__organizacion').get(usuario=user)
            # Si es colaborador, también permitir clientes de su sede específica
            # que puedan no tener organización pero sí sede
            queryset = base_queryset.filter(
                Q(perfil__organizacion=user_org) | Q(perfil__sede=colaborador.sede)
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
            # Verificar que ambos usuarios tienen perfil
            if not hasattr(user, 'perfil') or not user.perfil:
                raise PermissionDenied("Tu cuenta no tiene un perfil asignado.")

            if not hasattr(client, 'perfil') or not client.perfil:
                raise PermissionDenied("El cliente solicitado no tiene un perfil asignado.")

            # Verificar que pertenecen a la misma organización
            user_org = user.perfil.organizacion
            client_org = client.perfil.organizacion

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

        return Response({
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
        try:
            perfil = request.user.perfil
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
        except PerfilUsuario.DoesNotExist:
            return Response({
                'error': 'Usuario no tiene perfil configurado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _get_user_role(self, user):
        """Determinar el rol del usuario en la organización."""
        if user.is_staff:
            return 'super_admin'
        
        try:
            perfil = user.perfil
            if perfil.sedes_administradas.exists():
                return 'sede_admin'
            return 'member'
        except PerfilUsuario.DoesNotExist:
            return 'member'


class InvitationView(APIView):
    """Vista para enviar invitaciones a la organización."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Enviar invitación a un usuario."""
        try:
            perfil = request.user.perfil
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
                # Validar que la sede pertenece a la organización
                sede_id = serializer.validated_data.get('sede_id')
                if sede_id:
                    try:
                        sede = Sede.objects.get(id=sede_id, organizacion=organizacion)
                    except Sede.DoesNotExist:
                        return Response({
                            'error': 'La sede especificada no pertenece a tu organización'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Aquí se enviaría el email de invitación
                # Por ahora solo devolvemos éxito
                return Response({
                    'message': 'Invitación enviada exitosamente',
                    'invitation_data': serializer.validated_data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except PerfilUsuario.DoesNotExist:
            return Response({
                'error': 'Usuario no tiene perfil configurado'
            }, status=status.HTTP_404_NOT_FOUND)


class OrganizationMembersView(APIView):
    """Vista para listar miembros de la organización."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Listar miembros de la organización del usuario."""
        try:
            perfil = request.user.perfil
            organizacion = perfil.organizacion
            
            if not organizacion:
                return Response({
                    'error': 'Usuario no pertenece a ninguna organización'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Obtener todos los usuarios de la organización
            miembros = User.objects.filter(
                perfil__organizacion=organizacion
            ).select_related('perfil').prefetch_related('perfil__sedes_administradas')
            
            # Filtrar por sede si se especifica
            sede_id = request.query_params.get('sede_id')
            if sede_id:
                try:
                    sede = Sede.objects.get(id=sede_id, organizacion=organizacion)
                    miembros = miembros.filter(perfil__sede=sede)
                except Sede.DoesNotExist:
                    return Response({
                        'error': 'La sede especificada no pertenece a tu organización'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'miembros': UserSerializer(miembros, many=True).data,
                'total': miembros.count()
            })

        except PerfilUsuario.DoesNotExist:
            return Response({
                'error': 'Usuario no tiene perfil configurado'
            }, status=status.HTTP_404_NOT_FOUND)


class RequestHistoryLinkView(APIView):
    """
    Vista para solicitar un Magic Link de acceso al historial de citas.
    Permite a cualquier usuario (incluidos invitados) solicitar acceso mediante email.
    """
    permission_classes = [AllowAny]

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

                    # Obtener info de la organización del usuario
                    org_name = ""
                    if hasattr(user, 'perfil') and user.perfil and user.perfil.organizacion:
                        org_name = f" - {user.perfil.organizacion.nombre}"

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
