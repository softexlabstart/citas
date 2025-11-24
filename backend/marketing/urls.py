from django.urls import path
from .views import SendMarketingEmailView, SendMarketingWhatsAppView

app_name = 'marketing'

urlpatterns = [
    path('send-email/', SendMarketingEmailView.as_view(), name='send_marketing_email'),
    path('send-whatsapp/', SendMarketingWhatsAppView.as_view(), name='send_marketing_whatsapp'),
]
