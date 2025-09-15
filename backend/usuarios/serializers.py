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
    # Fields from User model
    username = serializers.CharField(required=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=True)

    # Fields from PerfilUsuario model
    telefono = serializers.CharField(source='perfil.telefono', required=False, allow_blank=True)
    ciudad = serializers.CharField(source='perfil.ciudad', required=False, allow_blank=True)
    barrio = serializers.CharField(source='perfil.barrio', required=False, allow_blank=True)
    genero = serializers.CharField(source='perfil.genero', required=False, allow_blank=True) # Use 'genero' directly for writing
    fecha_nacimiento = serializers.DateField(source='perfil.fecha_nacimiento', required=False, allow_null=True)

    # Read-only fields (properties)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    age = serializers.IntegerField(source='perfil.age', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento',
            'full_name', 'age'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        perfil_data = validated_data.pop('perfil', {})
        
        # Create User instance
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            # No password for existing users, or generate a random one if needed
            # For client management, we don't typically set passwords here
        )

        # Create or update PerfilUsuario instance
        PerfilUsuario.objects.update_or_create(
            user=user,
            defaults={
                'telefono': perfil_data.get('telefono'),
                'ciudad': perfil_data.get('ciudad'),
                'barrio': perfil_data.get('barrio'),
                'genero': perfil_data.get('genero'),
                'fecha_nacimiento': perfil_data.get('fecha_nacimiento'),
            }
        )
        return user

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfil', {})

        # Update User instance
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        # Update PerfilUsuario instance
        perfil, created = PerfilUsuario.objects.get_or_create(user=instance)
        perfil.telefono = perfil_data.get('telefono', perfil.telefono)
        perfil.ciudad = perfil_data.get('ciudad', perfil.ciudad)
        perfil.barrio = perfil_data.get('barrio', perfil.barrio)
        perfil.genero = perfil_data.get('genero', perfil.genero)
        perfil.fecha_nacimiento = perfil_data.get('fecha_nacimiento', perfil.fecha_nacimiento)
        perfil.save()

        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializer(self.user).data
        data.update({'user': serializer})
        return data

