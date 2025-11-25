"""
Custom logging handler para guardar logs en base de datos.
"""
import logging
import traceback
from django.conf import settings


class DatabaseLogHandler(logging.Handler):
    """
    Handler que guarda logs en la base de datos usando el modelo ApplicationLog.
    """

    def emit(self, record):
        """
        Guarda el log record en la base de datos.
        """
        try:
            # Importar aquí para evitar circular imports
            from organizacion.models_logs import ApplicationLog
            from organizacion.thread_locals import get_current_organization

            # Obtener organización actual del thread local si existe
            organizacion = None
            try:
                organizacion = get_current_organization()
            except Exception:
                pass

            # Obtener información del usuario si está disponible
            user_id = None
            user_username = ''
            if hasattr(record, 'request') and hasattr(record.request, 'user'):
                user = record.request.user
                if user and user.is_authenticated:
                    user_id = user.id
                    user_username = user.username

            # Obtener traceback si hay excepción
            exc_info_str = ''
            if record.exc_info:
                exc_info_str = ''.join(traceback.format_exception(*record.exc_info))

            # Obtener información del request si está disponible
            request_path = ''
            request_method = ''
            request_user_agent = ''
            if hasattr(record, 'request'):
                req = record.request
                request_path = getattr(req, 'path', '')
                request_method = getattr(req, 'method', '')
                if hasattr(req, 'META'):
                    request_user_agent = req.META.get('HTTP_USER_AGENT', '')[:500]

            # Crear el log en la base de datos
            ApplicationLog.objects.create(
                level=record.levelname,
                logger_name=record.name,
                message=record.getMessage(),
                organizacion=organizacion,
                user_id=user_id,
                user_username=user_username,
                pathname=record.pathname,
                func_name=record.funcName,
                lineno=record.lineno,
                exc_info=exc_info_str,
                request_path=request_path,
                request_method=request_method,
                request_user_agent=request_user_agent,
            )

        except Exception as e:
            # No queremos que un error en el logging rompa la aplicación
            # Solo loggear en stderr
            import sys
            print(f"Error saving log to database: {str(e)}", file=sys.stderr)

    def format(self, record):
        """No necesitamos formatear porque guardamos campos individuales"""
        return record.getMessage()
