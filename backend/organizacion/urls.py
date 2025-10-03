from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SedeViewSet, CreateOrganizacionView, OrganizacionPublicView

app_name = 'organizacion'

router = DefaultRouter()
router.register(r'sedes', SedeViewSet, basename='sede')

urlpatterns = router.urls + [
    path('organizaciones/', CreateOrganizacionView.as_view(), name='crear-organizacion'),
    path('organizaciones/<slug:slug>/', OrganizacionPublicView.as_view(), name='organizacion-public'),
]