from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import Cita, Servicio, Recurso, Sede
from usuarios.models import PerfilUsuario
from datetime import datetime, timedelta
import pytz

class CitaAPITests(APITestCase):

    def setUp(self):
        # Create Sedes
        self.sede1 = Sede.objects.create(nombre='Sede Principal', direccion='Calle 1')
        self.sede2 = Sede.objects.create(nombre='Sede Secundaria', direccion='Calle 2')

        # Create Users
        self.staff_user = User.objects.create_user(username='staff', password='password123', is_staff=True)
        self.admin_user = User.objects.create_user(username='admin_sede', password='password123')
        self.regular_user1 = User.objects.create_user(username='user1', password='password123')
        self.regular_user2 = User.objects.create_user(username='user2', password='password123')

        # Create Profiles
        self.perfil_admin = PerfilUsuario.objects.create(user=self.admin_user, is_sede_admin=True)
        self.perfil_admin.sedes_administradas.add(self.sede1)

        self.perfil_user1 = PerfilUsuario.objects.create(user=self.regular_user1, sede=self.sede1)
        self.perfil_user2 = PerfilUsuario.objects.create(user=self.regular_user2, sede=self.sede2)

        # Create Services and Resources
        self.servicio1 = Servicio.objects.create(nombre='Servicio 1', sede=self.sede1)
        self.recurso1 = Recurso.objects.create(nombre='Recurso 1', sede=self.sede1)

        self.servicio2 = Servicio.objects.create(nombre='Servicio 2', sede=self.sede2)
        self.recurso2 = Recurso.objects.create(nombre='Recurso 2', sede=self.sede2)

        # Create Appointments
        utc = pytz.UTC
        self.cita_user1 = Cita.objects.create(
            user=self.regular_user1, nombre='Cita User 1', fecha=datetime.now(utc) + timedelta(days=1),
            servicio=self.servicio1, sede=self.sede1
        )
        self.cita_user2 = Cita.objects.create(
            user=self.regular_user2, nombre='Cita User 2', fecha=datetime.now(utc) + timedelta(days=2),
            servicio=self.servicio2, sede=self.sede2
        )

        self.client = APIClient()

    def test_regular_user_permissions(self):
        """
        Ensure a regular user can only see their own appointments.
        """
        self.client.force_authenticate(user=self.regular_user1)
        response = self.client.get(reverse('cita-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.cita_user1.id)

    def test_sede_admin_permissions(self):
        """
        Ensure a Sede Admin can see all appointments in their managed sede, but not others.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('cita-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.cita_user1.id) # Sees cita from Sede 1

    def test_staff_user_permissions(self):
        """
        Ensure a staff user can see all appointments from all sedes.
        """
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(reverse('cita-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Sees both appointments

    def test_unauthenticated_access(self):
        """
        Ensure unauthenticated users cannot access the appointments list.
        """
        response = self.client.get(reverse('cita-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
