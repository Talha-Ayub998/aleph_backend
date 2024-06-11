import random
import string
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, User, PermissionsMixin
# import json
# from datetime import datetime# from django.contrib.postgres.fields import JSONField
# from django.db.models import JSONField
# import fitz  # PyMuPDF
# from django.core.files.base import ContentFile
# from PIL import Image, ImageDraw, ImageFont
# import io
# import os


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# Company Model
class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact = models.CharField(max_length=30, default="0")  # Replace "default_contact_value" with your desired default value
    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class User(AbstractBaseUser, PermissionsMixin):
    GROUP_CHOICES = (
        ('review', 'Review'),
        ('admin', 'Admin'),
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    user_id = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.CharField(max_length=10, choices=GROUP_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    last_login = models.DateTimeField(null=True, blank=True)
    password = models.CharField(max_length=128)  # This is the hashed password field
    is_staff = models.BooleanField(default=False)  # Staff status
    is_superuser = models.BooleanField(default=False)  # Superuser status
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees', null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
        if not self.pk:  # Only generate user_id if the instance is being created (not updated)
            self.user_id = self._generate_user_id()
        super().save(*args, **kwargs)

    def _generate_user_id(self):
        while True:
            # Generate a random 2-digit number
            number_part = str(random.randint(10, 99))

            # Generate a random alphabet
            alphabet_part = random.choice(string.ascii_uppercase)

            # Concatenate the number and alphabet parts
            generated_id = number_part + alphabet_part

            # Check if the generated ID already exists in the database
            if not User.objects.filter(user_id=generated_id).exists():
                return generated_id

    def __str__(self):
        return f"{self.email}"

    class Meta:
        ordering = ['-created_at']

    def has_module_perms(self, app_label):
        # For simplicity, grant all users access to all modules
        return True


class PotentialUser(models.Model):
    email = models.EmailField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    temporary_password = models.CharField(max_length=128, null=True, blank=True)  # Temporary password before approval

    def generate_temporary_password(self):
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))  # Generate a random password
        self.temporary_password = password
        return password

    def __str__(self):
        return f"{self.email}"


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    users = models.ManyToManyField('User', related_name='projects')

    def __str__(self):
        return self.name

class Document(models.Model):
    s3_file_name = models.CharField(max_length=2000, null=True, blank=True)
    file_name = models.CharField(max_length=500, null=True, blank=True)
    file_url = models.URLField(max_length=500, null=True, blank=True)  # Store the S3 URL here
    uploaded_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')

    def __str__(self):
        return str(self.file_url)

class DocumentMeta(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    hash_value = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    size_bytes = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=100, null=True, blank=True)
    is_directory = models.BooleanField(default=False, null=True, blank=True)
    creation_time = models.DateTimeField(null=True, blank=True)
    last_modified_time = models.DateTimeField(null=True, blank=True)
    last_accessed_time = models.DateTimeField(null=True, blank=True)
    permissions = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Meta for {self.document}"

class PageImage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='page_images/')

    def __str__(self):
        return f"Image for {self.document}"

class OCRText(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return f"OCR Text for {self.document}"

