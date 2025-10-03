from django.core.management.base import BaseCommand
from citas.models import Colaborador
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Identifica colaboradores vinculados a usuarios que no deberían ser colaboradores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Desvincular usuarios de colaboradores (poner usuario=NULL)',
        )

    def handle(self, *args, **options):
        # Buscar colaboradores que tienen usuario vinculado
        colaboradores_con_usuario = Colaborador.all_objects.filter(
            usuario__isnull=False
        ).select_related('usuario', 'sede', 'sede__organizacion')

        if not colaboradores_con_usuario.exists():
            self.stdout.write(self.style.SUCCESS('✅ No hay colaboradores con usuarios vinculados'))
            return

        self.stdout.write(f'\n🔍 Encontrados {colaboradores_con_usuario.count()} colaboradores con usuario vinculado:\n')

        problematic = []
        for colab in colaboradores_con_usuario:
            user = colab.usuario
            # Verificar si el usuario es staff/superuser (estos SÍ deberían poder ser colaboradores)
            if user.is_staff or user.is_superuser:
                status = "✅ OK (es staff/superuser)"
            # Verificar si tiene sedes administradas (admin de sede)
            elif hasattr(user, 'perfil') and user.perfil.sedes_administradas.exists():
                status = "✅ OK (es admin de sede)"
            # Si no es ni staff ni admin de sede, probablemente es un cliente
            else:
                status = "⚠️ PROBLEMA (parece ser un cliente)"
                problematic.append(colab)

            self.stdout.write(
                f'  • Colaborador: {colab.nombre} (sede: {colab.sede.nombre})\n'
                f'    Usuario vinculado: {user.username} ({user.email})\n'
                f'    Estado: {status}\n'
            )

        if problematic:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️ {len(problematic)} colaboradores tienen usuarios vinculados que parecen ser clientes\n'
                )
            )

            if options['fix']:
                self.stdout.write(self.style.WARNING('\n🔧 Desvinculando usuarios de colaboradores...\n'))
                for colab in problematic:
                    old_user = colab.usuario
                    colab.usuario = None
                    colab.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Desvinculado: {colab.nombre} ya no está vinculado a {old_user.username}'
                        )
                    )
                self.stdout.write(
                    self.style.SUCCESS(f'\n✨ {len(problematic)} colaboradores corregidos')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '\n💡 Usa --fix para desvincular automáticamente estos usuarios'
                    )
                )
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Todos los colaboradores con usuario vinculado son válidos'))
