from django.contrib import admin
from .models import User,Document,Project,DocumentMeta,PageImage,OCRText


class UserAdmin(admin.ModelAdmin):
    list_display=['id','user_id','email','is_staff','is_superuser']

class DocumentAdmin(admin.ModelAdmin):
    list_display=['id','file','uploaded_at']

class DocumentMetaAdmin(admin.ModelAdmin):
    list_display=['id','document','hash_value']

class ProjectAdmin(admin.ModelAdmin):
    list_display=['id','name','user']

class PageImageAdmin(admin.ModelAdmin):
    list_display=['id','image','document']

class OcrTextAdmin(admin.ModelAdmin):
    list_display=['id','document']

admin.site.register(User,UserAdmin)
admin.site.register(Document,DocumentAdmin)
admin.site.register(DocumentMeta,DocumentMetaAdmin)
admin.site.register(Project,ProjectAdmin)
admin.site.register(PageImage,PageImageAdmin)
admin.site.register(OCRText,OcrTextAdmin)
