"""
Custom validators for input sanitization and XSS prevention.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import bleach


def validate_no_html_tags(value):
    """
    SECURITY: Prevent HTML/Script injection in text fields.
    Blocks common XSS vectors while allowing safe characters.
    """
    if not value:
        return value

    # Lista de tags peligrosos
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'<iframe[^>]*>.*?</iframe>',  # Iframes
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers (onclick, onload, etc)
        r'<object[^>]*>',  # Object tags
        r'<embed[^>]*>',  # Embed tags
        r'<link[^>]*>',  # Link tags
        r'<style[^>]*>',  # Style tags
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, str(value), re.IGNORECASE):
            raise ValidationError(
                _('El texto contiene contenido no permitido. No se permiten scripts, HTML o código malicioso.'),
                code='xss_attempt'
            )

    return value


def sanitize_html(value, allowed_tags=None, allowed_attributes=None):
    """
    SECURITY: Sanitize HTML using bleach library.
    Removes dangerous tags and attributes while preserving safe ones.

    Args:
        value: String to sanitize
        allowed_tags: List of allowed HTML tags (default: safe subset)
        allowed_attributes: Dict of allowed attributes per tag

    Returns:
        Sanitized string
    """
    if not value:
        return value

    # Tags seguros por defecto (solo formato básico)
    if allowed_tags is None:
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']

    # Atributos seguros por defecto (ninguno)
    if allowed_attributes is None:
        allowed_attributes = {}

    # Limpiar el HTML
    cleaned = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True  # Eliminar tags no permitidos en lugar de escaparlos
    )

    return cleaned


def validate_safe_filename(value):
    """
    SECURITY: Validate filename to prevent directory traversal attacks.
    """
    if not value:
        return value

    # Patrones peligrosos en nombres de archivo
    dangerous_patterns = [
        r'\.\.',  # Directory traversal
        r'/',  # Path separator
        r'\\',  # Windows path separator
        r'\0',  # Null byte
        r'[<>:"|?*]',  # Invalid filename characters
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, str(value)):
            raise ValidationError(
                _('El nombre de archivo contiene caracteres no permitidos.'),
                code='invalid_filename'
            )

    return value


def validate_no_sql_keywords(value):
    """
    SECURITY: Basic check for SQL injection attempts in text fields.
    Note: This is a defense-in-depth measure. Primary protection is using ORM.
    """
    if not value:
        return value

    # Palabras clave SQL sospechosas en contextos donde no deberían estar
    sql_keywords = [
        r'\bDROP\s+TABLE\b',
        r'\bDELETE\s+FROM\b',
        r'\bUPDATE\s+.*\s+SET\b',
        r'\bINSERT\s+INTO\b',
        r'\bEXEC\s*\(',
        r'\bUNION\s+SELECT\b',
        r'--',  # SQL comment
        r'/\*.*\*/',  # SQL comment
        r'\bOR\s+1\s*=\s*1\b',  # Classic SQL injection
        r'\bAND\s+1\s*=\s*1\b',
    ]

    for pattern in sql_keywords:
        if re.search(pattern, str(value), re.IGNORECASE):
            raise ValidationError(
                _('El texto contiene contenido sospechoso de inyección SQL.'),
                code='sql_injection_attempt'
            )

    return value
