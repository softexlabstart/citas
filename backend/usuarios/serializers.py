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
        fields = ('timezone', 'sede', 'sedes_administradas', 'is_sede_admin', 'telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento', 'has_consented_data_processing', 'data_processing_opt_out') # Added data_processing_opt_out

    def get_is_sede_admin(self, obj):
        user = obj.user
        is_in_admin_group = user.groups.filter(name='SedeAdmin').exists()
        has_sedes_administradas = obj.sedes_administradas.exists()
        return is_in_admin_group or has_sedes_administradas

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False) # Make password optional for updates
    perfil = PerfilUsuarioSerializer() # Removed read_only=True
    groups = serializers.SerializerMethodField(read_only=True) # Make groups read_only

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'password', 'perfil', 'groups')

    def get_groups(self, obj):
        return [group.name for group in obj.groups.all()]

    def create(self, validated_data):
        perfil_data = validated_data.pop('perfil', {})
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        PerfilUsuario.objects.create(user=user, **perfil_data) # Create PerfilUsuario here
        return user

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfil', {})

        # Update User fields
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.save()

        # Update PerfilUsuario fields
        perfil = instance.perfil
        for attr, value in perfil_data.items():
            setattr(perfil, attr, value)
        perfil.save()

        return instance


class ClientSerializer(serializers.ModelSerializer):
    # Perfil fields (now flat)
    telefono = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ciudad = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    barrio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    genero = serializers.ChoiceField(choices=PerfilUsuario.GENERO_CHOICES, required=False, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)

    # Read-only fields
    full_name = serializers.SerializerMethodField(read_only=True)
    age = serializers.IntegerField(source='perfil.age', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento',
            'full_name', 'age'
        )

    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.username

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        perfil = getattr(instance, 'perfil', None)
        if perfil:
            representation['telefono'] = perfil.telefono
            representation['ciudad'] = perfil.ciudad
            representation['barrio'] = perfil.barrio
            representation['genero'] = perfil.genero
            representation['fecha_nacimiento'] = perfil.fecha_nacimiento
        return representation

    def create(self, validated_data):
        perfil_fields = ['telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento']
        perfil_data = {field: validated_data.pop(field) for field in perfil_fields if field in validated_data}
        
        user = User.objects.create_user(**validated_data)
        PerfilUsuario.objects.create(user=user, **perfil_data)
        return user

    def update(self, instance, validated_data):
        perfil, created = PerfilUsuario.objects.get_or_create(user=instance)
        
        # User fields
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        
        # Perfil fields
        perfil.telefono = validated_data.get('telefono', perfil.telefono)
        perfil.ciudad = validated_data.get('ciudad', perfil.ciudad)
        perfil.barrio = validated_data.get('barrio', perfil.barrio)
        perfil.genero = validated_data.get('genero', perfil.genero)
        perfil.fecha_nacimiento = validated_data.get('fecha_nacimiento', perfil.fecha_nacimiento)
        
        perfil.save()
        instance.save()
        return instance


class ClientEmailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email')

    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.username


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializer(self.user).data
        data.update({'user': serializer})
        return data

