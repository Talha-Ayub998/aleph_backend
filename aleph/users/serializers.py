from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import *
from django.core.mail import send_mail
import string

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    generate_initial_password = serializers.BooleanField(write_only=True, default=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'group', 'status', 'password', 'generate_initial_password']

    def create(self, validated_data):
        generate_initial_password = validated_data.pop('generate_initial_password', True)
        password = validated_data.pop('password', None)

        user = User.objects.create(**validated_data)

        if password:
            user.set_password(password)
            user.save()
        elif generate_initial_password:
            generated_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))  # Generate a random password
            user.set_password(generated_password)
            user.save()

            # Send email with the initial password
            send_mail(
                'Your Initial Password',
                f'Your initial password is: {generated_password}',
                'admin@example.com',  # Sender's email address
                [validated_data['email']],  # Recipient's email address
                fail_silently=False,
            )

        return user


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
        fields = ['id', 'file', 'uploaded_at']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description']
