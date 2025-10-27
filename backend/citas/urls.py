# citas/urls.py
app_name = 'citas' # Added app_name
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (ServicioViewSet, CitaViewSet, HorarioViewSet,
                    AppointmentReportView, DisponibilidadView, RecursoViewSet,
                    SedeReportView, BloqueoViewSet, DashboardSummaryView,
                    NextAvailabilityView, RecursoCitaViewSet, ColaboradorViewSet)
from .views_public import PublicCitaViewSet, InvitadoCitaView

router = DefaultRouter()
router.register(r'servicios', ServicioViewSet, basename='servicio')
router.register(r'citas', CitaViewSet)
router.register(r'horarios', HorarioViewSet)
router.register(r'recursos', RecursoViewSet, basename='recurso')
router.register(r'colaboradores', ColaboradorViewSet, basename='colaborador')
router.register(r'bloqueos', BloqueoViewSet)
router.register(r'recurso-citas', RecursoCitaViewSet, basename='recurso-cita')

urlpatterns = [
    path('reports/appointments/', AppointmentReportView.as_view(), name='appointment-reports'),
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('reports/sede_summary/', SedeReportView.as_view(), name='sede-reports-summary'),
    path('next-availability/', NextAvailabilityView.as_view(), name='next-availability'),
    path('disponibilidad/', DisponibilidadView.as_view(), name='disponibilidad'),
    # Endpoints públicos para reservas de invitados
    path('public-booking/', PublicCitaViewSet.as_view({'post': 'create'}), name='public-booking'),
    path('invitado/<int:cita_id>/', InvitadoCitaView.as_view(), name='invitado-cita'),
    path('', include(router.urls)),
]
