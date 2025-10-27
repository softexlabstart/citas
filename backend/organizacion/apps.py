from django.apps import AppConfig


class OrganizacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizacion'
    verbose_name = 'Organización'

    def ready(self):
        """
        Importar signals cuando la app esté lista.
        Esto registra los signals automáticos para provisión de tenants.
        """
        import organizacion.signals  # noqa
