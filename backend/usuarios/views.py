from django.contrib.auth import authenticate, login
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, MyTokenObtainPairSerializer, ClientSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
import pytz
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User, Group # Added Group
from citas.permissions import IsAdminOrSedeAdmin

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
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # Preload related data for the user's profile
        user = User.objects.prefetch_related('perfil__sedes_administradas').get(pk=user.pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

class ClientViewSet(viewsets.ModelViewSet): # Changed to ModelViewSet
    """
    A viewset for viewing and managing client data.
    Accessible to admin users and sede administrators.
    """
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrSedeAdmin]

    def get_queryset(self):
        # Get the Group objects for 'SedeAdmin' and 'Recurso'
        sede_admin_group = Group.objects.get(name='SedeAdmin')
        recurso_group = Group.objects.get(name='Recurso')

        # Exclude users who are staff, in SedeAdmin group, or in Recurso group
        return User.objects.filter(is_staff=False)
            .exclude(groups=sede_admin_group)
            .exclude(groups=recurso_group)
            .select_related('perfil')
