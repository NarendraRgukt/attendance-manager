from django.contrib import admin

# Register your models here.

from .models import MemberScan,Attendance

admin.site.register(MemberScan)
admin.site.register(Attendance)