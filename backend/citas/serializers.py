from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import F
from .models import Cita, Servicio, Horario, Colaborador, Bloqueo
from usuarios.serializers import UserSerializer
from organizacion.models import Sede
from .services import check_appointment_availability

class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ['id', 'nombre']

class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = '__all__'

class ServicioSerializer(serializers.ModelSerializer):
    sede = SedeSerializer(read_only=True)
    sede_id = serializers.PrimaryKeyRelatedField(queryset=Sede.all_objects.all(), source='sede', write_only=True)

    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'duracion_estimada', 'precio', 'metadata', 'sede', 'sede_id']

class ColaboradorSerializer(serializers.ModelSerializer):
    sede = SedeSerializer(read_only=True)
    sede_id = serializers.PrimaryKeyRelatedField(queryset=Sede.all_objects.all(), source='sede', write_only=True)
    class Meta:
        model = Colaborador
        fields = ['id', 'nombre', 'email', 'descripcion', 'metadata', 'sede', 'sede_id']

class BloqueoSerializer(serializers.ModelSerializer):
    # For read operations, show the nested object
    colaborador = ColaboradorSerializer(read_only=True)

    # For write operations, accept IDs
    colaborador_id = serializers.PrimaryKeyRelatedField(
        queryset=Colaborador.all_objects.all(), source='colaborador', write_only=True
    )

    class Meta:
        model = Bloqueo
        fields = ['id', 'colaborador', 'motivo', 'fecha_inicio', 'fecha_fin', 'colaborador_id']

    def to_representation(self, instance):
        """Override to ensure colaborador is fetched with all_objects"""
        representation = super().to_representation(instance)
        if instance.colaborador_id:
            try:
                colaborador = Colaborador.all_objects.select_related('sede').get(id=instance.colaborador_id)
                representation['colaborador'] = ColaboradorSerializer(colaborador).data
            except Colaborador.DoesNotExist:
                representation['colaborador'] = None
        return representation

class CitaSerializer(serializers.ModelSerializer):
    servicios = ServicioSerializer(many=True, read_only=True)
    servicios_ids = serializers.PrimaryKeyRelatedField(queryset=Servicio.all_objects.all(), source='servicios', many=True, write_only=True)
    user = UserSerializer(read_only=True)
    colaboradores = ColaboradorSerializer(many=True, read_only=True)
    colaboradores_ids = serializers.PrimaryKeyRelatedField(queryset=Colaborador.all_objects.all(), source='colaboradores', many=True, write_only=True)
    sede = SedeSerializer(read_only=True)
    sede_id = serializers.PrimaryKeyRelatedField(queryset=Sede.all_objects.all(), source='sede', write_only=True)

    class Meta:
        model = Cita
        fields = ['id', 'nombre', 'fecha', 'servicios', 'servicios_ids', 'confirmado', 'user', 'estado', 'colaboradores', 'colaboradores_ids', 'sede', 'sede_id', 'comentario']
        read_only_fields = ['id', 'user', 'confirmado', 'estado']  # SECURITY: Status changes only via dedicated actions

    def validate_servicios_ids(self, value):
        """
        Check that at least one service is provided.
        """
        if not value:
            raise serializers.ValidationError("Debe seleccionar al menos un servicio.")
        return value

    def validate_fecha(self, value):
        if self.instance and self.instance.estado == 'Cancelada':
            raise serializers.ValidationError("No se puede reprogramar una cita cancelada.")
        if value < timezone.now():
            raise serializers.ValidationError("No se pueden agendar citas en fechas pasadas.")
        return value

    def validate_nombre(self, value):
        """SECURITY: Validate nombre field to prevent XSS attacks."""
        from core.validators import validate_no_html_tags
        return validate_no_html_tags(value)

    def validate_comentario(self, value):
        """SECURITY: Validate comentario field to prevent XSS attacks."""
        from core.validators import validate_no_html_tags
        if value:
            return validate_no_html_tags(value)
        return value

    def validate(self, data):
        if self.instance and self.instance.estado == 'Cancelada':
            raise serializers.ValidationError("No se puede modificar una cita cancelada.")

        # Get values from data or fallback to instance values
        # Convert QuerySets to lists to ensure proper validation
        colaboradores_qs = data.get('colaboradores', self.instance.colaboradores.all() if self.instance else None)
        colaboradores = list(colaboradores_qs) if colaboradores_qs is not None else []

        fecha = data.get('fecha', self.instance.fecha if self.instance else None)

        servicios_qs = data.get('servicios', self.instance.servicios.all() if self.instance else None)
        servicios = list(servicios_qs) if servicios_qs is not None else []

        sede = data.get('sede', self.instance.sede if self.instance else None)
        cita_id = self.instance.id if self.instance else None

        # CRITICAL FIX: Always validate availability when we have all required data
        # Check that all required values are present and not empty
        if colaboradores and fecha and servicios and sede:
            check_appointment_availability(sede, servicios, colaboradores, fecha, cita_id)
        elif not self.instance:
            # For new appointments, all fields are required
            if not colaboradores:
                raise serializers.ValidationError("Debe seleccionar al menos un colaborador.")
            if not servicios:
                raise serializers.ValidationError("Debe seleccionar al menos un servicio.")
            if not sede:
                raise serializers.ValidationError("Debe seleccionar una sede.")
            if not fecha:
                raise serializers.ValidationError("Debe seleccionar una fecha.")

        return data


class GuestCitaSerializer(serializers.ModelSerializer):
    """
    Serializer para citas creadas por invitados (sin cuenta de usuario).
    Requiere email_cliente y permite crear citas sin autenticación.
    """
    servicios = ServicioSerializer(many=True, read_only=True)
    servicios_ids = serializers.PrimaryKeyRelatedField(
        queryset=Servicio.all_objects.all(),
        source='servicios',
        many=True,
        write_only=True
    )
    colaboradores = ColaboradorSerializer(many=True, read_only=True)
    colaboradores_ids = serializers.PrimaryKeyRelatedField(
        queryset=Colaborador.all_objects.all(),
        source='colaboradores',
        many=True,
        write_only=True
    )
    sede = SedeSerializer(read_only=True)
    sede_id = serializers.PrimaryKeyRelatedField(
        queryset=Sede.all_objects.all(),
        source='sede',
        write_only=True
    )

    class Meta:
        model = Cita
        fields = [
            'id', 'nombre', 'email_cliente', 'telefono_cliente', 'fecha',
            'servicios', 'servicios_ids', 'confirmado', 'estado',
            'colaboradores', 'colaboradores_ids', 'sede', 'sede_id', 'comentario'
        ]
        read_only_fields = ['id', 'confirmado', 'estado']  # SECURITY: Guests cannot confirm or change status

    def validate(self, data):
        # Validar que se proporcione email_cliente para reservas de invitados
        if not data.get('email_cliente'):
            raise serializers.ValidationError({
                'email_cliente': 'El email es requerido para reservas de invitados.'
            })

        # Validar disponibilidad
        # Get values from data or fallback to instance values
        # Convert QuerySets to lists to ensure proper validation
        colaboradores_qs = data.get('colaboradores', self.instance.colaboradores.all() if self.instance else None)
        colaboradores = list(colaboradores_qs) if colaboradores_qs is not None else []

        fecha = data.get('fecha', self.instance.fecha if self.instance else None)

        servicios_qs = data.get('servicios', self.instance.servicios.all() if self.instance else None)
        servicios = list(servicios_qs) if servicios_qs is not None else []

        sede = data.get('sede', self.instance.sede if self.instance else None)
        cita_id = self.instance.id if self.instance else None

        # CRITICAL FIX: Always validate availability when we have all required data
        # Check that all required values are present and not empty
        if colaboradores and fecha and servicios and sede:
            check_appointment_availability(sede, servicios, colaboradores, fecha, cita_id)
        elif not self.instance:
            # For new appointments, all fields are required
            if not colaboradores:
                raise serializers.ValidationError("Debe seleccionar al menos un colaborador.")
            if not servicios:
                raise serializers.ValidationError("Debe seleccionar al menos un servicio.")
            if not sede:
                raise serializers.ValidationError("Debe seleccionar una sede.")
            if not fecha:
                raise serializers.ValidationError("Debe seleccionar una fecha.")

        return data

    def validate_fecha(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("No se pueden agendar citas en fechas pasadas.")
        return value

    def validate_servicios_ids(self, value):
        if not value:
            raise serializers.ValidationError("Debe seleccionar al menos un servicio.")
        return value