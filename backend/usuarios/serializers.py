from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PerfilUsuario
from organizacion.models import Sede
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ('id', 'nombre')

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    sedes_administradas = SedeSerializer(many=True, read_only=True)
    is_sede_admin = serializers.SerializerMethodField()

    class Meta:
        model = PerfilUsuario
        fields = ('timezone', 'sede', 'sedes_administradas', 'is_sede_admin', 'telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento')

    def get_is_sede_admin(self, obj):
        return obj.sedes_administradas.exists()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    perfil = PerfilUsuarioSerializer(read_only=True) # Nested serializer for PerfilUsuario
    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'password', 'perfil', 'groups') # Include 'perfil'

    def get_groups(self, obj):
        return [group.name for group in obj.groups.all()]

    def create(self, validated_data):
        # The 'sede' field was previously handled directly in UserSerializer,
        # but now it's part of PerfilUsuario. We need to adjust this.
        # For user creation, we'll assume 'sede' might come in the initial data
        # and pass it to PerfilUsuario creation.
        # If 'sede' is not directly passed during user creation, PerfilUsuario
        # will be created without a default 'sede', which can be updated later.

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()

        # PerfilUsuario is created via signal, so we don't need to explicitly create it here
        # However, if 'sede' was part of the initial user creation request,
        # we need to ensure it's set on the PerfilUsuario.
        # This part of the logic might need adjustment depending on how user registration
        # is expected to handle the 'sede' field for PerfilUsuario.
        # For now, assuming PerfilUsuario is created by signal and can be updated later.
        return user


class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name')
    email = serializers.CharField(source='email')
    telefono = serializers.CharField(source='perfil.telefono')
    ciudad = serializers.CharField(source='perfil.ciudad')
    barrio = serializers.CharField(source='perfil.barrio')
    genero = serializers.CharField(source='perfil.get_genero_display')
    age = serializers.IntegerField(source='perfil.age')

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'telefono', 'ciudad', 'barrio', 'genero', 'age')


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializer(self.user).data
        data.update({'user': serializer})
        return data

