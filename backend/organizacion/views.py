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

class SedeViewSet(viewsets.ModelViewSet):
    serializer_class = SedeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Sede.all_objects.all()
        try:
            organizacion = user.perfil.organizacion
            if organizacion:
                return Sede.all_objects.filter(organizacion=organizacion)
            return Sede.objects.none()
        except AttributeError: # Catches if user has no perfil
            return Sede.objects.none()
