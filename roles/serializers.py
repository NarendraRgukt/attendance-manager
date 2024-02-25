from rest_framework import serializers
from roles import models
from django.contrib.auth import get_user_model,authenticate

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.Member
        fields="__all__"
        read_only_fields=['uuid']

    def update(self,instance,validated_data):
        instance=super().update(instance,validated_data)
        return instance
    





class MemberUserSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=245)
    username = serializers.CharField(max_length=123)
    password = serializers.CharField(write_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=models.Role.objects.all()) 
    organization = serializers.PrimaryKeyRelatedField(queryset=models.Organization.objects.all())
    first_name=serializers.CharField(max_length=100)
    last_name=serializers.CharField(max_length=123)

class ExportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.ExportRequest
        fields="__all__"


        

        
        
