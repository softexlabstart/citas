from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GuideSectionViewSet

router = DefaultRouter()
router.register(r'sections', GuideSectionViewSet, basename='guidesection')

urlpatterns = [
    path('', include(router.urls)),
]
