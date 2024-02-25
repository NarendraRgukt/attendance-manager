from django.shortcuts import render
from roles import serializers,models
from roles.permissions import AdminPermission
from rest_framework import permissions,authentication
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model,authenticate
from django.db.models import Q,Value
from django.db.models.functions import Concat
from django.db import IntegrityError
from roles.models import Member,ExportRequest
from roles.tasks import export_request
from roles.serializers import ExportRequestSerializer

from rest_framework.views import APIView
from django.shortcuts import redirect
import os
from django.conf import settings
from django.http import FileResponse
from shift.tasks import schedule_shifts
from shift.models import ShiftScheduleLog,Shift
from django.utils import timezone
from account.models import User


class AllMemberAPI(APIView):
    serializer_class=serializers.MemberUserSerializer
    permission_classes=[permissions.IsAuthenticated,AdminPermission]
    authentication_classes=[authentication.TokenAuthentication]

    def get_queryset(self):

            
        queryset=models.Member.objects.all()
        return queryset
    
    def get_serializer_class(self):
        if self.request.method=="GET":
            return serializers.MemberSerializer
        else:
            return self.serializer_class
    
    

    def get(self,request,*args,**kwargs):
        schedule_shifts.apply_async()
        member=Member.objects.filter(user=request.user,role__name="admin")
        if not member.exists():
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        export=request.GET.get('export')
        role_uuid=request.GET.get('role')
        query=Q()
        if role_uuid:
            query=Q(role__uuid=role_uuid)
        if export:
            uuid_lists=Member.objects.all().values('uuid')
            uuid_lists=uuid_lists.filter(query)

            uuids=[]
            for uuid_dict in uuid_lists:
                uuid=uuid_dict.get('uuid')
                print(uuid)
                uuids.append(str(uuid))
            content={
                'model':'Member',
                'uuid':uuids
            }
            print(uuids)
            print(content)
            if len(uuids)==0:
                return Response({'message:No objects in the database'},status=status.HTTP_404_NOT_FOUND)
            export_request_obj=ExportRequest.objects.create(member=member.first(),content=content,status="pending")
            serializer=ExportRequestSerializer(export_request_obj)
            export_request.apply_async()
            return Response(serializer.data,status=status.HTTP_201_CREATED)

        serializer_class = self.get_serializer_class() 
        serializer = serializer_class(self.get_queryset(), many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self,request,*args,**kwargs):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        serializer_class=self.get_serializer_class()
        serializer=serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        organization = serializer.validated_data.get('organization')
        print(organization)
        print(organization.shift_default,"this is shift")
        role = serializer.validated_data.get('role')
        first_name = serializer.validated_data.get('first_name')
        last_name= serializer.validated_data.get('last_name')

        shift=Shift.objects.get(uuid=organization.shift_default.uuid)
        try:
            user=get_user_model().objects.get(username=username,email=email)
            try:  
                member_check=models.Member.objects.get(organization=organization,user=user)
                if member_check:
                    return Response({'message':'You are already registered to this organization'},status=status.HTTP_400_BAD_REQUEST)
            except  models.Member.DoesNotExist:
                member=models.Member.objects.create(user=user, organization=organization, role=role)
                member.save()
                
                shift_schedule=ShiftScheduleLog.objects.create(member=member,shift=shift,start_date=timezone.now().date(),organization=organization)
                shift_schedule.save()
                return Response(serializer.data,status=status.HTTP_201_CREATED)     
        except User.DoesNotExist:

                user = get_user_model().objects.create_user(username=username, email=email,first_name=first_name,last_name=last_name)
                user.set_password(password)
                user.save()
                member=models.Member.objects.create(user=user, organization=organization, role=role)
                shift_schedule=ShiftScheduleLog.objects.create(member=member,shift=organization.shift_default,start_date=timezone.now().date(),organization=organization)
                shift_schedule.save()
                member.save()        
                return Response(serializer.data,status=status.HTTP_201_CREATED)
        


class MemberAPI(APIView):
    serializer_class=serializers.MemberSerializer
    permission_classes=[permissions.IsAuthenticated]
    authentication_classes=[authentication.TokenAuthentication]

    def put(self,request,uuid):
        try:
            member=Member.objects.filter(user=request.user,role__name="admin").exists()
            if not member:
                return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
            member=models.Member.objects.get(uuid=uuid)
            serializer=self.serializer_class(member,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)

        except models.Member.DoesNotExist:
            return Response({'message':'Member does not found'},status=status.HTTP_404_NOT_FOUND)
        
    def delete(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        try:
            member=models.Member.objects.get(uuid=uuid)
            user=get_user_model().objects.filter(member__uuid=member.uuid).first()
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except models.Member.DoesNotExist:
            return Response({'message':'member does not found'},status=status.HTTP_404_NOT_FOUND)

class AllExportRequest(APIView):
    serializer_class=ExportRequestSerializer
    permission_classes=[permissions.IsAuthenticated]
    authentication_classes=[authentication.TokenAuthentication]

    def get(self,request,uuid,*args,**kwargs):
        try:
            export_request=ExportRequest.objects.get(uuid=uuid)
        except ExportRequest.DoesNotExist:
            return Response({'message':'The export request is not found'},status=status.HTTP_404_NOT_FOUND)
        serializer=self.serializer_class(export_request)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
class ExportRequestDownload(APIView):
    permission_classes=[permissions.IsAuthenticated]
    authentication_classes=[authentication.TokenAuthentication]

    def get(self,request,filename):
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            return response
        else:
            return Response({'message':'The export request is not found'},status=status.HTTP_404_NOT_FOUND)
            
        
