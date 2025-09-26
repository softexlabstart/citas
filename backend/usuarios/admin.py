from django.contrib import admin
from .models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_sede_nombre', 'organizacion')
    search_fields = ('user__username', 'sede__nombre', 'organizacion__nombre')
    list_filter = ('sede', 'organizacion')
    filter_horizontal = ('sedes_administradas',)

    def get_sede_nombre(self, obj):
        """
        Devuelve el nombre de la sede o un valor por defecto si no existe.
        """
        if obj.sede:
            return obj.sede.nombre
        return "Sin sede asignada"
    get_sede_nombre.short_description = 'Sede'
    get_sede_nombre.admin_order_field = 'sede__nombre'