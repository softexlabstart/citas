from django.urls import path
from .views import LoginView, RegisterView, TimezoneView, UserDetailView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('timezones/', TimezoneView.as_view(), name='timezones'),
    path('auth/user/', UserDetailView.as_view(), name='user_detail'),
]
