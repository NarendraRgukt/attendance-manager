from frimage.models import FRImage
from rest_framework import serializers
import base64
from io import BytesIO
from PIL import Image


class FrImageSerializer(serializers.ModelSerializer):
    image=serializers.CharField()
    class Meta:
        model=FRImage
        fields="__all__"

    def update(self,instance,validated_data):
        instance=super().update(instance,validated_data)
        return instance