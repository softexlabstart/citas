"""
Database Router para Multi-Tenant con Schema Isolation.

Este router determina a qué schema PostgreSQL debe ir cada query basándose
en el tenant actual almacenado en thread-local storage.

Arquitectura:
- Schema 'public': Tablas compartidas (Organizacion, Plan, Suscripcion, User)
- Schema 'tenant_X': Tablas del tenant (Cita, Servicio, PerfilUsuario, etc.)
"""

from django.conf import settings
from organizacion.thread_locals import get_current_organization
import logging

logger = logging.getLogger(__name__)


class TenantRouter:
    """
    Router que dirige operaciones de base de datos al schema correcto.
    """

    # Tablas que SIEMPRE van en el schema 'public' (compartidas entre todos los tenants)
    SHARED_APPS = [
        'contenttypes',
        'auth',  # User, Group, Permission
        'sessions',
        'admin',
        'authtoken',
        'token_blacklist',  # JWT blacklist
        'axes',  # Brute force protection
    ]

    SHARED_MODELS = [
        'organizacion.Organizacion',  # Tabla maestra de tenants
        'billing.Plan',  # Planes de suscripción
        'billing.Suscripcion',  # Suscripciones
        'billing.PagoSuscripcion',  # Pagos
        'billing.PaqueteCreditos',
        'billing.CompraPaqueteCreditos',
        'usuarios.User',  # Usuario de autenticación (Django User)
        'usuarios.FailedLoginAttempt',  # Brute force tracking
        'usuarios.ActiveJWTToken',  # Session management
        'usuarios.AuditLog',  # Audit log global
        'usuarios.PerfilUsuario',  # MOVED: Perfiles accesibles desde admin sin tenant
    ]

    # Tablas que van al schema del tenant actual
    TENANT_APPS = [
        'citas',
        'marketing',
        'guide',
        'reports',
    ]

    TENANT_MODELS = [
        'organizacion.Sede',  # Las sedes pertenecen al tenant
        # 'usuarios.PerfilUsuario',  # MOVED to SHARED_MODELS for admin access
        'usuarios.OnboardingProgress',
        # Todos los modelos de citas
        'citas.Servicio',
        'citas.Cita',
        'citas.Colaborador',
        # Marketing
        'marketing.CampaignMetrics',
        'marketing.ChannelPreference',
        # Etc.
    ]

    def _get_schema_for_model(self, model):
        """
        Determina si un modelo va al schema compartido (public) o al schema del tenant.
        """
        app_label = model._meta.app_label
        model_name = f"{app_label}.{model.__name__}"

        # 1. Verificar si la app completa es compartida
        if app_label in self.SHARED_APPS:
            return 'public'

        # 2. Verificar si el modelo específico es compartido
        if model_name in self.SHARED_MODELS:
            return 'public'

        # 3. Verificar si la app es de tenant
        if app_label in self.TENANT_APPS:
            org = get_current_organization()
            if org:
                return org.schema_name
            else:
                # No hay tenant activo - usar public por defecto
                logger.warning(
                    f"[TenantRouter] No tenant set for tenant model {model_name}. "
                    f"Using 'public' schema as fallback."
                )
                return 'public'

        # 4. Verificar si el modelo específico es de tenant
        if model_name in self.TENANT_MODELS:
            org = get_current_organization()
            if org:
                return org.schema_name
            else:
                logger.warning(
                    f"[TenantRouter] No tenant set for tenant model {model_name}. "
                    f"Using 'public' schema as fallback."
                )
                return 'public'

        # Por defecto: public
        return 'public'

    def db_for_read(self, model, **hints):
        """
        Determina qué base de datos usar para operaciones de lectura.
        """
        schema = self._get_schema_for_model(model)
        logger.debug(f"[TenantRouter] READ {model._meta.label} → schema '{schema}'")

        # Siempre usamos 'default' pero con SET search_path en el middleware
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Determina qué base de datos usar para operaciones de escritura.
        """
        schema = self._get_schema_for_model(model)
        logger.debug(f"[TenantRouter] WRITE {model._meta.label} → schema '{schema}'")

        # Siempre usamos 'default' pero con SET search_path en el middleware
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Permitir relaciones solo si están en el mismo schema.

        IMPORTANTE: Permitimos tenant → public (ej: Cita → User, Sede → Organizacion)
        porque los modelos del tenant necesitan referencias a modelos compartidos.
        """
        schema1 = self._get_schema_for_model(type(obj1))
        schema2 = self._get_schema_for_model(type(obj2))

        # Permitir relaciones entre mismo schema
        if schema1 == schema2:
            return True

        # Permitir relaciones de tenant → public (ej: Cita → User, Sede → Organizacion)
        if schema1 != 'public' and schema2 == 'public':
            return True

        # TAMBIÉN permitir public → tenant SOLO para User model
        # Esto permite asignar User a Cita desde el serializer
        from django.contrib.auth.models import User
        if type(obj1) == User or type(obj2) == User:
            return True

        # Denegar otras relaciones de public → tenant
        if schema1 == 'public' and schema2 != 'public':
            return False

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Determina si se permite ejecutar migraciones en esta base de datos.

        IMPORTANTE: Las migraciones se ejecutan de forma especial:
        1. Migraciones de tablas compartidas: python manage.py migrate --schema=public
        2. Migraciones de tablas tenant: python manage.py migrate_schemas
        """

        # Por ahora, permitir todas las migraciones en 'default'
        # La separación por schema se maneja con comandos personalizados
        return db == 'default'
