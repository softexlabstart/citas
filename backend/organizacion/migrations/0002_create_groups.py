from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='SedeAdmin')

class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]