from django.db import models
from .thread_locals import get_current_organization, get_current_user

class OrganizacionManager(models.Manager):
    """
    Custom manager that filters querysets by the current organization.
    It can be configured with the path to the organization field.
    """
    def __init__(self, *args, **kwargs):
        self.organization_filter_path = kwargs.pop('organization_filter_path', 'organizacion')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = get_current_user()

        if user and user.is_superuser:
            return queryset

        organization = get_current_organization()

        if organization:
            filter_kwargs = {self.organization_filter_path: organization}
            return queryset.filter(**filter_kwargs)

        # Si no hay organización, devolver queryset vacío para seguridad
        return queryset.none()
