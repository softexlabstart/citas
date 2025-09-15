from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, RegisterView, TimezoneView, UserDetailView, ClientViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('timezones/', TimezoneView.as_view(), name='timezones'),
    path('auth/user/', UserDetailView.as_view(), name='user_detail'),
]
