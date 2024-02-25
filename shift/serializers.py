from rest_framework import serializers
from shift import models

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.Shift
        fields="__all__"
        read_only_fields=["created_by","updated_by"]


    def update(self,instance,validated_data):
        instance=super().update(instance,validated_data)
        return instance
    

class ShiftScheduleLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.ShiftScheduleLog
        fields="__all__"

    def update(self,instance,validated_data):
        instance=super().update(instance,validated_data)
        return instance