from django.contrib import admin

from .models import LocationSettings,SystemLocation

admin.site.register(LocationSettings)
admin.site.register(SystemLocation)
