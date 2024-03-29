from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'group', 'status', 'created_at', 'last_login']

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")

    def to_representation(self, instance):
        return UserSerializer(instance).data


class PageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageImage
        fields = ['id', 'document', 'image']



class PageDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file']
