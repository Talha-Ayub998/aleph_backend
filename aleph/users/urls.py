from django.urls import path
from .views import LoginAPIView, PageImageUploadAPIView, PageImageView

urlpatterns = [
    path('api/login/', LoginAPIView.as_view(), name='api-login'),
    path('api/upload_page_image/', PageImageUploadAPIView.as_view(), name='api-upload-page-image'),
    path('api/view_page_image/<int:image_id>/', PageImageView.as_view(), name='api-view-page-image'),
]
