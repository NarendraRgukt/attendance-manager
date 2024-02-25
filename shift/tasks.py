from .models import ShiftScheduleLog,Shift
from memberscan.models import MemberScan,Attendance
from datetime import datetime,timedelta,time
from attendancemanager.celery import Celery
from celery.schedules import crontab
from celery import shared_task
from django.utils import timezone
from attendancemanager.celery import app
import logging
logger=logging.getLogger(__name__)
from rest_framework.response import Response
from django.db.models import Q
from roles.models import Organization


@shared_task
def schedule_shifts():

    current_hour=timezone.now().time().hour
    print(current_hour)
    current_date = timezone.now().date() 
    organizations=Organization.objects.all()
    for organization in organizations:
        today_date=timezone.now().date()
        due_shifts = ShiftScheduleLog.objects.filter(Q(shift__crone_job__hour=current_hour)&Q(organization=organization)&(
        Q(shiftschedulelog__start_date__gte=today_date) &
        (Q(shiftschedulelog__end_date__lte=today_date) | Q(shiftschedulelog__end_date__isnull=True))
        ))
        print(due_shifts)
        date_now= timezone.now()
        date_before=date_now-timedelta(days=1)
        for shift_schedule in due_shifts:
            print("shift schedule starts")
            memberscans = MemberScan.objects.filter(member=shift_schedule.member,created_at__range=(date_before,date_now)).order_by('created_at')
            total_time_difference = timedelta()  # Initialize total time difference as zero

            num_scans = len(memberscans)
            pair_size = 2  # Number of scans in each pair
            print(num_scans,"this is number of scans")

            if num_scans >= 2:
                for i in range(0,num_scans, pair_size):
                    scan1=memberscans[i]
                    print(scan1,"this is scan 1 ")
                    try:
                        scan2=memberscans[i+1]
                        print(scan2,"this is scan 2")
                    except IndexError:
                        break
                    difference=scan2.created_at-scan1.created_at
                    total_time_difference+=difference
                    print(total_time_difference,"this is total time difference")
                print("total_time difference after for loop",total_time_difference)
                total_working_hours = total_time_difference.total_seconds() / 3600  # Convert to hours
                print("Total Working Hours:", total_working_hours)
                        
                if total_working_hours>=8:
                    attendance=Attendance.objects.create(member=shift_schedule.member,status="present",shift=shift_schedule.shift,date=current_date)
                    for memberscan in memberscans:
                        memberscan.attendance=attendance
                        memberscan.save()
                    
                else:
                    attendance=Attendance.objects.create(member=shift_schedule.member,status="absent",shift=shift_schedule.shift,date=current_date)
                    for memberscan in memberscans:
                        memberscan.attendance=attendance
                        memberscan.save()

            else:
                attendance=Attendance.objects.create(member=shift_schedule.member,status="absent",shift=shift_schedule.shift,date=current_date)
                for memberscan in memberscans:
                    memberscan.attendance=attendance
                    memberscan.save()



app.conf.beat_schedule={
    'schedule_shifts':{
        'task':'shift.tasks.schedule_shifts',
        'schedule':crontab(minute="*/60")
    }
}