from django.urls import path
from .views import FinancialSummaryView

app_name = 'reports'

urlpatterns = [
    path('financial-summary/', FinancialSummaryView.as_view(), name='financial-summary'),
]
