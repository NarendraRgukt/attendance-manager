from django.db import models
from roles.models import Member,Organization,Role
import uuid
class Shift(models.Model):
    status_choices=(
        ('active','active'),
        ('inactive','inactive')
    )
    uuid=models.UUIDField(primary_key=True,editable=False,default=uuid.uuid4)
    name=models.CharField(max_length=200,unique=True)
    description=models.TextField(max_length=200,null=True)
    start_time=models.TimeField()
    end_time=models.TimeField()
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="shift")
    default_location=models.ForeignKey("location.SystemLocation",on_delete=models.CASCADE,related_name="shift",null=True)
    enable_face_recognition=models.BooleanField(default=True)
    enable_geo_fencing=models.BooleanField(default=True)
    status=models.CharField(choices=status_choices,max_length=15,default="active")
    shift_start_time_restriction=models.BooleanField(default=True)
    loc_settings_start_time_restriction=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey(Member,on_delete=models.CASCADE,related_name='shift')
    updated_by=models.ForeignKey(Member,on_delete=models.CASCADE,related_name="updated_shift")
    crone_job=models.TimeField()

    class Meta:
        unique_together=["name","organization"]

    def __str__(self) -> str:
        return self.name
    

class ShiftScheduleLog(models.Model):
    status_choices=(
        ('active','active'),
        ('inactive','inactive')
    )
    uuid=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    member=models.ForeignKey(Member,on_delete=models.CASCADE,related_name="shiftschedulelog")
    shift=models.ForeignKey(Shift,on_delete=models.CASCADE,related_name="shiftschedulelog")
    status=models.CharField(choices=status_choices,max_length=15,default="active")
    start_date=models.DateField()
    end_date=models.DateField(null=True,blank=True)
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="shiftschedulelog")
    location_settings=models.ManyToManyField("location.LocationSettings",related_name="shiftschedulelog",blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.start_date}__{self.end_date}"
    class Meta:
        ordering=['start_date']




    

