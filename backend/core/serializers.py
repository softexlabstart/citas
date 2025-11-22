"""
Serializers base reutilizables para evitar código duplicado.
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, date


class BaseValidationMixin:
    """
    Mixin con validaciones comunes reutilizables.
    """

    @staticmethod
    def validate_future_date(value, field_name='fecha'):
        """
        Valida que una fecha no sea en el pasado.

        Args:
            value: El valor de fecha a validar
            field_name: Nombre del campo para el mensaje de error

        Returns:
            El valor validado

        Raises:
            ValidationError si la fecha es pasada
        """
        if value and value < timezone.now():
            raise serializers.ValidationError(f'La {field_name} no puede ser en el pasado.')
        return value

    @staticmethod
    def validate_past_date(value, field_name='fecha'):
        """
        Valida que una fecha no sea en el futuro.

        Args:
            value: El valor de fecha a validar
            field_name: Nombre del campo para el mensaje de error

        Returns:
            El valor validado

        Raises:
            ValidationError si la fecha es futura
        """
        if value:
            # Si es datetime
            if isinstance(value, datetime):
                if value > timezone.now():
                    raise serializers.ValidationError(f'La {field_name} no puede ser en el futuro.')
            # Si es date
            elif isinstance(value, date):
                if value > date.today():
                    raise serializers.ValidationError(f'La {field_name} no puede ser en el futuro.')
        return value

    @staticmethod
    def validate_email_unique(value, model, instance=None, error_message=None):
        """
        Valida que un email sea único en el modelo especificado.

        Args:
            value: El email a validar
            model: El modelo a verificar
            instance: La instancia actual (para updates)
            error_message: Mensaje de error personalizado

        Returns:
            El valor validado

        Raises:
            ValidationError si el email ya existe
        """
        queryset = model.objects.filter(email=value)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)

        if queryset.exists():
            msg = error_message or 'Este email ya está en uso.'
            raise serializers.ValidationError(msg)

        return value

    @staticmethod
    def validate_phone_format(value):
        """
        Valida formato básico de teléfono.

        Args:
            value: El número de teléfono a validar

        Returns:
            El valor validado

        Raises:
            ValidationError si el formato es inválido
        """
        if not value:
            return value

        # Eliminar espacios y caracteres especiales comunes
        cleaned = value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')

        # Verificar que solo contenga dígitos
        if not cleaned.isdigit():
            raise serializers.ValidationError('El teléfono solo debe contener números y caracteres válidos (+, -, espacios, paréntesis).')

        # Verificar longitud razonable (entre 7 y 15 dígitos)
        if len(cleaned) < 7 or len(cleaned) > 15:
            raise serializers.ValidationError('El teléfono debe tener entre 7 y 15 dígitos.')

        return value

    @staticmethod
    def validate_positive_number(value, field_name='valor'):
        """
        Valida que un número sea positivo.

        Args:
            value: El número a validar
            field_name: Nombre del campo para el mensaje de error

        Returns:
            El valor validado

        Raises:
            ValidationError si el número no es positivo
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError(f'El {field_name} debe ser mayor que 0.')
        return value

    @staticmethod
    def validate_date_range(start_date, end_date, start_field='fecha_inicio', end_field='fecha_fin'):
        """
        Valida que una fecha de inicio sea anterior a la fecha de fin.

        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            start_field: Nombre del campo de inicio
            end_field: Nombre del campo de fin

        Raises:
            ValidationError si el rango es inválido
        """
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                end_field: f'La {end_field} debe ser posterior a la {start_field}.'
            })


class OrganizationIsolatedSerializer(serializers.ModelSerializer):
    """
    Serializer base para modelos que requieren aislamiento por organización.
    Automáticamente filtra querysets por la organización del usuario.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_organization_filtering()

    def _setup_organization_filtering(self):
        """
        Configura filtrado automático por organización en campos relacionados.
        Override este método en subclases si se necesita lógica personalizada.
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return

        user = request.user
        if not user or not user.is_authenticated:
            return

        # Obtener organización del usuario si existe
        org = getattr(user, 'organization', None)
        if not org:
            return

        # Filtrar querysets de campos relacionados por organización
        for field_name, field in self.fields.items():
            if isinstance(field, serializers.PrimaryKeyRelatedField):
                if hasattr(field.queryset, 'model'):
                    model = field.queryset.model
                    # Si el modelo tiene campo 'organization', filtrar
                    if hasattr(model, 'organization'):
                        field.queryset = field.queryset.filter(organization=org)


class TimestampedSerializer(serializers.ModelSerializer):
    """
    Serializer base para modelos con campos de timestamp (created_at, updated_at).
    Incluye estos campos como read-only automáticamente.
    """

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class SoftDeleteSerializer(serializers.ModelSerializer):
    """
    Serializer base para modelos con soft delete (is_deleted).
    Excluye objetos eliminados por defecto.
    """

    def get_queryset(self):
        """Override para excluir objetos soft-deleted"""
        queryset = super().get_queryset()
        if hasattr(queryset.model, 'is_deleted'):
            return queryset.filter(is_deleted=False)
        return queryset
