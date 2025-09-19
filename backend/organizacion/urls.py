app_name = 'organizacion' # Added app_name
from rest_framework.routers import DefaultRouter
from .views import SedeViewSet

router = DefaultRouter()
router.register(r'sedes', SedeViewSet)

urlpatterns = router.urls