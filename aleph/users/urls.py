from .views import *
from django.urls import path

urlpatterns = [
    path('api/login/', LoginAPIView.as_view(), name='api-login'),
    path('api/view_page_image/<int:image_id>/', PageImageView.as_view(), name='api-view-page-image'),
    path('api/upload_document/', PageDocumentUploadAPIView.as_view(), name='api-upload-document'),
    path('api/document_images/<int:document_id>/', PageDocumentImagesAPIView.as_view(), name='document_images'),
    path('api/create_project/', ProjectCreateAPIView.as_view(), name='api-create-project'),
]
