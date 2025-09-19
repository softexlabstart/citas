from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, RegisterView, TimezoneView, UserDetailView, ClientViewSet, ClientEmailListView

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('timezones/', TimezoneView.as_view(), name='timezones'),
    path('auth/user/', UserDetailView.as_view(), name='user_detail'),
    path('auth/user/personal-data/', UserDetailView.as_view({'get': 'get_personal_data'}), name='user_personal_data'), # New URL for personal data
    path('auth/user/delete-account/', UserDetailView.as_view({'delete': 'delete_my_account'}), name='user_delete_account'), # New URL for deleting account
    path('client-emails/', ClientEmailListView.as_view(), name='client_emails'),
]
