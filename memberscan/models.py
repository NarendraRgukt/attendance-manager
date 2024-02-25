from django.db import models
import uuid
from roles.models import Organization,Role,Member
from shift.models import Shift

class Attendance(models.Model):
    status_choices=(
        ("present","present"),
        ("absent","absent")
    )
    shift=models.ForeignKey(Shift,on_delete=models.CASCADE)
    member=models.ForeignKey(Member,on_delete=models.CASCADE)
    status=models.CharField(choices=status_choices,max_length=19)
    date=models.DateField()

class MemberScan(models.Model):
    scan_choices=(
        ('checkin','checkin'),
        ('checkout','checkout')
    )
    uuid=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    member=models.ForeignKey(Member,on_delete=models.CASCADE,related_name="memberscan")
    system_location=models.ForeignKey("location.SystemLocation",on_delete=models.CASCADE,related_name="memberscan",null=True)
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="memberscan")
    image=models.ImageField(null=True,upload_to="media")
    date_time=models.DateTimeField(auto_now_add=True)
    latitude=models.CharField(max_length=200,null=True,blank=True)
    longitude=models.CharField(max_length=200,null=True,blank=True)
    scan_type=models.CharField(choices=scan_choices,max_length=15,null=True)
    created_at=models.DateTimeField()
    attendance=models.ForeignKey(Attendance,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return f'{self.member}'
    class Meta:
        ordering=["-created_at"]

