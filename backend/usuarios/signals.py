from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)
    else:
        try:
            instance.perfil.save()
        except PerfilUsuario.DoesNotExist:
            PerfilUsuario.objects.create(user=instance)
