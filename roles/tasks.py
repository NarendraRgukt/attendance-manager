from celery import Celery
from celery import shared_task
from celery.schedules import crontab
from attendancemanager.celery import app
from shift.tasks import schedule_shifts
from roles.models import ExportRequest
from memberscan.models import Attendance,MemberScan
from roles.models import Member,ExportRequest
import csv
from django.conf import settings
import os
from django.core import serializers
import json
from roles.serializers import MemberSerializer
from memberscan.serializers import MemberScanSerializer,AttendanceSerializer

@shared_task
def export_request():

    export_requests=ExportRequest.objects.filter(status="pending")


    for export_request in export_requests:
        export_request_content=export_request.content
        export_request_model=export_request_content.get('model')
        print("this is the requested model",export_request_model)
        export_request_uuids=export_request_content.get('uuid')
        print("these are the list of uuids",export_request_uuids)
        csv_file_path=os.path.join(settings.MEDIA_ROOT,f'{export_request_model}_{export_request.uuid}.csv')
        relative_path=os.path.relpath(csv_file_path,start=settings.BASE_DIR)
        if export_request_model=="Attendance":
            attendance_objects=Attendance.objects.filter(id__in=export_request_uuids)
            field_names=["id","shift","status","member","date"]
            with open(csv_file_path,"w",newline="") as csv_file:
                writer=csv.DictWriter(csv_file,field_names)
                writer.writeheader()
                for attendance_object in attendance_objects:
                    writer.writerow({
                        'id': attendance_object.id,
                        'shift': attendance_object.shift.name,
                        'status': attendance_object.status,
                        'member': attendance_object.member.user.email,
                        'date': attendance_object.date
                        })

        if export_request_model=="MemberScan":
            memberscan_objects=MemberScan.objects.filter(uuid__in=export_request_uuids)
            print("memberscan objects",memberscan_objects)
            serializer=MemberScanSerializer(memberscan_objects,many=True)
            field_names = ["uuid","member","system_location","organization","image","date_time","latitude","longitude","scan_type",'created_at','attendance']
            print(field_names)
            with open(csv_file_path,"w",newline="") as csv_file:
                writer=csv.DictWriter(csv_file,field_names)
                writer.writeheader()
                for memberscan_object in memberscan_objects:
                    writer.writerow({
                        "uuid":memberscan_object.uuid,
                        "member":memberscan_object.member.user.email,
                        "system_location":memberscan_object.system_location.name,
                        "organization":memberscan_object.organization.name,
                        "image":memberscan_object.image,
                        "date_time":memberscan_object.date_time,
                        "latitude":memberscan_object.latitude,
                        "longitude":memberscan_object.longitude,
                        "scan_type":memberscan_object.scan_type,
                        "created_at":memberscan_object.created_at,
                        "attendance":memberscan_object.attendance

                    })
        if export_request_model=="Member":
            print(export_request,"this is export request")
            member_objects=Member.objects.filter(uuid__in=export_request_uuids)
            print(member_objects)
            serializer=MemberSerializer(member_objects,many=True)
            field_names=["uuid","email","username","first_name","last_name","organization","role"]
            with open(csv_file_path,"w",newline="") as csv_file:
                writer=csv.DictWriter(csv_file,field_names)
                writer.writeheader()
                for member_object in member_objects:
                    writer.writerow({
                        "uuid":member_object.uuid,
                        "email":member_object.user.email,
                        "username":member_object.user.username,
                        "first_name":member_object.user.first_name,
                        "last_name":member_object.user.last_name,
                        "organization":member_object.organization.name,
                        "role":member_object.role.name
                    })
        export_request.status="completed"
        export_request.path=relative_path
        export_request.save()
        

        
        




app.conf.beat_schedule={
    'export_request':{
        'task':'roles.tasks.export_request',
        'schedule':crontab(minute="*/60")
    }
}