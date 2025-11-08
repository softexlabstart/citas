from rest_framework import serializers
from .models import Organizacion, Sede

class OrganizacionSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Organizacion
        fields = [
            'id', 'nombre', 'slug', 'is_active',
            'permitir_agendamiento_publico',
            'usar_branding_personalizado', 'logo', 'logo_url',
            'color_primario', 'color_secundario',
            'color_texto', 'color_fondo',
            'texto_bienvenida'
        ]
        extra_kwargs = {
            'logo': {'write_only': True}  # Solo para escritura, usamos logo_url para lectura
        }

    def get_logo_url(self, obj):
        """Retorna la URL completa del logo si existe"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

class SedeSerializer(serializers.ModelSerializer):
    organizacion_nombre = serializers.CharField(source='organizacion.nombre', read_only=True)
    organizacion_slug = serializers.CharField(source='organizacion.slug', read_only=True)

    class Meta:
        model = Sede
        fields = ['id', 'nombre', 'organizacion', 'organizacion_nombre', 'organizacion_slug', 'direccion', 'telefono']