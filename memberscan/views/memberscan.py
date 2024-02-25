from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from memberscan.serializers import MemberScanSerializer,AttendanceSerializer
from roles.models import Member
from memberscan.models import MemberScan,Attendance
from shift.models import Shift,ShiftScheduleLog
from location.models import SystemLocation,LocationSettings
from geopy.distance import geodesic
import face_recognition
from frimage.models import FRImage
from PIL import Image
import numpy as np
from datetime import datetime
from django.utils import timezone
import base64
from django.core.files.base import ContentFile
from roles.models import ExportRequest
from roles.tasks import export_request
from shift.tasks import schedule_shifts
from roles.serializers import ExportRequestSerializer
from django.db.models import Q
from datetime import datetime,date


class AllMemberScanAPI(APIView):
    serializer_class=MemberScanSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes=[TokenAuthentication]
    def get_queryset(self):
        member=Member.objects.filter(user=self.request.user,role__name="admin")
        if member.exists():
            return MemberScan.objects.all()
        else:
            return MemberScan.objects.filter(member__user=self.request.user)
        
    def get(self,request,*args,**kwargs):
        member=Member.objects.filter(user=self.request.user,role__name="admin")
        queryset=self.get_queryset()
        export=request.GET.get('export')
        query=Q()
        start_date_string=request.GET.get('start_date')
        end_date_string=request.GET.get('end_date')
        
        print(timezone.now(),"this is django date time field")
        if start_date_string and end_date_string:
            start_date=datetime.strptime(start_date_string,"%Y-%m-%d")
            end_date=datetime.strptime(end_date_string,"%Y-%m-%d")
            query=Q(created_at__range=(start_date.date(),end_date.date()))
            
        if export:
            uuids_list=MemberScan.objects.filter(query).values('uuid')
            uuids=[]
            for uuid_dict in uuids_list:
                uuid=uuid_dict.get("uuid")
                uuids.append(str(uuid))
            content={
                'model':'MemberScan',
                'uuid':uuids
            }
            print(uuids)
            if len(uuids)==0:
                return Response({'message:No objects in the database'},status=status.HTTP_404_NOT_FOUND)
            export_request_obj=ExportRequest.objects.create(member=member.first(),content=content,status="pending")
            serializer=ExportRequestSerializer(export_request_obj)
            export_request.apply_async()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        serializer=self.serializer_class(queryset,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request,*args,**kwargs):
        try:
            shift=Shift.objects.get(shiftschedulelog__member__user=request.user)
            print(shift)
        except Shift.DoesNotExist:
            return Response({'message':"Shift location does not found"},status=status.HTTP_404_NOT_FOUND)
        today_date=timezone.now().date()
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        scan_latitude=serializer.validated_data.get('latitude')
        scan_longitude=serializer.validated_data.get('longitude')
        scan_location=(scan_latitude,scan_longitude)
        system_location=SystemLocation.objects.get(shift=shift)
        shift_latitude_default=system_location.latitude
        shift_longitude_default=system_location.longitude
        shift_location=(shift_latitude_default,shift_longitude_default)
        shift_schedules=ShiftScheduleLog.objects.filter(Q(member__user=request.user) &
        (
        Q(start_date__gte=today_date) &
        (Q(end_date__lte=today_date) | Q(end_date__isnull=True))
        ))
        if shift_schedules.count()>1:
            return Response({'message':'unknown error occured'},status=status.HTTP_400_BAD_REQUEST)
        
        

        location_status=False
        if shift.shift_start_time_restriction:
            current_time = timezone.now().time()
            if current_time>shift.start_time:
                return Response({'message':'You are not on the right time'},status=status.HTTP_400_BAD_REQUEST)
        
        for shift_schedule in shift_schedules:
            location_settings=LocationSettings.objects.filter(shiftschedulelog=shift_schedule)
            if location_settings.exists():
                for location_setting in location_settings:
                    location_latitude=location_setting.system_location.latitude
                    location_longitude=location_setting.system_location.longitude
                    location=(location_latitude,location_longitude)
                    distance=geodesic(location,scan_location).meters
                    if distance<=location_setting.system_location.radius:
                        location_status=True
                        if shift.loc_settings_start_time_restriction:
                            current_time = timezone.now().time()
                            start_time=location_setting.start_time
                            if current_time>start_time:
                                return Response({'message':'You are not at time of location time'},status=status.HTTP_400_BAD_REQUEST)
                        
                        break
                if location_status==False:
                    return Response({'message':'You are not at the registered locations'},status=status.HTTP_400_BAD_REQUEST)
                        
            
        if shift.enable_geo_fencing:
            distance=geodesic(scan_location,shift_location).meters
            if distance>system_location.radius:
                return Response({"message":"you are not at the system location"},status=status.HTTP_400_BAD_REQUEST)
        if shift.enable_face_recognition:
            try:
                frimage_objects = FRImage.objects.filter(member__user=request.user)
                
                if not frimage_objects.exists():
                    return Response({'message': 'No reference images found'}, status=status.HTTP_404_NOT_FOUND)

                scan_image_base64 = serializer.validated_data.get('image')
                format, file = scan_image_base64.split(";base64,")
                extension = format.split("/")[-1]
                file_name = f'image.{extension}'
                file_decode = base64.b64decode(file)
                scan_image = ContentFile(file_decode, name=file_name)

                scan_image_load = face_recognition.load_image_file(scan_image)
                scan_image_encoding = face_recognition.face_encodings(scan_image_load)[0]

                frimage_encodings = [
                    face_recognition.face_encodings(face_recognition.load_image_file(image.image.path))[0]
                    for image in frimage_objects
                ]

                similarity_threshold = 0.6
                face_distances = face_recognition.face_distance(frimage_encodings, scan_image_encoding)
                min_face_distance = np.min(face_distances)
                min_distance_index = np.argmin(face_distances)
                print(min_distance_index)
                print(min_distance_index,"this is minimum distance index")
                face_match = face_recognition.compare_faces(frimage_encodings, scan_image_encoding)
                print(face_match,"this is face match value")
                if not face_match[min_distance_index]:
                    return Response({'message': 'Your face does not match'}, status=status.HTTP_400_BAD_REQUEST)
                serializer.save(image=scan_image)
                return Response({'message':'your data  is recorded successfully','data':serializer.data},status=status.HTTP_201_CREATED)
             

            except Exception as e:
                return Response({'message': 'Something wrong with image please provide the valid image'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    
 
            

class AllAttendanceAPI(APIView):
    serializer_class=AttendanceSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes=[TokenAuthentication]

    def get(self,request,*args,**kwargs):
        member=Member.objects.filter(user=request.user,role__name="admin")
        if not member.exists():
            return Response({'message':'You donot have the permission'},status=status.HTTP_401_UNAUTHORIZED)
        export=request.GET.get('export')
        member_uuid=request.GET.get('member')
        query=Q()
        if member_uuid:
            query &=Q(member__uuid=member_uuid)
        if export:
            attendance_id=Attendance.objects.all().values("id")
            print(attendance_id)
            attendance_ids=attendance_id.filter(query)
            print(attendance_ids)
            ids=[]
            for id_dict in attendance_ids:
                id=id_dict.get("id")
                ids.append(id)
            content={
                'model':'Attendance',
                'uuid':ids
            }
            if len(ids)==0:
                return Response({'message:No objects in the database'},status=status.HTTP_404_NOT_FOUND)
            export_request_obj=ExportRequest.objects.create(member=member.first(),content=content,status="pending")
            serializer=ExportRequestSerializer(export_request_obj)
            export_request.apply_async()
            return Response(serializer.data,status=status.HTTP_201_CREATED)

        queryset=Attendance.objects.all()
        serializer=self.serializer_class(queryset,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)