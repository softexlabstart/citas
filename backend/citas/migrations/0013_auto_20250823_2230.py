from django.db import migrations, models
import django.db.models.deletion

def assign_default_sede(apps, schema_editor):
    Sede = apps.get_model('organizacion', 'Sede')
    default_sede, created = Sede.objects.get_or_create(nombre='Sede por defecto', defaults={'direccion': 'Dirección por defecto'})

    Cita = apps.get_model('citas', 'Cita')
    Cita.objects.filter(sede__isnull=True).update(sede=default_sede)

    Horario = apps.get_model('citas', 'Horario')
    Horario.objects.filter(sede__isnull=True).update(sede=default_sede)

    Recurso = apps.get_model('citas', 'Recurso')
    Recurso.objects.filter(sede__isnull=True).update(sede=default_sede)

    Servicio = apps.get_model('citas', 'Servicio')
    Servicio.objects.filter(sede__isnull=True).update(sede=default_sede)


class Migration(migrations.Migration):

    dependencies = [
        ('citas', '0012_cita_sede_horario_sede_recurso_sede_servicio_sede'),
        ('organizacion', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(assign_default_sede),

        migrations.AlterField(
            model_name='cita',
            name='sede',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citas', to='organizacion.sede'),
        ),
        migrations.AlterField(
            model_name='horario',
            name='sede',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='horarios', to='organizacion.sede'),
        ),
        migrations.AlterField(
            model_name='recurso',
            name='sede',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recursos', to='organizacion.sede'),
        ),
        migrations.AlterField(
            model_name='servicio',
            name='sede',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='servicios', to='organizacion.sede'),
        ),
    ]
