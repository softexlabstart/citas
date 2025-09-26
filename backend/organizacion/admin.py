from django.contrib import admin
from .models import Organizacion, Sede

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
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            organizacion = request.user.perfil.organizacion
            if organizacion:
                return qs.filter(organizacion=organizacion)
            return qs.none()
        except AttributeError:
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Restrict the 'organizacion' dropdown in the Sede form
        if db_field.name == "organizacion" and not request.user.is_superuser:
            try:
                user_org = request.user.perfil.organizacion
                if user_org:
                    kwargs["queryset"] = Organizacion.objects.filter(pk=user_org.pk)
            except (AttributeError, Organizacion.DoesNotExist):
                kwargs["queryset"] = Organizacion.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
