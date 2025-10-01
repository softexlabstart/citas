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

        print(f"[OrganizacionManager] User: {user}, is_staff: {user.is_staff if user else None}, is_superuser: {user.is_superuser if user else None}")

        # Superusers and staff can see everything
        if user and (user.is_superuser or user.is_staff):
            print(f"[OrganizacionManager] User is staff/superuser, returning all queryset. Count: {queryset.count()}")
            return queryset

        organization = get_current_organization()
        print(f"[OrganizacionManager] Organization: {organization}")

        if organization:
            filter_kwargs = {self.organization_filter_path: organization}
            filtered_queryset = queryset.filter(**filter_kwargs)
            print(f"[OrganizacionManager] Filtered by organization. Count: {filtered_queryset.count()}")
            return filtered_queryset

        # Si no hay organización, devolver queryset vacío para seguridad
        print("[OrganizacionManager] No organization, returning empty queryset")
        return queryset.none()
