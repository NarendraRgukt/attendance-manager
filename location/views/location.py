from django.shortcuts import render,get_object_or_404

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from roles.permissions import AdminPermission
from roles.models import Member
from location import serialilzers
from location.models import SystemLocation,LocationSettings
from shift.models import ShiftScheduleLog,Shift
from datetime import datetime,timedelta


class AllSystemLocationAPI(APIView):
    serializer_class=serialilzers.SystemLocationSerializer
    permission_classes=[IsAuthenticated,AdminPermission]
    authentication_classes=[TokenAuthentication]
    

    def get(self,request,*args,**kwargs):
        queryset=SystemLocation.objects.all()
        serializer=self.serializer_class(queryset,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request,*args,**kwargs):
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    

class SystemLocationAPI(APIView):
    serializer_class=serialilzers.SystemLocationSerializer
    permission_classes=[IsAuthenticated,AdminPermission]
    authentication_classes=[TokenAuthentication]

    def put(self,request,uuid):
        try:
            system_location=SystemLocation.objects.get(uuid=uuid)
            print(system_location)
        except SystemLocation.DoesNotExist:
            return Response({"message":"System location does not found"},status=status.HTTP_404_NOT_FOUND)
        serializer=self.serializer_class(system_location,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        print(serializer.validated_data)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def delete(self,request,uuid):
        try:
            system_location=SystemLocation.objects.get(uuid=uuid)
        except SystemLocation.DoesNotExist:
            return Response({'message':'System location does not found'},status=status.HTTP_404_NOT_FOUND)
        system_location.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    

class AllLocationSettingsAPI(APIView):
    serializer_class=serialilzers.LocationSettingsSerializer
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsAuthenticated]


    def get_queryset(self):
        member=Member.objects.filter(user=self.request.user,role__name="admin")
        if member.exists():
            return LocationSettings.objects.all()
        else:
            return LocationSettings.objects.filter(shiftschedulelog__member__user=self.request.user)
        
    def get(self,request,*args,**kwargs):
        queryset=self.get_queryset()
        serializer=self.serializer_class(queryset,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
class LocationSettingsAPI(APIView):
    serializer_class=serialilzers.LocationSettingsSerializer
    permission_classes=[IsAuthenticated,AdminPermission]
    authentication_classes=[TokenAuthentication]
    def post(self, request, uuid):
        member=Member.objects.filter(user=request.user,role__name="admin")
        if not member.exists():
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        member_obj=member.first()
        try:
            shift_schedule=ShiftScheduleLog.objects.get(uuid=uuid)
        except ShiftScheduleLog.DoesNotExist:
            return Response({'message':'shift schedule log is not found'},status=status.HTTP_404_NOT_FOUND)
        shift = Shift.objects.get(shiftschedulelog__uuid=shift_schedule.uuid)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_time = serializer.validated_data.get('start_time')
        end_time = serializer.validated_data.get('end_time')

        
        shift_start_time = datetime.combine(datetime.today(), shift.start_time)
        shift_end_time = datetime.combine(datetime.today(), shift.end_time)

        
        start_time_dt = datetime.combine(datetime.today(), start_time)
        end_time_dt = datetime.combine(datetime.today(), end_time)

        
        
        if shift.start_time.hour > shift.end_time.hour:
            shift_end_time += timedelta(hours=24)
            end_time_dt+=timedelta(hours=24)


        
        
        if not (shift_start_time<=start_time_dt < shift_end_time):
            return Response({'message': 'Location settings must be within the start time and end time'}, status=status.HTTP_400_BAD_REQUEST)
        elif not ( shift_start_time<=end_time_dt <= shift_end_time):
            return Response({'message': 'Time must be within the start time and end time of shift'}, status=status.HTTP_400_BAD_REQUEST)

        location_setting = serializer.save(updated_by=member_obj,created_by=member_obj)

        shift_schedule.location_settings.add(location_setting)

        return Response({'message': 'Location settings saved successfully'}, status=status.HTTP_201_CREATED)

    def put(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin")
        if not member.exists():
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        member_obj=member.first()
        try:
            location_setting=LocationSettings.objects.get(uuid=uuid)
        except LocationSettings.DoesNotExist:
            return Response({'message':'Location settings does not exist'},status=status.HTTP_404_NOT_FOUND)
        serialilzer=self.serializer_class(location_setting,data=request.data)
        serialilzer.is_valid(raise_exception=True)

        serialilzer.save(updated_by=member_obj)
        return Response(serialilzer.data,status=status.HTTP_200_OK)
    
    def delete(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin")
        if not member.exists():
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        try:
            location_setting=LocationSettings.objects.get(uuid=uuid)
        except LocationSettings.DoesNotExist:
            return Response({'message':'Location settings does not exist'},status=status.HTTP_404_NOT_FOUND)
        location_setting.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
            
        
        
        
    

