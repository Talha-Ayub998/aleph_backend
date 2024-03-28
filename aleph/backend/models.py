from django.db import models
from django.utils import timezone
import random

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import User
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

class User(AbstractBaseUser):
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

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
        if not self.pk:  # Only generate user_id if the instance is being created (not updated)
            self.user_id = self._generate_user_id()
        super().save(*args, **kwargs)

    def _generate_user_id(self):
        # Generate a random 3-digit ID
        return str(random.randint(100, 999))

    def __str__(self):
        return f"{self.email}"

    class Meta:
        ordering = ['-created_at']


class Project(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.name

class Document(models.Model):
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.file)

class DocumentMeta(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    hash_value = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Meta for {self.document}"

class PageImage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='page_images/')

    def __str__(self):
        return f"Image for {self.document}"

class OCRText(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return f"OCR Text for {self.document}"

