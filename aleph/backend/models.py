from django.db import models
from django.utils import timezone
import random

class User(models.Model):
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
    email = models.CharField(max_length=50, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.CharField(max_length=10, choices=GROUP_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    last_login = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
            if not self.pk:  # Only generate user_id if the instance is being created (not updated)
                self.user_id = self._generate_user_id()
            super().save(*args, **kwargs)

    def _generate_user_id(self):
        # Generate a random 3-digit ID
        return str(random.randint(100, 999))

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['-created_at']


class Project(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.name


class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class OCRText(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    raw_text = models.TextField()

    def __str__(self):
        return f"OCR Text for {self.document}"

