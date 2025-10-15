from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import GuideSection
from .serializers import GuideSectionSerializer


class GuideSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para las secciones de la guía.
    Permite a cualquier usuario (autenticado o no) consultar la guía.

    Filtros disponibles:
    - language: Filtrar por idioma (es, en)
    - category: Filtrar por categoría (general, usuarios, administradores, colaboradores)
    """
    serializer_class = GuideSectionSerializer
    permission_classes = [AllowAny]  # Accesible para todos

    def get_queryset(self):
        """
        Retorna solo las secciones activas, ordenadas por categoría y orden.
        Permite filtrar por idioma y categoría.
        """
        queryset = GuideSection.objects.filter(is_active=True)

        # Filtrar por idioma si se especifica
        language = self.request.query_params.get('language', None)
        if language:
            queryset = queryset.filter(language=language)

        # Filtrar por categoría si se especifica
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        return queryset.order_by('category', 'order', 'title')
