from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from roles.permissions import AdminPermission
from roles.models import Member
from shift import serializers,models
from shift.tasks import schedule_shifts
from shift.models import ShiftScheduleLog
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta,date

class AllShiftAPI(APIView):
    serializer_class=serializers.ShiftSerializer
    permission_classes=[IsAuthenticated,AdminPermission]
    authentication_classes=[TokenAuthentication]

    def get(self,request,*args,**kwargs):
        schedule_shifts.delay()
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        queryset=models.Shift.objects.all()
        serializer=self.serializer_class(queryset,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request,*args,**kwargs):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        member=models.Member.objects.get(user=request.user)
        serializer.save(created_by=member,updated_by=member)
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    

class ShiftAPI(APIView):
    serializer_class=serializers.ShiftSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes=[TokenAuthentication]

    def put(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        try:
            shift=models.Shift.objects.get(uuid=uuid)
            
        except models.Shift.DoesNotExist:
            return Response({'message':"Shift does not found"},status=status.HTTP_404_NOT_FOUND)
        serializer=self.serializer_class(shift,data=request.data)
        serializer.is_valid(raise_exception=True)
        member=models.Member.objects.get(user=self.request.user)
        serializer.save(updated_by=member)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def delete(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        try:
            shift=models.Shift.objects.get(uuid=uuid)
        except models.Shift.DoesNotExist:
            return Response({'message':"Shift does not found"},status=status.HTTP_404_NOT_FOUND)
        shift.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class AllShiftScheduleLogAPI(APIView):
    serializer_class=serializers.ShiftScheduleLogSerializer
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsAuthenticated]
    def get_queryset(self):
        member=Member.objects.filter(user=self.request.user,role__name="admin").exists()
        if member:
            return ShiftScheduleLog.objects.all().order_by('start_date')
        else:
            return ShiftScheduleLog.objects.filter(member__user=self.request.user).order_by('start_date')
 
    def get(self,request,*args,**kwargs):
        serializer=self.serializer_class(self.get_queryset(),many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request,*args,**kwargs):
        member=Member.objects.filter(user=request.user,role__name="admin")
        if not member.exists():
            return Response({'message':'You do not have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        member=serializer.validated_data.get('member')
        start_date=serializer.validated_data.get('start_date')
        end_date=serializer.validated_data.get('end_date')
        if end_date is None:
                print("this needs to be executed")
                #this functionality is for deleting the shift schedules when we put end date as null during creation process
                shift_schedules_delete=ShiftScheduleLog.objects.filter(start_date__gte=start_date,member=member)
                print(shift_schedules_delete,"this needs to deleted")
                shift_schedule_same_date=ShiftScheduleLog.objects.filter(start_date=start_date,end_date__isnull=True).first()#Checking if it already exists or not
                #checking whether same date is applied
                if shift_schedule_same_date:
                    return Response({'message':'No changes were made since you assigned the same schedule'},status=status.HTTP_200_OK)
                #If the assigned start_date is different from start_date present in the data base deleting all the objects from that start_date and we have to assign end_date to the shift schedule log which is present before our null object which is done in 109
                shift_schedule_previous_one=ShiftScheduleLog.objects.filter(start_date__lt=start_date).order_by('-start_date').first()
                print(shift_schedule_previous_one,"this is previous one")
                if shift_schedule_previous_one:
                    if shift_schedule_previous_one.end_date is None or (start_date<=shift_schedule_previous_one.end_date):#updating end date only if new shift is in previous one otherwise keep it.
                        shift_schedule_previous_one.end_date=start_date-timedelta(days=1)
                    shift_schedule_previous_one.save()
                    shift_schedule_previous_one_serializer=self.serializer_class(shift_schedule_previous_one)
                    shift_schedules_delete.delete()
                    shift_schedule2=serializer.save()
                    if shift_schedule_previous_one.start_date>shift_schedule_previous_one.end_date:
                        shift_schedule_previous_one.delete()
                    return Response({'shift_updated':shift_schedule_previous_one_serializer.data,'shif_schedule_new':serializer.data},status= status.HTTP_201_CREATED)
                else:
                    shift_schedules_delete.delete()
                    serializer.save()
                    return Response({'shift_null':serializer.data},status=status.HTTP_200_OK)
                '''this is for when user uploads shift which is already assigned so we update it and create new shift if there is a more than one day left in the previous shift time'''
        shift_schedules=ShiftScheduleLog.objects.filter(Q(member=member)&((Q(start_date__lte=start_date)&(Q(end_date__gte=end_date)|Q(end_date__isnull=True))))|Q(start_date__lte=start_date,end_date__gte=start_date)|(Q(start_date__lte=end_date)&(Q(end_date__gte=end_date)|Q(end_date__isnull=True)))).order_by('start_date')
        #this filtering condition works for either one shift schedule log or two shift schedule log
        print(shift_schedules,"these are the shift schedules that matches date")
        if shift_schedules.exists():   
            shift_schedule=shift_schedules.first()
            temporary_storing_shift_schedule=shift_schedule
            shift_end_date_temp=shift_schedule.end_date
            if shift_schedules.count()==2:
                shift_second=shift_schedules[1]
                shift_second_start_time=shift_second.start_date
                print(shift_second_start_time,"this is start date of second")
                deleting_schedules=ShiftScheduleLog.objects.filter(start_date__gt=shift_end_date_temp,end_date__lt=shift_second_start_time)
                print(deleting_schedules,"these needs to delete")
                deleting_schedules.delete()
                
                
            '''If the assigned start date is contains the start_date which is present in our data base'''
            if (shift_schedule.start_date==start_date) & (shift_schedule.end_date==end_date):
                return Response({'message':'Shift schedule with this details exists'},status=status.HTTP_400_BAD_REQUEST)
            elif (shift_schedule.start_date==start_date)& shift_schedules.count()==1:
                #condition for only start date matches
                print("same date condition is executing")
                shift_schedule.end_date=end_date#if start date already exists simply updating the end date
                shift_schedule.save()
                shift_schedule_serializer=self.serializer_class(shift_schedule)
                new_shift_schedule=ShiftScheduleLog.objects.create(member=member,shift=temporary_storing_shift_schedule.organization.shift_default,start_date=shift_schedule.end_date+timedelta(days=1),end_date=shift_end_date_temp,organization=temporary_storing_shift_schedule.organization)
                new_shift_serializer=self.serializer_class(new_shift_schedule)
                return Response({'shift updated':shift_schedule_serializer.data,"new shift":new_shift_serializer.data},status=status.HTTP_200_OK)
            '''if there is no start_date object which matches data base object in that case perform another opeation'''
            '''this is when the start and end date condition does not match'''
            shift_schedule.end_date=start_date-timedelta(days=1)
            shift_schedule_serializer=self.serializer_class(shift_schedule)
            shift_schedule.save()
            shift_schedule_serializer=self.serializer_class(shift_schedule)
            shift_schedule2=serializer.save()
            '''if the date is greater than 1 in that case only we create a new third object otherewise we won't create new object'''
            if shift_end_date_temp is None or (shift_end_date_temp - shift_schedule2.end_date).days > 1 or shift_schedules.count()==2:
                if shift_schedules.count()==2:
                    shift_schedule3=shift_schedules[1]
                    
                    print((end_date-shift_schedule3.start_date).days,"this is the difference")
                    #if start date and end date matches with first and second shift respectively create that one and delete existing two
                    if (start_date==shift_schedule.start_date) & (end_date==shift_schedule3.end_date):
                        shift_schedule.delete()
                        shift_schedule3.delete()
                        return Response({'shift':serializer.data},status=status.HTTP_200_OK)
                    elif (start_date==shift_schedule.start_date)&(end_date==shift_schedule3.start_date):
                        pass
                    #this is for start_date matches in the first one
                    elif start_date==shift_schedules.first().start_date:
                        shift_second=shift_schedules[1]
                        print(shift_second,"this is second one")
                        if shift_second.end_date is None or (shift_second.end_date-end_date).days>1:
                            shift_second.start_date=end_date+timedelta(days=1)
                        
                            shift_second.save()
                            print(shift_second.start_date,"this is start date")
                            shift_second_serializer=self.serializer_class(shift_second)
                        
                        if shift_schedule.end_date<shift_schedule.start_date:
                            shift_schedule.delete()
                        elif shift_schedule.end_date>shift_schedule.start_date:
                            shift_schedule.end_date-timedelta(days=1)
                            shift_schedule.save()
                        else:
                            shift_second.delete()
                            return Response({'shift_updated':shift_schedule_serializer.data,'shift_new':serializer.data},status=status.HTTP_200_OK)

                        return Response({'shift':serializer.data,'updated_one1':shift_second_serializer.data},status=status.HTTP_200_OK)
                    #this is when end date matches with second one
                    elif end_date==shift_schedule3.end_date:
                        shift_schedule3.delete()
                        return Response({'shift_one':shift_schedule_serializer.data,"shift_two":serializer.data},status=status.HTTP_200_OK)
                

                    if shift_schedule3.end_date is None or (end_date-shift_schedule3.end_date).days!=0:
                        print("if loop executing")
                        if shift_schedule.end_date<shift_schedule.start_date:
                            shift_schedule.delete()
                        print(shift_schedule3,shift_schedule3.start_date,shift_schedule3.end_date)
                        shift_schedule3.start_date=end_date+timedelta(days=1)
                        shift_schedule3.save()
                else:
                    if shift_schedule.end_date<shift_schedule.start_date:
                            shift_schedule.delete()
                    
                    shift_schedule3=ShiftScheduleLog.objects.create(member=member,shift=temporary_storing_shift_schedule.organization.shift_default,start_date=(end_date+timedelta(days=1)),organization=temporary_storing_shift_schedule.organization,end_date=shift_end_date_temp)
                shift_schedule3_data=self.serializer_class(shift_schedule3)
                return Response({"shift_updated":shift_schedule_serializer.data,"shif_schedule_new ":serializer.data,"shift_updated_new":shift_schedule3_data.data},status=status.HTTP_201_CREATED)
            else:
                if shift_schedule.end_date<shift_schedule.start_date:
                        shift_schedule.delete()
                return Response({"shift_updated":shift_schedule_serializer.data,"shif_schedule_new":serializer.data},status=status.HTTP_201_CREATED)
        '''if there is no shift schedule log i.e present in the dates we simply save it'''
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    

class ShiftScheduleLogAPI(APIView):
    serializer_class=serializers.ShiftScheduleLogSerializer
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsAuthenticated,AdminPermission]

    def put(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)       
        try:
            shift_schedule=ShiftScheduleLog.objects.get(uuid=uuid)
        except ShiftScheduleLog.DoesNotExist:
            return Response({'message':"ShiftSchedule does not found"},status=404)
        serializer=self.serializer_class(shift_schedule,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=200)
    def delete(self,request,uuid):
        member=Member.objects.filter(user=request.user,role__name="admin").exists()
        if not member:
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        try:
            shift_schedule=ShiftScheduleLog.objects.get(uuid=uuid)
        except ShiftScheduleLog.DoesNotExist:
            return Response({'message':"Trip schedule details not found"},status=404)
        shift_schedule.delete()

        return Response(status=204)

    
    



        

