from rest_framework import serializers
from .models import GuideSection


class GuideSectionSerializer(serializers.ModelSerializer):
    """
    Serializer para las secciones de la guía de usuario.
    """
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)

    class Meta:
        model = GuideSection
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'category',
            'category_display',
            'order',
            'icon',
            'language',
            'language_display',
            'video_url',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
