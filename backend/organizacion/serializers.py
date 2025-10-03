from rest_framework import serializers
from .models import Organizacion, Sede

class OrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizacion
        fields = ['id', 'nombre', 'slug']

class SedeSerializer(serializers.ModelSerializer):
    organizacion_nombre = serializers.CharField(source='organizacion.nombre', read_only=True)
    organizacion_slug = serializers.CharField(source='organizacion.slug', read_only=True)

    class Meta:
        model = Sede
        fields = ['id', 'nombre', 'organizacion', 'organizacion_nombre', 'organizacion_slug', 'direccion', 'telefono']