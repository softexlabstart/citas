from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import PerfilUsuario
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=PerfilUsuario)
def auto_assign_organizacion_from_sede(sender, instance, **kwargs):
    """
    Signal que asigna automáticamente la organización al perfil del usuario
    cuando se asigna una sede, si no tiene organización asignada.

    Esto asegura que los usuarios siempre tengan organización cuando tienen sede.
    """
    # Si tiene sede pero no tiene organización, asignar la organización de la sede
    if instance.sede and not instance.organizacion:
        instance.organizacion = instance.sede.organizacion
        logger.info(f"Auto-asignando organización {instance.organizacion} al usuario {instance.user.username} desde la sede {instance.sede}")
