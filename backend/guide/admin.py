from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import GuideSection


@admin.register(GuideSection)
class GuideSectionAdmin(admin.ModelAdmin):
    """
    Admin personalizado para GuideSection con editor de texto enriquecido.
    """

    list_display = ('title', 'category', 'language', 'order', 'is_active', 'updated_at')
    list_filter = ('category', 'language', 'is_active', 'created_at')
    search_fields = ('title', 'content', 'slug')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'slug', 'icon', 'category', 'language')
        }),
        ('Contenido', {
            'fields': ('content',),
            'description': 'Puedes usar HTML: <strong>negrita</strong>, <em>cursiva</em>, <ul><li>listas</li></ul>, etc.'
        }),
        ('Organización', {
            'fields': ('order', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Multimedia (Opcional)', {
            'fields': ('video_url',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    # Usar un textarea más grande para el contenido
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 20, 'cols': 100, 'style': 'font-family: monospace;'})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Ordenar por categoría y orden
        return qs.order_by('category', 'order')

    class Media:
        css = {
            'all': ('admin/css/custom_guide_admin.css',)
        }
        js = ('admin/js/guide_admin.js',)


# Personalización del sitio admin
admin.site.site_header = "Sistema de Citas - Administración"
admin.site.site_title = "Admin Sistema de Citas"
admin.site.index_title = "Panel de Administración"
