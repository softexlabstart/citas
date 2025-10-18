app_name = 'usuarios'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, RegisterView, RegisterByOrganizacionView, TimezoneView, UserDetailView, ClientViewSet, ClientEmailListView, PersonalDataView, DeleteAccountView, MultiTenantRegistrationView, OrganizationManagementView, InvitationView, AcceptInvitationView, OrganizationMembersView, RequestHistoryLinkView, AccessHistoryWithTokenView
from .views_password_reset import RequestPasswordResetView, ConfirmPasswordResetView
from .views_onboarding import OnboardingProgressViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'onboarding/progress', OnboardingProgressViewSet, basename='onboarding-progress')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('register/<slug:organizacion_slug>/', RegisterByOrganizacionView.as_view(), name='register_by_organization'),
    path('register-organization/', MultiTenantRegistrationView.as_view(), name='register_organization'),
    path('timezones/', TimezoneView.as_view(), name='timezones'),
    path('auth/user/', UserDetailView.as_view(), name='user_detail'),
    path('auth/user/personal-data/', PersonalDataView.as_view(), name='user_personal_data'), # New URL for personal data
    path('auth/user/delete-account/', DeleteAccountView.as_view(), name='user_delete_account'), # New URL for deleting account
    path('client-emails/', ClientEmailListView.as_view(), name='client_emails'),
    # URLs para gestión multi-tenant
    path('organization/', OrganizationManagementView.as_view(), name='organization_management'),
    path('organization/members/', OrganizationMembersView.as_view(), name='organization_members'),
    path('organization/invite/', InvitationView.as_view(), name='organization_invite'),
    path('invitations/<uuid:token>/', AcceptInvitationView.as_view(), name='accept_invitation'),
    # URLs para Magic Link
    path('auth/request-history-link/', RequestHistoryLinkView.as_view(), name='request_history_link'),
    path('auth/access-history-with-token/', AccessHistoryWithTokenView.as_view(), name='access_history_with_token'),
    # URLs para Password Reset
    path('auth/request-password-reset/', RequestPasswordResetView.as_view(), name='request_password_reset'),
    path('auth/confirm-password-reset/', ConfirmPasswordResetView.as_view(), name='confirm_password_reset'),
]