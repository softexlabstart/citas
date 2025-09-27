from django.contrib import admin
from .models import PerfilUsuario
from organizacion.models import Sede, Organizacion


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_sede_nombre', 'organizacion')
    search_fields = ('user__username',)
    list_filter = ('sede', 'organizacion')
    filter_horizontal = ('sedes_administradas',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            organizacion = request.user.perfil.organizacion
            if organizacion:
                return qs.filter(organizacion=organizacion)
            return qs.none()
        except (AttributeError, PerfilUsuario.DoesNotExist):
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            try:
                organizacion = request.user.perfil.organizacion
                if organizacion:
                    if db_field.name == "sede":
                        kwargs["queryset"] = Sede.all_objects.filter(organizacion=organizacion)
                    if db_field.name == "organizacion":
                        kwargs["queryset"] = Organizacion.objects.filter(pk=organizacion.pk)
                else:
                    if db_field.name in ["sede", "organizacion"]:
                        kwargs["queryset"] = Sede.all_objects.none()
            except (AttributeError, PerfilUsuario.DoesNotExist):
                if db_field.name in ["sede", "organizacion"]:
                    kwargs["queryset"] = Sede.all_objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            try:
                organizacion = request.user.perfil.organizacion
                if organizacion and db_field.name == "sedes_administradas":
                    kwargs["queryset"] = Sede.all_objects.filter(organizacion=organizacion)
                else:
                    kwargs["queryset"] = Sede.all_objects.none()
            except (AttributeError, PerfilUsuario.DoesNotExist):
                kwargs["queryset"] = Sede.all_objects.none()
        
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_sede_nombre(self, obj):
        """
        Devuelve el nombre de la sede o un valor por defecto si no existe.
        """
        if obj.sede:
            return obj.sede.nombre
        return "Sin sede asignada"
    get_sede_nombre.short_description = 'Sede'