from django.contrib import admin
from .models import Organizacion, Sede

# MULTI-TENANT: Import helper for profile management
from usuarios.utils import get_perfil_or_first

@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

    # Only superusers can see and manage organizations
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'organizacion', 'direccion', 'telefono')
    list_filter = ('organizacion__nombre',)
    search_fields = ('nombre', 'direccion', 'organizacion__nombre')
    list_select_related = ('organizacion',)

    def get_queryset(self, request):
        # Use all_objects to bypass the default OrganizacionManager
        qs = self.model.all_objects.all()
        if request.user.is_superuser:
            return qs

        # MULTI-TENANT: Usar helper para obtener perfil
        perfil = get_perfil_or_first(request.user)
        if perfil and perfil.organizacion:
            return qs.filter(organizacion=perfil.organizacion)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Restrict the 'organizacion' dropdown in the Sede form
        if db_field.name == "organizacion" and not request.user.is_superuser:
            # MULTI-TENANT: Usar helper para obtener perfil
            perfil = get_perfil_or_first(request.user)
            if perfil and perfil.organizacion:
                kwargs["queryset"] = Organizacion.objects.filter(pk=perfil.organizacion.pk)
            else:
                kwargs["queryset"] = Organizacion.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
