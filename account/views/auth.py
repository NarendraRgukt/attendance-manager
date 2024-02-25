from django.shortcuts import render
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from account import serializers
from rest_framework import status


class UserTokenView(ObtainAuthToken):
    serializer_class = serializers.UserTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)



        
        email = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user = authenticate(request=request, username=email, password=password)
 


        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'username': user.username,'uuid':user.uuid}, status=status.HTTP_200_OK)

        else:
            return Response({'error':"Invalid username or password"},status=status.HTTP_401_UNAUTHORIZED)