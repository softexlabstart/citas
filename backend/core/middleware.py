from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class OrganizationMiddleware(MiddlewareMixin):
    """
    Middleware para extraer el ID de la organización del header HTTP X-Organization-ID
    y almacenarlo en el objeto request para uso en views y managers.
    
    Este middleware soporta el sistema multi-tenant permitiendo que un usuario
    con múltiples perfiles acceda a diferentes organizaciones.
    """
    
    def process_request(self, request):
        # Obtener el ID de la organización del header
        org_id = request.META.get('HTTP_X_ORGANIZATION_ID')
        
        if org_id:
            try:
                request.organization_id = int(org_id)
                logger.debug(f'Organization ID set from header: {org_id}')
            except (ValueError, TypeError):
                request.organization_id = None
                logger.warning(f'Invalid organization ID in header: {org_id}')
        else:
            # Si no hay header, intentar obtenerlo del perfil del usuario autenticado
            if hasattr(request, 'user') and request.user.is_authenticated:
                # Si el usuario tiene un solo perfil, usar esa organización
                perfiles = request.user.perfiles.all()
                if perfiles.count() == 1:
                    perfil = perfiles.first()
                    if perfil and perfil.organizacion:
                        request.organization_id = perfil.organizacion.id
                        logger.debug(f'Organization ID set from single profile: {request.organization_id}')
                    else:
                        request.organization_id = None
                else:
                    # Usuario con múltiples perfiles debe enviar el header
                    request.organization_id = None
            else:
                request.organization_id = None
        
        return None
