from django.contrib import admin
from .models import PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'sede')
    search_fields = ('user__username', 'sede__nombre')
    filter_horizontal = ('sedes_administradas',) # To manage ManyToManyField