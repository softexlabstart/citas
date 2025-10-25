"""
Mensajes de error genéricos para proteger información del sistema.

IMPORTANTE: Estos mensajes NO deben revelar:
- Existencia de organizaciones, usuarios o recursos
- Estructura de la base de datos
- Relaciones entre entidades
- Validaciones específicas del negocio

Los mensajes detallados se loguean para debugging, pero NO se envían al cliente.
"""

# Mensajes de autenticación y autorización
UNAUTHORIZED = "No tienes permisos para realizar esta acción"
ACCESS_DENIED = "Acceso denegado"
INVALID_CREDENTIALS = "Credenciales inválidas"
SESSION_EXPIRED = "Tu sesión ha expirado. Por favor, inicia sesión nuevamente"

# Mensajes de operaciones
OPERATION_NOT_ALLOWED = "No se puede completar esta operación"
INVALID_REQUEST = "Solicitud inválida"
RESOURCE_NOT_FOUND = "El recurso solicitado no está disponible"
DATA_VALIDATION_ERROR = "Los datos proporcionados no son válidos"

# Mensajes de creación/actualización
CREATION_FAILED = "No se pudo crear el registro"
UPDATE_FAILED = "No se pudo actualizar el registro"
DELETION_FAILED = "No se pudo eliminar el registro"

# Mensajes de duplicados (sin revelar qué campo está duplicado)
DUPLICATE_ENTRY = "Ya existe un registro con estos datos"
EMAIL_IN_USE = "El correo electrónico ya está registrado"
USERNAME_TAKEN = "El nombre de usuario no está disponible"

# Mensajes de registro/invitación
INVALID_INVITATION = "El enlace de invitación no es válido o ha expirado"
REGISTRATION_FAILED = "No se pudo completar el registro"

# Mensajes de sistema
SYSTEM_ERROR = "Ha ocurrido un error. Por favor, intenta nuevamente"
SERVICE_UNAVAILABLE = "El servicio no está disponible temporalmente"

# Mensajes de validación genéricos
REQUIRED_FIELDS_MISSING = "Faltan campos obligatorios"
INVALID_FORMAT = "El formato de los datos es incorrecto"
INVALID_VALUE = "Uno o más valores son inválidos"
