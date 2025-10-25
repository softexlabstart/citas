"""
Vistas públicas para el sistema de citas.
Permiten a usuarios no autenticados agendar citas como invitados.

SEGURIDAD: Implementa rate limiting para prevenir spam y ataques DoS.
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

# MULTI-TENANT: Import helper for profile management
from usuarios.utils import get_perfil_or_first

# SECURITY: Import custom throttles
from core.throttling import PublicBookingIPThrottle, PublicBookingEmailThrottle

logger = logging.getLogger(__name__)


class PublicCitaViewSet(viewsets.ModelViewSet):
    """
    Endpoint público para que invitados puedan agendar citas.
    No requiere autenticación.

    SEGURIDAD - Rate Limiting:
    - Por IP: Máximo 5 citas por hora (previene spam desde una IP)
    - Por Email: Máximo 3 citas por día (previene abuso de un mismo email)
    - Previene: spam, DoS, flooding de emails, saturación de BD

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

    # SECURITY: Rate limiting para prevenir spam y ataques DoS
    throttle_classes = [PublicBookingIPThrottle, PublicBookingEmailThrottle]

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
                user_created = False
                existing_users = User.objects.filter(email=email)

                # MULTI-TENANT: Buscar si existe un usuario con perfil en esta organización
                for existing_user in existing_users:
                    existing_perfil = existing_user.perfiles.filter(organizacion=organizacion).first()
                    if existing_perfil:
                        user = existing_user
                        logger.info(f"Usuario existente encontrado: {user.username} ({user.email}) en organización {organizacion.nombre}")
                        break

                # Si no existe usuario en esta organización, crear uno nuevo
                if not user:
                    # Generar username único
                    import hashlib
                    if existing_users.exists():
                        # Ya existe usuario con este email en otra org - usar username con hash
                        hash_suffix = hashlib.md5(organizacion.nombre.encode()).hexdigest()[:8]
                        username = f"{email.split('@')[0]}_{hash_suffix}"
                    else:
                        # Primera vez con este email - usar email como username
                        username = email

                    user, user_created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'first_name': cita.nombre.split()[0] if cita.nombre else 'Invitado'
                        }
                    )

                    if not user_created:
                        # El username ya existía (caso raro) - buscar si tiene perfil en esta org
                        user_perfil = user.perfiles.filter(organizacion=organizacion).first()
                        if user_perfil:
                            logger.info(f"Usuario con username {username} ya existe en esta organización")
                        else:
                            logger.warning(f"Usuario con username {username} existe pero sin perfil en esta organización")
                    else:
                        logger.info(f"Nuevo usuario creado: {username} ({email})")

                # MULTI-TENANT: Manejo del perfil del usuario
                if user_created or not user.perfiles.filter(organizacion=organizacion).exists():
                    # Usuario nuevo O usuario sin perfil en esta org: crear perfil con sede asignada
                    from usuarios.models import PerfilUsuario
                    perfil = PerfilUsuario.objects.create(
                        user=user,
                        organizacion=organizacion,
                        sede=cita.sede,
                        nombre=cita.nombre or 'Invitado',
                        telefono=cita.telefono_cliente or ''
                    )
                    # Agregar la sede a la relación M2M sedes
                    perfil.sedes.add(cita.sede)
                    logger.info(f"Perfil creado para usuario {user.email} con organización {organizacion.nombre} y sede {cita.sede.nombre}")
                else:
                    # Usuario YA existe con perfil en esta organización
                    # Obtener el perfil para esta organización específica
                    perfil_actual = user.perfiles.filter(organizacion=organizacion).first()
                    if perfil_actual:
                        # Agregar sede si no la tiene
                        if cita.sede not in perfil_actual.sedes.all():
                            perfil_actual.sedes.add(cita.sede)
                            logger.info(f"Sede {cita.sede.nombre} agregada al perfil de {user.email}")

                        # Actualizar sede principal si no tiene una asignada
                        if not perfil_actual.sede:
                            perfil_actual.sede = cita.sede
                            perfil_actual.save()
                            logger.info(f"Sede principal {cita.sede.nombre} asignada a {user.email}")

                        # Actualizar información si ha cambiado
                        updated = False
                        if cita.nombre and perfil_actual.nombre != cita.nombre:
                            perfil_actual.nombre = cita.nombre
                            updated = True
                        if cita.telefono_cliente and perfil_actual.telefono != cita.telefono_cliente:
                            perfil_actual.telefono = cita.telefono_cliente
                            updated = True
                        if updated:
                            perfil_actual.save()
                            logger.info(f"Información del perfil actualizada para {user.email}")

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
