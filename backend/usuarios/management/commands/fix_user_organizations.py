from django.core.management.base import BaseCommand
from usuarios.models import PerfilUsuario


class Command(BaseCommand):
    help = 'Asigna automáticamente la organización a usuarios que tienen sede pero no organización'

    def handle(self, *args, **options):
        # Buscar perfiles que tienen sede pero no organización
        perfiles_sin_org = PerfilUsuario.objects.filter(
            sede__isnull=False,
            organizacion__isnull=True
        ).select_related('sede', 'sede__organizacion', 'user')

        count = perfiles_sin_org.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('✅ Todos los usuarios con sede ya tienen organización asignada'))
            return

        self.stdout.write(f'🔍 Encontrados {count} usuarios con sede pero sin organización')

        for perfil in perfiles_sin_org:
            org = perfil.sede.organizacion
            perfil.organizacion = org
            perfil.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Usuario "{perfil.user.username}" ({perfil.user.email}) '
                    f'ahora pertenece a la organización "{org.nombre}" desde la sede "{perfil.sede.nombre}"'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n✨ {count} usuarios actualizados correctamente')
        )
