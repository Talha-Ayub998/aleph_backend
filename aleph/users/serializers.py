from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import *
from django.core.mail import send_mail
import string
from django.contrib.auth import get_user_model


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
                'talhaayub998@gmail.com',  # Sender's email address
                [validated_data['email']],  # Recipient's email address
                fail_silently=False,
            )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


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
        fields = ['id', 'uploaded_at', 'file_url', 's3_file_name', 'file_name', 'project']

class MultiplePageDocumentSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField()
    )
    project_id = serializers.IntegerField()

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description']

class ProjectMultipleSerializer(serializers.ModelSerializer):
    total_documents = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'total_documents']

    def get_total_documents(self, obj):
        return obj.documents.count()

class PotentialUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PotentialUser
        fields = ['email', 'first_name', 'last_name']

    def validate_email(self, value):
        User = get_user_model()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'