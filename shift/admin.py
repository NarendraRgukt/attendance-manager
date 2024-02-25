from django.contrib import admin

from .models import Shift,ShiftScheduleLog

admin.site.register(Shift)

admin.site.register(ShiftScheduleLog)
