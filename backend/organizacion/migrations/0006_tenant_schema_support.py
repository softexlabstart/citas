# Generated manually - Database-per-tenant support
# This migration combines previous 0006 and 0007 to avoid conflicts
# Safe to run: all fields have null=True or default values

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0005_auto_20250925_1552'),  # Last common migration in server
    ]

    operations = [
        # From old 0006: Add slug field
        migrations.AddField(
            model_name='organizacion',
            name='slug',
            field=models.SlugField(blank=True, db_index=True, max_length=100, unique=True),
        ),

        # From old 0007: Add tenant schema fields
        migrations.AddField(
            model_name='organizacion',
            name='schema_name',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='PostgreSQL schema name for this tenant',
                max_length=63,
                unique=True
            ),
        ),
        migrations.AddField(
            model_name='organizacion',
            name='database_name',
            field=models.CharField(
                blank=True,
                help_text='Nombre de base de datos dedicada (solo para enterprise)',
                max_length=63,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='organizacion',
            name='is_active',
            field=models.BooleanField(
                db_index=True,
                default=True,
                help_text='Si está activo el tenant'
            ),
        ),
        migrations.AddField(
            model_name='organizacion',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='organizacion',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),

        # Ensure table name is correct
        migrations.AlterModelTable(
            name='organizacion',
            table='organizacion_organizacion',
        ),
    ]
