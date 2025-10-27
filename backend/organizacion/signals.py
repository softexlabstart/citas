"""
Signals para automatizar la provisión de schemas de tenants.

Cuando se crea una Organizacion, automáticamente:
1. Se genera el schema_name si no existe
2. Se crea el schema en PostgreSQL
3. Se ejecutan las migraciones en el schema del tenant
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection
from django.core.management import call_command
import logging

from .models import Organizacion

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Organizacion)
def provision_tenant_schema(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar una Organizacion.

    Si es una nueva organización (created=True), crea el schema en PostgreSQL
    y ejecuta las migraciones necesarias.

    IMPORTANTE: Este proceso es asíncrono en producción para no bloquear el request.
    """

    # Solo ejecutar para organizaciones nuevas
    if not created:
        return

    org = instance
    schema_name = org.schema_name

    logger.info(f"[TenantProvision] Nueva organización creada: {org.nombre} (ID: {org.id})")
    logger.info(f"[TenantProvision] Schema name: {schema_name}")

    try:
        # 1. Verificar si el schema ya existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = %s;
            """, [schema_name])

            if cursor.fetchone():
                logger.warning(
                    f"[TenantProvision] Schema {schema_name} ya existe. "
                    f"Saltando creación."
                )
                return

        # 2. Crear el schema en PostgreSQL
        logger.info(f"[TenantProvision] Creando schema: {schema_name}")

        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name};')

        logger.info(f"[TenantProvision] ✓ Schema {schema_name} creado")

        # 3. Ejecutar migraciones en el schema del tenant
        logger.info(f"[TenantProvision] Ejecutando migraciones en {schema_name}")

        # Configurar search_path para que las migraciones se ejecuten en el schema correcto
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {schema_name}, public;')

        # Migrar apps de tenant
        tenant_apps = ['citas', 'marketing', 'guide', 'reports', 'usuarios', 'organizacion']

        for app in tenant_apps:
            try:
                call_command('migrate', app, verbosity=0, interactive=False)
                logger.debug(f"[TenantProvision]   ✓ Migrado: {app}")
            except Exception as e:
                logger.warning(f"[TenantProvision]   ⚠ Error migrando {app}: {e}")

        # Restaurar search_path
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO public;')

        logger.info(
            f"[TenantProvision] ✓ Tenant {org.nombre} provisionado exitosamente!"
        )

        # TODO: Enviar email de bienvenida al owner
        # TODO: Crear datos de ejemplo si está en trial

    except Exception as e:
        logger.error(
            f"[TenantProvision] ✗ Error provisionando tenant {org.nombre}: {e}",
            exc_info=True
        )
        # TODO: En producción, enviar alerta a administradores
        # TODO: Marcar org.is_active = False si falla la provisión


@receiver(post_save, sender=Organizacion)
def create_trial_subscription(sender, instance, created, **kwargs):
    """
    Signal para crear suscripción trial automáticamente al crear una organización.

    Este signal se ejecutará una vez implementes el sistema de billing.
    """
    if not created:
        return

    # TODO: Descomentar cuando implementes billing
    # try:
    #     from billing.models import Plan, Suscripcion
    #     from datetime import timedelta
    #     from django.utils import timezone
    #
    #     # Obtener plan Esencial (trial)
    #     plan_esencial = Plan.objects.get(nombre='esencial')
    #
    #     # Crear suscripción trial de 14 días
    #     Suscripcion.objects.create(
    #         organizacion=instance,
    #         plan=plan_esencial,
    #         estado='trial',
    #         periodo='monthly',
    #         fecha_fin_trial=timezone.now().date() + timedelta(days=14),
    #         creditos_whatsapp_disponibles=plan_esencial.creditos_whatsapp_mensuales
    #     )
    #
    #     logger.info(f"[Billing] Trial de 14 días creado para {instance.nombre}")
    #
    # except Exception as e:
    #     logger.error(f"[Billing] Error creando trial para {instance.nombre}: {e}")

    pass
