"""
Migration to add database indexes for better query performance.
These indexes will significantly improve the performance of queries filtering by these fields.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('citas', '0002_alter_servicio_precio'),
    ]

    operations = [
        # Add indexes for Cita model - most frequently queried fields
        migrations.AddIndex(
            model_name='cita',
            index=models.Index(fields=['fecha'], name='cita_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='cita',
            index=models.Index(fields=['estado'], name='cita_estado_idx'),
        ),
        migrations.AddIndex(
            model_name='cita',
            index=models.Index(fields=['fecha', 'estado'], name='cita_fecha_estado_idx'),
        ),
        migrations.AddIndex(
            model_name='cita',
            index=models.Index(fields=['sede', 'fecha'], name='cita_sede_fecha_idx'),
        ),

        # Add indexes for Servicio model
        migrations.AddIndex(
            model_name='servicio',
            index=models.Index(fields=['sede'], name='servicio_sede_idx'),
        ),

        # Add indexes for Colaborador model
        migrations.AddIndex(
            model_name='colaborador',
            index=models.Index(fields=['sede'], name='colaborador_sede_idx'),
        ),

        # Add indexes for Bloqueo model
        migrations.AddIndex(
            model_name='bloqueo',
            index=models.Index(fields=['fecha_inicio', 'fecha_fin'], name='bloqueo_fechas_idx'),
        ),

        # Add indexes for Horario model
        migrations.AddIndex(
            model_name='horario',
            index=models.Index(fields=['dia_semana'], name='horario_dia_idx'),
        ),
    ]
