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
    sede_id = serializers.PrimaryKeyRelatedField(queryset=Sede.objects.all(), source='sede', write_only=True)

    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'duracion_estimada', 'precio', 'metadata', 'sede', 'sede_id']

class ColaboradorSerializer(serializers.ModelSerializer):
    sede = SedeSerializer(read_only=True)
    sede_id = serializers.PrimaryKeyRelatedField(queryset=Sede.objects.all(), source='sede', write_only=True)
    class Meta:
        model = Colaborador
        fields = ['id', 'nombre', 'email', 'descripcion', 'metadata', 'sede', 'sede_id']

class BloqueoSerializer(serializers.ModelSerializer):
    # For read operations, show the nested object
    colaborador = ColaboradorSerializer(read_only=True)

    # For write operations, accept IDs
    colaborador_id = serializers.PrimaryKeyRelatedField(
        queryset=Colaborador.objects.all(), source='colaborador', write_only=True
    )

    class Meta:
        model = Bloqueo
        fields = ['id', 'colaborador', 'motivo', 'fecha_inicio', 'fecha_fin', 'colaborador_id']

class CitaSerializer(serializers.ModelSerializer):
    servicios = ServicioSerializer(many=True, read_only=True)
    servicios_ids = serializers.PrimaryKeyRelatedField(queryset=Servicio.objects.all(), source='servicios', many=True, write_only=True)
    user = UserSerializer(read_only=True)
    colaboradores = ColaboradorSerializer(many=True, read_only=True)
    colaboradores_ids = serializers.PrimaryKeyRelatedField(queryset=Colaborador.objects.all(), source='colaboradores', many=True, write_only=True)
    sede = SedeSerializer(read_only=True)
    sede_id = serializers.PrimaryKeyRelatedField(queryset=Sede.objects.all(), source='sede', write_only=True)

    class Meta:
        model = Cita
        fields = ['id', 'nombre', 'fecha', 'servicios', 'servicios_ids', 'confirmado', 'user', 'estado', 'colaboradores', 'colaboradores_ids', 'sede', 'sede_id', 'comentario']

    def validate_fecha(self, value):
        if self.instance and self.instance.estado == 'Cancelada':
            raise serializers.ValidationError("No se puede reprogramar una cita cancelada.")
        if value < timezone.now():
            raise serializers.ValidationError("No se pueden agendar citas en fechas pasadas.")
        return value

    def validate(self, data):
        if self.instance and self.instance.estado == 'Cancelada':
            raise serializers.ValidationError("No se puede modificar una cita cancelada.")

        colaboradores = data.get('colaboradores', self.instance.colaboradores.all() if self.instance else [])
        fecha = data.get('fecha', self.instance.fecha if self.instance else None)
        servicios = data.get('servicios', self.instance.servicios.all() if self.instance else [])
        sede = data.get('sede', self.instance.sede if self.instance else None)
        cita_id = self.instance.id if self.instance else None

        if not all([colaboradores, fecha, servicios, sede]):
            return data

        for servicio in servicios:
            check_appointment_availability(sede, servicio, colaboradores, fecha, cita_id)

        return data