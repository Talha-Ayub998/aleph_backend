from django.contrib import admin
from .models import *

class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'email', 'is_staff', 'is_superuser']

class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'file_url', 'uploaded_at', 's3_file_name', 'file_name', 'project']

class DocumentMetaAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'hash_value']

class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'get_user_emails']

    def get_user_emails(self, obj):
        return ", ".join([user.email for user in obj.users.all()])

class PageImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'document']

class OCRTextAdmin(admin.ModelAdmin):
    list_display = ['id', 'document']

admin.site.register(User, UserAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(DocumentMeta, DocumentMetaAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(PageImage, PageImageAdmin)
admin.site.register(OCRText, OCRTextAdmin)
