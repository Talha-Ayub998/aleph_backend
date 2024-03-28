from rest_framework import serializers
from django.contrib.auth import authenticate


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=user.email, password=data.get('password'))  # Change to 'email'
        if not user:
            raise serializers.ValidationError("Invalid email or password")  # Update error message
        return user

