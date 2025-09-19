app_name = 'usuarios'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, RegisterView, TimezoneView, UserDetailView, ClientViewSet, ClientEmailListView, PersonalDataView, DeleteAccountView

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('timezones/', TimezoneView.as_view(), name='timezones'),
    path('auth/user/', UserDetailView.as_view(), name='user_detail'),
    path('auth/user/personal-data/', PersonalDataView.as_view(), name='user_personal_data'), # New URL for personal data
    path('auth/user/delete-account/', DeleteAccountView.as_view(), name='user_delete_account'), # New URL for deleting account
    path('client-emails/', ClientEmailListView.as_view(), name='client_emails'),
]