from django.db import migrations, models
import django.db.models.deletion

def assign_default_recurso(apps, schema_editor):
    Horario = apps.get_model('citas', 'Horario')
    Recurso = apps.get_model('citas', 'Recurso')
    default_recurso, created = Recurso.objects.get_or_create(nombre='Recurso por defecto', defaults={'descripcion': 'Recurso temporal creado por migración'})
    Horario.objects.filter(recurso__isnull=True).update(recurso=default_recurso)


class Migration(migrations.Migration):

    dependencies = [
        ('citas', '0010_remove_horario_user_remove_recurso_horarios_and_more'),
    ]

    operations = [
        migrations.RunPython(assign_default_recurso),
        migrations.AlterField(
            model_name='horario',
            name='recurso',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='horarios', to='citas.recurso'),
        ),
    ]