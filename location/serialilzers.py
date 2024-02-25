from rest_framework import serializers
from location import models
class SystemLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.SystemLocation
        fields="__all__"
        read_only_fields=["uuid"]

    def update(self,instance,validated_data):
        instance=super().update(instance,validated_data)
        return instance
    

class LocationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.LocationSettings
        fields="__all__"