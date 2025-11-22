"""
Utilidades centralizadas para logging.
Evita código duplicado en el sistema.
"""
import logging
from typing import Optional


def get_logger(module_name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.

    Args:
        module_name: Nombre del módulo (__name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(module_name)


class SecurityLogger:
    """
    Logger especializado para eventos de seguridad.
    Centraliza el formato de logs de seguridad.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_login(self, username: str, org_count: Optional[int] = None):
        """Registra un inicio de sesión exitoso"""
        if org_count:
            self.logger.info(f'[SECURITY] Usuario {username} con {org_count} organizaciones inicia sesión')
        else:
            self.logger.info(f'[SECURITY] Usuario {username} inicia sesión')

    def log_logout(self, username: str, success: bool = True):
        """Registra un cierre de sesión"""
        if success:
            self.logger.info(f'[SECURITY] Usuario {username} cerró sesión exitosamente')
        else:
            self.logger.warning(f'[SECURITY] Fallo en cierre de sesión para usuario {username}')

    def log_session_created(self, username: str, ip_address: str):
        """Registra creación de nueva sesión"""
        self.logger.info(f'[SECURITY] Nueva sesión creada para usuario {username} desde IP {ip_address}')

    def log_session_revoked(self, username: str, reason: str = 'Max sessions reached'):
        """Registra revocación de sesión"""
        self.logger.info(f'[SECURITY] {reason} para usuario {username}, sesión más antigua revocada')

    def log_failed_attempt(self, identifier: str, reason: str):
        """Registra intento fallido"""
        self.logger.warning(f'[SECURITY] Intento fallido: {reason} - {identifier}')


class UserActionLogger:
    """
    Logger para acciones de usuarios.
    Centraliza el formato de logs de acciones.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_user_created(self, username: str, email: str, context: str = ''):
        """Registra creación de usuario"""
        suffix = f' - {context}' if context else ''
        self.logger.info(f'Nuevo usuario creado: {username} ({email}){suffix}')

    def log_user_updated(self, username: str, field: str):
        """Registra actualización de usuario"""
        self.logger.info(f'Usuario actualizado: {username} - Campo: {field}')

    def log_org_joined(self, username: str, org_name: str):
        """Registra que un usuario se unió a una organización"""
        self.logger.info(f'Usuario {username} agregado a organización: {org_name}')


class EmailLogger:
    """
    Logger para eventos de email.
    Centraliza el formato de logs de emails.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_email_sent(self, recipient: str, subject: str, context: str = ''):
        """Registra email enviado exitosamente"""
        ctx = f' - {context}' if context else ''
        self.logger.info(f'Email enviado a {recipient}: {subject}{ctx}')

    def log_email_failed(self, recipient: str, error: str, context: str = ''):
        """Registra fallo en envío de email"""
        ctx = f' - {context}' if context else ''
        self.logger.error(f'Error al enviar email a {recipient}: {error}{ctx}')

    def log_invitation_sent(self, recipient: str, sender: str):
        """Registra invitación enviada"""
        self.logger.info(f'Invitación enviada a {recipient} por {sender}')


class ErrorLogger:
    """
    Logger para errores y excepciones.
    Centraliza el manejo de errores.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_error(self, context: str, error: Exception, include_trace: bool = False):
        """Registra un error con contexto"""
        if include_trace:
            self.logger.error(f'Error en {context}: {str(error)}', exc_info=True)
        else:
            self.logger.error(f'Error en {context}: {str(error)}')

    def log_warning(self, message: str, context: str = ''):
        """Registra una advertencia"""
        prefix = f'[{context}] ' if context else ''
        self.logger.warning(f'{prefix}{message}')

    def log_validation_error(self, field: str, value: str, reason: str):
        """Registra error de validación"""
        self.logger.warning(f'Error de validación - Campo: {field}, Valor: {value}, Razón: {reason}')


class AppointmentLogger:
    """
    Logger especializado para eventos de citas.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_appointment_created(self, appointment_id: int, client_name: str, is_guest: bool = False):
        """Registra creación de cita"""
        guest_info = ' (invitado)' if is_guest else ''
        self.logger.info(f'Cita creada #{appointment_id} - Cliente: {client_name}{guest_info}')

    def log_appointment_cancelled(self, appointment_id: int, reason: str = ''):
        """Registra cancelación de cita"""
        reason_info = f' - Razón: {reason}' if reason else ''
        self.logger.info(f'Cita cancelada #{appointment_id}{reason_info}')

    def log_appointment_updated(self, appointment_id: int, field: str, old_value: str, new_value: str):
        """Registra actualización de cita"""
        self.logger.info(f'Cita actualizada #{appointment_id} - {field}: {old_value} → {new_value}')


class LoggerFactory:
    """
    Factory para obtener loggers especializados fácilmente.
    """

    @staticmethod
    def get_security_logger(module_name: str) -> SecurityLogger:
        """Obtiene un SecurityLogger"""
        return SecurityLogger(get_logger(module_name))

    @staticmethod
    def get_user_logger(module_name: str) -> UserActionLogger:
        """Obtiene un UserActionLogger"""
        return UserActionLogger(get_logger(module_name))

    @staticmethod
    def get_email_logger(module_name: str) -> EmailLogger:
        """Obtiene un EmailLogger"""
        return EmailLogger(get_logger(module_name))

    @staticmethod
    def get_error_logger(module_name: str) -> ErrorLogger:
        """Obtiene un ErrorLogger"""
        return ErrorLogger(get_logger(module_name))

    @staticmethod
    def get_appointment_logger(module_name: str) -> AppointmentLogger:
        """Obtiene un AppointmentLogger"""
        return AppointmentLogger(get_logger(module_name))
