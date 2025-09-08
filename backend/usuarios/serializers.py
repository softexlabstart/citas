from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PerfilUsuario
from organizacion.models import Sede

class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ('id', 'nombre')

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    sedes_administradas = SedeSerializer(many=True, read_only=True)
    is_sede_admin = serializers.SerializerMethodField()

    class Meta:
        model = PerfilUsuario
        fields = ('timezone', 'sede', 'sedes_administradas', 'is_sede_admin')

    def get_is_sede_admin(self, obj):
        return obj.sedes_administradas.exists()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    perfil = PerfilUsuarioSerializer(read_only=True) # Nested serializer for PerfilUsuario

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'password', 'perfil') # Include 'perfil'

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

