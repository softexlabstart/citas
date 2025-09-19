from django.contrib.auth import authenticate, login
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, MyTokenObtainPairSerializer, ClientSerializer, ClientEmailSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
import pytz
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User, Group # Added Group
from citas.permissions import IsAdminOrSedeAdmin
from rest_framework.decorators import action
from django.db.models import Count, Q
from citas.models import Cita
from citas.serializers import CitaSerializer

class ClientEmailListView(generics.ListAPIView):
    serializer_class = ClientEmailSerializer
    permission_classes = [IsAdminOrSedeAdmin]

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True, is_staff=False).exclude(groups__name='SedeAdmin').exclude(groups__name='Recurso')
        client_ids = self.request.query_params.get('ids', None)
        if client_ids:
            client_ids = [int(id) for id in client_ids.split(',')]
            queryset = queryset.filter(id__in=client_ids)
        return queryset.order_by('first_name', 'last_name')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Si se pasa ?all=true, devolver todos los clientes
        if request.query_params.get('all', '').lower() == 'true':
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        # Si se pasan ids, devolver solo esos
        client_ids = request.query_params.get('ids', None)
        if client_ids:
            client_ids = [int(id) for id in client_ids.split(',')]
            queryset = queryset.filter(id__in=client_ids)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
        # No revelar si el usuario existe o no
        if user:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        # Mensaje genérico para credenciales inválidas
        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'El usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)
        if email and User.objects.filter(email=email).exists():
            return Response({'error': 'El email ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # Preload related data for the user's profile
        user = User.objects.prefetch_related('perfil__sedes_administradas').get(pk=user.pk)
        # Devuelve solo datos públicos, nunca información sensible
        data = UserSerializer(user).data
        # Elimina campos sensibles si existen
        data.pop('password', None)
        data.pop('last_login', None)
        data.pop('is_superuser', None)
        return Response(data)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
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
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ClientViewSet(viewsets.ModelViewSet): # Changed to ModelViewSet
    """
    A viewset for viewing and managing client data.
    Accessible to admin users and sede administrators.
    """
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrSedeAdmin]

    def get_queryset(self):
        sede_admin_group = Group.objects.get(name='SedeAdmin')
        recurso_group = Group.objects.get(name='Recurso')
        return User.objects.filter(is_staff=False)\
            .exclude(groups=sede_admin_group)\
            .exclude(groups=recurso_group)\
            .exclude(email__isnull=True)\
            .exclude(email__exact='')\
            .select_related('perfil')

    # Agregar paginación para evitar exponer grandes cantidades de datos
    page_size = 25
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        client = self.get_object()
        citas = Cita.objects.filter(Q(user=client) | Q(nombre=client.username)).distinct().order_by('-fecha')
        
        stats = citas.aggregate(
            total=Count('id'),
            asistidas=Count('id', filter=Q(estado='Asistio')),
            canceladas=Count('id', filter=Q(estado='Cancelada')),
            no_asistidas=Count('id', filter=Q(estado='No Asistio'))
        )
        
        servicios_usados = citas.values('servicio__nombre').annotate(count=Count('servicio')).order_by('-count')
        
        return Response({
            'citas': CitaSerializer(citas, many=True).data,
            'stats': stats,
            'servicios_mas_usados': list(servicios_usados)
        })