from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.views import MyTokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static
from citas.views import WelcomeView

urlpatterns = [
    path('', WelcomeView.as_view(), name='api-root-welcome'),
    path('admin/', admin.site.urls),
    path('api/citas/', include('citas.urls')),
    path('api/', include('usuarios.urls')),
    path('api/organizacion/', include('organizacion.urls')),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
