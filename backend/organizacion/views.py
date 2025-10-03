from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Sede, Organizacion
from .serializers import SedeSerializer, OrganizacionSerializer
from usuarios.permissions import IsSuperAdmin

class CreateOrganizacionView(APIView):
    """Vista para que un SuperAdmin cree una nueva Organizacion."""
    permission_classes = [IsSuperAdmin]

    def post(self, request, *args, **kwargs):
        serializer = OrganizacionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizacionPublicView(APIView):
    """Vista pública para obtener información básica de una organización por slug."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug, *args, **kwargs):
        try:
            organizacion = Organizacion.objects.get(slug=slug)
            return Response({
                'id': organizacion.id,
                'nombre': organizacion.nombre,
                'slug': organizacion.slug
            })
        except Organizacion.DoesNotExist:
            return Response({
                'error': 'Organización no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)

class SedeViewSet(viewsets.ModelViewSet):
    serializer_class = SedeSerializer
    # No permission_classes aquí - se define en get_permissions()

    def get_permissions(self):
        # Allow public access for list action when organizacion_slug is provided
        if self.action == 'list' and 'organizacion_slug' in self.request.query_params:
            return [permissions.AllowAny()]
        # Require authentication for other actions
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        organizacion_slug = self.request.query_params.get('organizacion_slug')

        # If organizacion_slug is provided (public access), filter by slug
        if organizacion_slug:
            return Sede.all_objects.filter(organizacion__slug=organizacion_slug)

        # Authenticated user access
        if user.is_authenticated:
            if user.is_superuser:
                return Sede.all_objects.all()
            try:
                organizacion = user.perfil.organizacion
                if organizacion:
                    return Sede.all_objects.filter(organizacion=organizacion)
                return Sede.objects.none()
            except AttributeError: # Catches if user has no perfil
                return Sede.objects.none()

        # No access for unauthenticated without slug
        return Sede.objects.none()
