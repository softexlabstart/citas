from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import OnboardingProgress
from .serializers import OnboardingProgressSerializer


class OnboardingProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el progreso del onboarding de usuarios.

    Endpoints:
    - GET /api/onboarding/progress/ - Ver progreso actual del usuario
    - PATCH /api/onboarding/progress/{id}/ - Actualizar progreso
    - POST /api/onboarding/progress/dismiss/ - Marcar como cerrado/saltado
    - POST /api/onboarding/progress/complete/ - Marcar como completado
    - POST /api/onboarding/progress/mark_step/ - Marcar un paso específico
    """
    serializer_class = OnboardingProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo permite ver el progreso del usuario autenticado"""
        return OnboardingProgress.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        Retorna el progreso del usuario actual.
        Si no existe, lo crea automáticamente.
        """
        progress, created = OnboardingProgress.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(progress)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def dismiss(self, request):
        """Marca el onboarding como cerrado (usuario decidió saltarlo)"""
        progress, created = OnboardingProgress.objects.get_or_create(
            user=request.user
        )
        progress.is_dismissed = True
        progress.save()

        serializer = self.get_serializer(progress)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def complete(self, request):
        """Marca el onboarding como completado"""
        progress, created = OnboardingProgress.objects.get_or_create(
            user=request.user
        )
        progress.mark_as_completed()

        serializer = self.get_serializer(progress)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_step(self, request):
        """
        Marca un paso específico como completado.

        Body: {
            "step": "has_created_service" | "has_added_collaborator" |
                    "has_viewed_public_link" | "has_completed_profile"
        }
        """
        progress, created = OnboardingProgress.objects.get_or_create(
            user=request.user
        )

        step = request.data.get('step')

        valid_steps = [
            'has_created_service',
            'has_added_collaborator',
            'has_viewed_public_link',
            'has_completed_profile'
        ]

        if step not in valid_steps:
            return Response(
                {'error': f'Paso inválido. Debe ser uno de: {", ".join(valid_steps)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Marcar el paso como completado
        setattr(progress, step, True)
        progress.save()

        # Auto-completar onboarding si todos los pasos esenciales están hechos
        if progress.has_created_service and not progress.is_completed:
            # Solo requiere haber creado al menos un servicio para considerar completo
            # Los demás son opcionales
            if progress.completion_percentage >= 50:  # Al menos 50% completo
                progress.mark_as_completed()

        serializer = self.get_serializer(progress)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def reset(self, request):
        """Reinicia el progreso del onboarding (útil para testing)"""
        progress, created = OnboardingProgress.objects.get_or_create(
            user=request.user
        )

        progress.has_created_service = False
        progress.has_added_collaborator = False
        progress.has_viewed_public_link = False
        progress.has_completed_profile = False
        progress.is_completed = False
        progress.is_dismissed = False
        progress.completed_at = None
        progress.save()

        serializer = self.get_serializer(progress)
        return Response(serializer.data)
