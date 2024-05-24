import random
import string
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import fitz  # PyMuPDF
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import io
import os


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
    contact = models.CharField(max_length=30)
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
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')

    def __str__(self):
        return str(self.file)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        file_extension = os.path.splitext(self.file.name)[1].lower()
        
        if file_extension == '.pdf':
            # Handle PDF files
            pdf_path = self.file.path
            doc = fitz.open(pdf_path)
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG')
                img_content = ContentFile(img_io.getvalue(), f"{self.file.name}_{page_num+1}.jpg")
                PageImage.objects.create(document=self, image=img_content)
            doc.close()
        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            # Handle image files
            with open(self.file.path, 'rb') as f:
                img_content = ContentFile(f.read(), self.file.name)
                PageImage.objects.create(document=self, image=img_content)
        elif file_extension == '.txt':
            # Handle text files
            with open(self.file.path, 'r') as f:
                # Create an image with text content
                img = Image.new('RGB', (800, 600), color='white')
                d = ImageDraw.Draw(img)
                font = ImageFont.load_default()
                text = f.read()
                d.text((10, 10), text, fill='black', font=font)
                
                # Save the image
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG')
                img_content = ContentFile(img_io.getvalue(), f"{self.file.name}.jpg")
                PageImage.objects.create(document=self, image=img_content)

class DocumentMeta(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    hash_value = models.CharField(max_length=255, unique=True)

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

