from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from roles.permissions import AdminPermission
from roles.models import Member
from frimage import serializers,models
import base64
from django.core.files.base import ContentFile

class AllFrImageAPI(APIView):
    serializer_class=serializers.FrImageSerializer
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsAuthenticated]
    def get_queryset(self):
        member=Member.objects.filter(user=self.request.user,role__name="admin").exists()
        if member:
            return models.FRImage.objects.all()
        else:
            return models.FRImage.objects.filter(member__user=self.request.user)
    def get(self,request,*args,**kwargs):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        serializer=self.serializer_class(self.get_queryset(),many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request,*args,**kwargs):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_data=serializer.validated_data.get("image")
        format,image_encode=image_data.split(";base64,")
        image_file=base64.b64decode(image_encode)
        extension=format.split('/')[-1]
        file_name=f'image.{extension}'
        image=ContentFile(image_file,name=file_name)
        serializer.save(image=image)
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    
class FriImageAPI(APIView):
    serializer_class=serializers.FrImageSerializer
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsAuthenticated]

    def put(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        fri_image=get_object_or_404(models.FRImage,uuid=uuid)
        serializer=self.serializer_class(fri_image,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def delete(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        fri_image=get_object_or_404(models.FRImage,uuid=uuid)
        fri_image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



