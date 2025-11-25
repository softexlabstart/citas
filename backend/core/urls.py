from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.views import MyTokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static
from citas.views import WelcomeView
from organizacion.admin_dashboard import admin_dashboard

urlpatterns = [
    path('', WelcomeView.as_view(), name='api-root-welcome'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/', admin.site.urls),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/citas/', include('citas.urls', namespace='citas')),
    path('api/organizacion/', include('organizacion.urls', namespace='organizacion')),
    path('api/marketing/', include('marketing.urls', namespace='marketing')),
    path('api/guide/', include('guide.urls')),
    path('api/reports/', include('reports.urls', namespace='reports')),
    path('api/', include('usuarios.urls', namespace='usuarios')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
