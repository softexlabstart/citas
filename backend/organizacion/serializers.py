from rest_framework import serializers
from .models import Sede

class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = '__all__'
