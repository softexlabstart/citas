from django.db import models
from django.utils.text import slugify


class GuideSection(models.Model):
    """
    Modelo para las secciones de la Guía de Usuario.
    Permite gestionar el contenido de la guía desde el Django Admin.
    """

    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('usuarios', 'Para Usuarios'),
        ('administradores', 'Para Administradores'),
        ('colaboradores', 'Para Colaboradores'),
    ]

    LANGUAGE_CHOICES = [
        ('es', 'Español'),
        ('en', 'English'),
    ]

    # Información básica
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título de la sección que aparecerá en el accordion'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        verbose_name='Slug',
        help_text='Se genera automáticamente del título'
    )

    # Contenido (HTML rico)
    content = models.TextField(
        verbose_name='Contenido',
        help_text='Contenido HTML de la sección. Puedes usar negrita, listas, imágenes, etc.'
    )

    # Organización
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name='Categoría',
        help_text='Categoría de la sección para agrupar contenido'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición (menor número aparece primero)'
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        default='QuestionCircle',
        verbose_name='Ícono',
        help_text='Nombre del ícono de Bootstrap Icons (ej: CalendarCheck, People, Gear)'
    )

    # Internacionalización
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='es',
        verbose_name='Idioma',
        db_index=True
    )

    # Multimedia (opcional)
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL de Video',
        help_text='URL de video de YouTube o Vimeo (opcional)'
    )

    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Solo las secciones activas se mostrarán en el frontend'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')

    class Meta:
        verbose_name = 'Sección de Guía'
        verbose_name_plural = 'Secciones de Guía'
        ordering = ['category', 'order', 'title']
        indexes = [
            models.Index(fields=['language', 'is_active', 'category']),
            models.Index(fields=['order']),
        ]

    def save(self, *args, **kwargs):
        """Generar slug automáticamente si no existe"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while GuideSection.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title} ({self.language.upper()})"
