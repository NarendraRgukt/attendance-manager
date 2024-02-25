from django.db import models
import uuid
from roles.models import Member,Organization,Role
class SystemLocation(models.Model):
    status_choices=(
        ('active','active'),
        ('inactive','inactive')
    )
    uuid=models.UUIDField(primary_key=True,editable=False,default=uuid.uuid4)
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="systemlocation")
    name=models.CharField(max_length=200)
    description=models.TextField(max_length=200,null=True)
    latitude=models.DecimalField(max_digits=9,decimal_places=7)
    longitude=models.DecimalField(max_digits=9,decimal_places=7)
    radius=models.FloatField(default=50.0)
    status=models.CharField(choices=status_choices,max_length=15)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    


class LocationSettings(models.Model):
    uuid=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    system_location=models.ForeignKey(SystemLocation,on_delete=models.CASCADE,related_name="locationsettings")
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="locationsettings")
    start_time=models.TimeField()
    end_time=models.TimeField()
    applicable_start_date=models.DateField()
    applicable_end_date=models.DateField(null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey(Member,on_delete=models.CASCADE,related_name="locationsettings",null=True)
    updated_by=models.ForeignKey(Member,on_delete=models.CASCADE,related_name="updated_locationsettings",null=True)

    def __str__(self):
        return '{self.uuid}'

