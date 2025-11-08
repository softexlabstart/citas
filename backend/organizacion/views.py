from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from .models import Sede, Organizacion
from .serializers import SedeSerializer, OrganizacionSerializer
from usuarios.permissions import IsSuperAdmin
import logging
from typing import Any

# MULTI-TENANT: Import helper for profile management
from usuarios.utils import get_perfil_or_first

logger = logging.getLogger(__name__)

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

    def get(self, request: Request, slug: str, *args: Any, **kwargs: Any) -> Response:
        try:
            organizacion = Organizacion.objects.get(slug=slug, is_active=True)

            # Obtener sedes de esta organización
            sedes = organizacion.sedes.all().values('id', 'nombre', 'direccion', 'telefono')

            response_data = {
                'id': organizacion.id,
                'nombre': organizacion.nombre,
                'slug': organizacion.slug,
                'permitir_agendamiento_publico': organizacion.permitir_agendamiento_publico,
                'sedes': list(sedes)
            }

            # Agregar branding si está habilitado
            if organizacion.usar_branding_personalizado:
                response_data['branding'] = {
                    'logo_url': organizacion.logo_url,
                    'color_primario': organizacion.color_primario or '#007bff',
                    'color_secundario': organizacion.color_secundario or '#6c757d',
                    'color_texto': organizacion.color_texto or '#212529',
                    'color_fondo': organizacion.color_fondo or '#ffffff',
                    'texto_bienvenida': organizacion.texto_bienvenida or ''
                }
            else:
                response_data['branding'] = None

            return Response(response_data)
        except Organizacion.DoesNotExist:
            # SECURITY: Log para debugging, mensaje genérico al cliente
            logger.info(f"Intento de acceso a organización con slug inexistente: {slug}")
            return Response({
                'error': 'No se encontró la información solicitada'
            }, status=status.HTTP_404_NOT_FOUND)

class SedeViewSet(viewsets.ModelViewSet):  # type: ignore
    serializer_class = SedeSerializer
    # No permission_classes aquí - se define en get_permissions()

    def get_permissions(self):  # type: ignore
        # Allow public access for list action when organizacion_slug is provided
        if self.action == 'list' and 'organizacion_slug' in self.request.query_params:
            return [permissions.AllowAny()]
        # Require authentication for other actions
        return [permissions.IsAuthenticated()]

    def get_queryset(self):  # type: ignore
        user = self.request.user
        organizacion_slug = self.request.query_params.get('organizacion_slug')

        # If organizacion_slug is provided (public access), filter by slug
        if organizacion_slug:
            return Sede.all_objects.filter(organizacion__slug=organizacion_slug)

        # Authenticated user access
        if user.is_authenticated:
            if user.is_superuser:
                return Sede.all_objects.all()

            # MULTI-TENANT: Usar helper para obtener perfil
            perfil = get_perfil_or_first(user)
            if perfil:
                # Verificar si es administrador de sedes específicas
                # SECURITY: Usar Django ORM en lugar de SQL raw
                # Las relaciones ManyToMany no pasan por OrganizationManager
                sedes_admin_ids = list(perfil.sedes_administradas.values_list('id', flat=True))

                if sedes_admin_ids:
                    # Usuario administra sedes específicas - mostrar solo esas
                    return Sede.all_objects.filter(id__in=sedes_admin_ids)

                # MULTI-TENANT: Usuario regular - verificar campo 'sedes' M2M
                # Estas son las sedes a las que el usuario tiene acceso explícito
                # Usar property sedes_acceso que bypasses OrganizacionManager filtering
                sedes_acceso = perfil.sedes_acceso
                if sedes_acceso.exists():
                    return sedes_acceso

                # Si no tiene sedes M2M, mostrar solo su sede principal
                if perfil.sede:
                    return Sede.all_objects.filter(id=perfil.sede.id)

                # Fallback: Si tiene organización, mostrar todas las sedes de la organización
                organizacion = perfil.organizacion
                if organizacion:
                    return Sede.all_objects.filter(organizacion=organizacion)

            return Sede.objects.none()

        # No access for unauthenticated without slug
        return Sede.objects.none()
