"""
Vistas públicas para el sistema de citas.
Permiten a usuarios no autenticados agendar citas como invitados.
"""
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
import logging

from .models import Cita
from .serializers import GuestCitaSerializer
from usuarios.models import MagicLinkToken

logger = logging.getLogger(__name__)


class PublicCitaViewSet(viewsets.ModelViewSet):
    """
    Endpoint público para que invitados puedan agendar citas.
    No requiere autenticación.

    POST /api/citas/public-booking/
    {
        "nombre": "Juan Pérez",
        "email_cliente": "juan@example.com",
        "telefono_cliente": "+57123456789",
        "fecha": "2025-10-05T10:00:00Z",
        "servicios_ids": [1, 2],
        "colaboradores_ids": [1],
        "sede_id": 1,
        "comentario": "Comentario opcional"
    }
    """
    queryset = Cita.objects.all()
    serializer_class = GuestCitaSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']  # Solo permitir POST (crear citas)

    def create(self, request, *args, **kwargs):
        """
        Crea una cita para un invitado y envía un magic link por email.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Crear la cita
        cita = serializer.save()

        # Enviar magic link automáticamente
        email = cita.email_cliente
        if email:
            try:
                from usuarios.models import PerfilUsuario
                organizacion = cita.sede.organizacion

                # Buscar usuario con este email que ya tenga perfil en esta organización
                user = None
                existing_users = User.objects.filter(email=email)

                for existing_user in existing_users:
                    if hasattr(existing_user, 'perfil') and existing_user.perfil.organizacion == organizacion:
                        user = existing_user
                        created = False
                        break

                # Si no existe, crear nuevo usuario
                if not user:
                    # Generar username único
                    import hashlib
                    if existing_users.exists():
                        # Ya existe usuario con este email en otra org
                        hash_suffix = hashlib.md5(organizacion.nombre.encode()).hexdigest()[:8]
                        username = f"{email.split('@')[0]}_{hash_suffix}"
                    else:
                        # Primera vez con este email
                        username = email

                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'first_name': cita.nombre.split()[0] if cita.nombre else 'Invitado'
                        }
                    )
                else:
                    created = False

                if created:
                    # Usuario nuevo: crear perfil
                    PerfilUsuario.objects.create(
                        usuario=user,
                        organizacion=organizacion,
                        nombre=cita.nombre or 'Invitado',
                        telefono=cita.telefono_cliente or ''
                    )
                    logger.info(f"Perfil creado para usuario {user.email} con organización {organizacion.nombre}")
                else:
                    # Usuario existente con ese email
                    if hasattr(user, 'perfil') and user.perfil is not None:
                        if user.perfil.organizacion != organizacion:
                            # Usuario existe en OTRA organización - crear nuevo usuario con username único
                            import hashlib
                            hash_suffix = hashlib.md5(organizacion.nombre.encode()).hexdigest()[:8]
                            new_username = f"{email.split('@')[0]}_{hash_suffix}"

                            user, user_created = User.objects.get_or_create(
                                username=new_username,
                                defaults={
                                    'email': email,
                                    'first_name': cita.nombre.split()[0] if cita.nombre else 'Invitado'
                                }
                            )

                            if user_created:
                                PerfilUsuario.objects.create(
                                    usuario=user,
                                    organizacion=organizacion,
                                    nombre=cita.nombre or 'Invitado',
                                    telefono=cita.telefono_cliente or ''
                                )
                                logger.info(f"Nuevo usuario '{new_username}' creado para {email} en {organizacion.nombre}")
                        # Si es la misma organización, usar el usuario existente
                    else:
                        # Usuario sin perfil: crear perfil
                        PerfilUsuario.objects.create(
                            usuario=user,
                            organizacion=organizacion,
                            nombre=cita.nombre or user.first_name or 'Invitado',
                            telefono=cita.telefono_cliente or ''
                        )
                        logger.info(f"Perfil creado para {user.email} en {organizacion.nombre}")

                # Asociar el usuario a la cita si no está ya asociado
                if not cita.user:
                    cita.user = user
                    cita.save()

                # Eliminar tokens antiguos y crear uno nuevo
                MagicLinkToken.objects.filter(user=user).delete()
                magic_token = MagicLinkToken.objects.create(user=user)

                # Construir el enlace mágico
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                magic_link = f"{frontend_url}/magic-link-auth?token={magic_token.token}"

                # Preparar mensaje de email
                servicios_nombres = ', '.join([s.nombre for s in cita.servicios.all()])
                fecha_formateada = cita.fecha.strftime('%d/%m/%Y a las %H:%M')

                subject = f'Cita Confirmada - {cita.sede.nombre}'
                message = f"""
Hola {cita.nombre},

¡Tu cita ha sido confirmada exitosamente!

📅 Fecha: {fecha_formateada}
📍 Sede: {cita.sede.nombre}
💼 Servicios: {servicios_nombres}

Para ver los detalles de tu cita y tu historial completo, haz clic en el siguiente enlace:

{magic_link}

Este enlace es válido por 15 minutos y solo puede usarse una vez.

Si no solicitaste esta cita, puedes ignorar este correo.

¡Nos vemos pronto!
Equipo de {getattr(settings, 'SITE_NAME', 'Citas')}
                """.strip()

                # Enviar email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    recipient_list=[email],
                    fail_silently=True
                )

                logger.info(f"Cita creada y magic link enviado a {email} (ID cita: {cita.id})")

            except Exception as e:
                logger.error(f"Error enviando magic link para cita {cita.id}: {str(e)}")
                # No fallar la creación de la cita si el email falla

        return Response(
            {
                **serializer.data,
                'message': 'Cita creada exitosamente. Se ha enviado un enlace a tu email para ver tus citas.'
            },
            status=status.HTTP_201_CREATED
        )
