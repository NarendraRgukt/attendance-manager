from django.test import TestCase,Client
from shift.models import ShiftScheduleLog
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

# Create your tests here.

class ShiftScheduleLog(TestCase):
    def setUp(self) -> None:
        self.client=Client()
        payload={
            'username':'rgukt',
            'email':'rgukt@gmail.com',
            'password':'asdf@123',
            'first_name':'hello',
            'last_name':'hello'
        }
        self.user=get_user_model().objects.create_user(**payload)
        self.client.force_login(self.user)
    def test_remove_item(self):
        
        url=reverse('user-token')
        res=self.client.post(url,{'username':'rgukt','password':'asdf@123'})
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        