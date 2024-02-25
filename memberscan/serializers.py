from .models import MemberScan,Attendance
from rest_framework import serializers

class MemberScanSerializer(serializers.ModelSerializer):
    image=serializers.CharField()
    class Meta:
        model=MemberScan
        fields="__all__"

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model=Attendance
        fields="__all__"
        