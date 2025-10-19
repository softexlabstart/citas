import logging
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PerfilUsuario
from organizacion.models import Sede, Organizacion
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# MULTI-TENANT: Import helpers for profile management
from .utils import get_perfil_or_first


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ('id', 'nombre')

class OrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizacion
        fields = ('id', 'nombre', 'slug')

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    sedes = serializers.SerializerMethodField()
    sedes_administradas = SedeSerializer(many=True, read_only=True)
    organizacion = OrganizacionSerializer(read_only=True)
    is_sede_admin = serializers.SerializerMethodField()

    class Meta:
        model = PerfilUsuario
        fields = ('timezone', 'sede', 'sedes', 'organizacion', 'sedes_administradas', 'is_sede_admin', 'telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento', 'has_consented_data_processing', 'data_processing_opt_out')

    def get_sedes(self, obj):
        """Get all sedes using direct query to bypass organization filtering."""
        if not obj:
            return []
        # Query the through table directly to bypass OrganizacionManager
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.id, s.nombre
                FROM organizacion_sede s
                INNER JOIN usuarios_perfilusuario_sedes ups ON s.id = ups.sede_id
                WHERE ups.perfilusuario_id = %s
            """, [obj.id])
            rows = cursor.fetchall()
            return [{'id': row[0], 'nombre': row[1]} for row in rows]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'sede' in self.fields:
            self.fields['sede'].queryset = Sede.all_objects.all()

    def get_is_sede_admin(self, obj):
        # Si el perfil no existe (obj es None), el usuario no puede ser admin de sede.
        if not obj:
            return False
            
        user = obj.user
        is_in_admin_group = user.groups.filter(name='SedeAdmin').exists()
        has_sedes_administradas = obj.sedes_administradas.exists()
        return is_in_admin_group or has_sedes_administradas

class PerfilUsuarioRegistrationSerializer(serializers.ModelSerializer):
    """Serializer simplificado para registro de usuarios."""
    
    class Meta:
        model = PerfilUsuario
        fields = ('timezone', 'telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento', 'has_consented_data_processing')
        extra_kwargs = {
            'timezone': {'required': False, 'default': 'America/Bogota'},
            'telefono': {'required': False, 'allow_blank': True, 'allow_null': True},
            'ciudad': {'required': False, 'allow_blank': True, 'allow_null': True},
            'barrio': {'required': False, 'allow_blank': True, 'allow_null': True},
            'genero': {'required': False, 'allow_null': True},
            'fecha_nacimiento': {'required': False, 'allow_null': True},
            'has_consented_data_processing': {'required': False, 'default': False},
        }

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False) # Make password optional for updates
    perfil = serializers.DictField(required=False, allow_null=True, write_only=True)  # Accept any dict for input
    groups = serializers.SerializerMethodField(read_only=True) # Make groups read_only

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'password', 'perfil', 'groups')

    def get_groups(self, obj):
        return [group.name for group in obj.groups.all()]

    def to_representation(self, instance):
        """Override to use read-only serializer for output."""
        representation = super().to_representation(instance)

        # MULTI-TENANT: Obtener perfil usando helper con contexto de request
        request = self.context.get('request')
        if request:
            perfil = get_perfil_or_first(instance)
        else:
            # Sin request context, usar primer perfil
            perfil = instance.perfiles.select_related('organizacion', 'sede').first()

        if perfil:
            representation['perfil'] = PerfilUsuarioSerializer(perfil).data
        else:
            representation['perfil'] = None

        return representation

    def create(self, validated_data):
        # This serializer should not be used for creation directly anymore.
        # The RegisterView uses its own logic or a dedicated registration serializer.
        raise NotImplementedError("Use a dedicated registration serializer instead.")

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

        # MULTI-TENANT: Obtener o crear perfil con contexto
        from organizacion.thread_locals import get_current_organization

        perfil = get_perfil_or_first(instance)

        if not perfil:
            # Crear nuevo perfil para la organización actual
            org = get_current_organization()
            perfil = PerfilUsuario.objects.create(user=instance, organizacion=org)

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
    has_consented_data_processing = serializers.BooleanField(source='perfil.has_consented_data_processing', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'telefono', 'ciudad', 'barrio', 'genero', 'fecha_nacimiento',
            'full_name', 'age', 'has_consented_data_processing'
        )

    def validate_fecha_nacimiento(self, value):
        """Validar que la fecha de nacimiento no sea futura."""
        if value:
            from datetime import date
            if value > date.today():
                raise serializers.ValidationError("La fecha de nacimiento no puede ser una fecha futura.")
        return value

    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.username

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # MULTI-TENANT: Obtener perfil usando helper
        perfil = get_perfil_or_first(instance)

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

        # MULTI-TENANT: Obtener organización del request user
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_perfil = get_perfil_or_first(request.user)
            if user_perfil and user_perfil.organizacion:
                perfil_data['organizacion'] = user_perfil.organizacion

        user = User.objects.create_user(**validated_data)
        PerfilUsuario.objects.create(user=user, **perfil_data)
        return user

    def update(self, instance, validated_data):
        logging.error(f"--- ClientSerializer.update CALLED for user: {instance.username} ---")
        logging.error(f"Validated data: {validated_data}")

        # Update User fields first
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        logging.error("--- Calling instance.save() [User] ---")
        instance.save()
        logging.error("--- instance.save() [User] finished ---")

        # MULTI-TENANT: Obtener o crear perfil con contexto
        from organizacion.thread_locals import get_current_organization

        perfil = get_perfil_or_first(instance)
        logging.error(f"--- Found existing profile (ID: {perfil.id}) for user {instance.username} ---" if perfil else "--- No profile found ---")

        if not perfil:
            logging.error(f"--- No profile found for user {instance.username}, creating a new one. ---")
            org = get_current_organization()
            perfil = PerfilUsuario.objects.create(user=instance, organizacion=org)

        # Update Perfil fields
        perfil.telefono = validated_data.get('telefono', perfil.telefono)
        perfil.ciudad = validated_data.get('ciudad', perfil.ciudad)
        perfil.barrio = validated_data.get('barrio', perfil.barrio)
        perfil.genero = validated_data.get('genero', perfil.genero)
        perfil.fecha_nacimiento = validated_data.get('fecha_nacimiento', perfil.fecha_nacimiento)
        
        logging.error(f"--- Calling perfil.save() for profile {perfil.id} ---")
        perfil.save()
        logging.error("--- perfil.save() finished ---")

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
        # Usar un bloque try-except para manejar usuarios sin perfil
        try:
            user_data = UserSerializer(self.user).data
        except ObjectDoesNotExist:
            # Si no hay perfil, serializa solo los datos básicos del usuario
            user_data = {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'groups': [group.name for group in self.user.groups.all()]
            }
        data.update({'user': user_data})
        return data


# Serializers para registro multi-tenant
class OrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizacion
        fields = ['id', 'nombre']

class SedeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ['id', 'nombre', 'direccion', 'telefono']

class MultiTenantRegistrationSerializer(serializers.Serializer):
    """Serializer para registro de usuario con organización."""
    # Datos del usuario
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, min_length=8)
    
    # Datos de la organización
    organizacion_nombre = serializers.CharField(max_length=100)
    
    # Datos de la sede principal
    sede_nombre = serializers.CharField(max_length=100)
    sede_direccion = serializers.CharField(max_length=255, required=False, allow_blank=True)
    sede_telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Datos del perfil
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    ciudad = serializers.CharField(max_length=100, required=False, allow_blank=True)
    barrio = serializers.CharField(max_length=100, required=False, allow_blank=True)
    genero = serializers.ChoiceField(choices=PerfilUsuario.GENERO_CHOICES, required=False, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    timezone = serializers.CharField(max_length=100, default='America/Bogota')
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value
    
    def validate_organizacion_nombre(self, value):
        if Organizacion.objects.filter(nombre=value).exists():
            raise serializers.ValidationError("Ya existe una organización con este nombre.")
        return value
    
    def create(self, validated_data):
        # Crear organización
        organizacion = Organizacion.objects.create(
            nombre=validated_data['organizacion_nombre']
        )
        
        # Crear sede principal
        sede = Sede.objects.create(
            nombre=validated_data['sede_nombre'],
            direccion=validated_data.get('sede_direccion', ''),
            telefono=validated_data.get('sede_telefono', ''),
            organizacion=organizacion
        )
        
        # Crear usuario
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        
        # Crear perfil de usuario
        perfil = PerfilUsuario.objects.create(
            user=user,
            organizacion=organizacion,
            sede=sede,
            telefono=validated_data.get('telefono', ''),
            ciudad=validated_data.get('ciudad', ''),
            barrio=validated_data.get('barrio', ''),
            genero=validated_data.get('genero'),
            fecha_nacimiento=validated_data.get('fecha_nacimiento'),
            timezone=validated_data.get('timezone', 'America/Bogota')
        )
        
        # Asignar al usuario como administrador de la sede
        # Usar all_objects para evitar filtrado por organización
        perfil.sedes_administradas.add(sede)
        
        return {
            'user': user,
            'organizacion': organizacion,
            'sede': sede,
            'perfil': perfil
        }

class InvitationSerializer(serializers.Serializer):
    """Serializer para invitaciones de usuarios a la organización."""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    role = serializers.ChoiceField(choices=[
        ('admin', 'Administrador'),
        ('sede_admin', 'Administrador de Sede'),
        ('colaborador', 'Colaborador')
    ])
    sede_id = serializers.IntegerField(required=False, allow_null=True)
    message = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value
    
    def validate_sede_id(self, value):
        if value is not None:
            try:
                # Usar all_objects para evitar filtrado por organización
                sede = Sede.all_objects.get(id=value)
                return value
            except Sede.DoesNotExist:
                raise serializers.ValidationError("La sede especificada no existe.")
        return value


class OnboardingProgressSerializer(serializers.ModelSerializer):
    """
    Serializer para el progreso del onboarding del usuario.
    """
    completion_percentage = serializers.ReadOnlyField()
    pending_steps = serializers.ReadOnlyField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        from .models import OnboardingProgress
        model = OnboardingProgress
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'has_created_service',
            'has_added_collaborator',
            'has_viewed_public_link',
            'has_completed_profile',
            'is_completed',
            'is_dismissed',
            'completion_percentage',
            'pending_steps',
            'created_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'completed_at']


# ==================== SERIALIZERS PARA SISTEMA DE ROLES ====================

class CreateUserWithRoleSerializer(serializers.Serializer):
    """
    Serializer para crear usuarios con roles en el sistema multi-tenant.

    Simplifica la creación de usuarios permitiendo especificar:
    - Datos básicos del usuario
    - Rol principal y roles adicionales
    - Sedes según el rol
    - Permisos personalizados (opcional)
    """

    # Datos básicos del usuario
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    # Sistema de roles
    role = serializers.ChoiceField(
        choices=PerfilUsuario.ROLE_CHOICES,
        required=True,
        help_text='Rol principal del usuario'
    )
    additional_roles = serializers.ListField(
        child=serializers.ChoiceField(choices=PerfilUsuario.ROLE_CHOICES),
        required=False,
        default=list,
        help_text='Roles adicionales (opcional). Ej: ["cliente"] si un colaborador también es cliente'
    )

    # Sedes según rol
    sede_principal_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='ID de la sede principal (requerido para colaboradores y admins de sede)'
    )
    sedes_trabajo_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text='IDs de sedes donde trabaja (para colaboradores multi-sede)'
    )
    sedes_administradas_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text='IDs de sedes que administra (para admins de sede)'
    )

    # Permisos personalizados
    permissions = serializers.JSONField(
        required=False,
        default=dict,
        help_text='Permisos granulares en JSON. Ej: {"can_view_reports": true}'
    )

    # Datos opcionales
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=100, required=False, default='UTC')

    def validate_email(self, value):
        """Verifica que el email no esté en uso en esta organización"""
        from organizacion.thread_locals import get_current_organization
        org = get_current_organization()

        if org:
            # Verificar si ya existe un usuario con este email en esta org
            existing_perfil = PerfilUsuario.all_objects.filter(
                user__email=value,
                organizacion=org
            ).first()

            if existing_perfil:
                raise serializers.ValidationError(
                    f"Ya existe un usuario con este email en la organización {org.nombre}"
                )

        return value.lower()

    def validate(self, data):
        """Validaciones cruzadas"""
        role = data.get('role')
        additional_roles = data.get('additional_roles', [])

        # Validar que sede_principal es requerida para ciertos roles
        if role in ['colaborador', 'sede_admin'] and not data.get('sede_principal_id'):
            raise serializers.ValidationError({
                'sede_principal_id': f'La sede principal es requerida para el rol {role}'
            })

        # No permitir rol duplicado en additional_roles
        if role in additional_roles:
            raise serializers.ValidationError({
                'additional_roles': f'El rol {role} ya está como rol principal'
            })

        return data

    def create(self, validated_data):
        """
        Crea el usuario, perfil y sincroniza con Colaborador si es necesario.
        """
        from django.contrib.auth.models import User
        from organizacion.thread_locals import get_current_organization
        from citas.models import Colaborador

        org = get_current_organization()
        if not org:
            raise serializers.ValidationError("No se pudo determinar la organización")

        # Crear usuario Django
        email = validated_data['email']
        username = f"{email.split('@')[0]}_{org.id}"

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )

        # Crear perfil
        perfil = PerfilUsuario.objects.create(
            user=user,
            organizacion=org,
            role=validated_data['role'],
            additional_roles=validated_data.get('additional_roles', []),
            sede_id=validated_data.get('sede_principal_id'),
            permissions=validated_data.get('permissions', {}),
            telefono=validated_data.get('telefono', ''),
            timezone=validated_data.get('timezone', 'UTC'),
        )

        # Asignar sedes según rol
        if validated_data.get('sedes_trabajo_ids'):
            perfil.sedes.set(validated_data['sedes_trabajo_ids'])

        if validated_data.get('sedes_administradas_ids'):
            perfil.sedes_administradas.set(validated_data['sedes_administradas_ids'])

        # Si es colaborador, crear registro en Colaborador
        if 'colaborador' in perfil.all_roles:
            Colaborador.objects.create(
                usuario=user,
                nombre=user.get_full_name(),
                email=user.email,
                sede=perfil.sede,
                organizacion=org,
            )

        return perfil


class PerfilWithRolesSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información del perfil con el nuevo sistema de roles.
    Incluye roles, sedes accesibles y permisos.
    """

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    all_roles = serializers.ReadOnlyField()
    display_badge = serializers.ReadOnlyField()
    accessible_sedes = SedeSerializer(many=True, read_only=True)
    can_access_all_sedes = serializers.ReadOnlyField()

    class Meta:
        model = PerfilUsuario
        fields = [
            'id',
            'user_email',
            'user_name',
            'organizacion',
            'role',
            'additional_roles',
            'all_roles',
            'display_badge',
            'is_active',
            'sede',
            'accessible_sedes',
            'can_access_all_sedes',
            'permissions',
            'timezone',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username