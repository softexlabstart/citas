from rest_framework import viewsets
from .models import Sede
from .serializers import SedeSerializer

class SedeViewSet(viewsets.ModelViewSet):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
