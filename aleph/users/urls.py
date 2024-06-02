from .views import *
from django.urls import path

urlpatterns = [
    path('api/login/', LoginAPIView.as_view(), name='api-login'),
    path('api/users/create/', UserCreateAPIView.as_view(), name='user-create'),
    path('api/users/update/', UserUpdateAPIView.as_view(), name='user-update'),
    path('api/users/delete/', UserDeleteAPIView.as_view(), name='user-delete'),
    path('api/users/<str:email>/', SingleUserDetailsAPIView.as_view(), name='user-details'),
    path('api/all/users/', MultipleUserDetailsAPIView.as_view(), name='all-user-details'),
    path('api/upload_document/', PageDocumentUploadAPIView.as_view(), name='api-upload-document'),
    path('api/create_project/', ProjectCreateAPIView.as_view(), name='api-create-project'),
    path('api/view_projects/', MultipleProjectDetailsAPIView.as_view(), name='api-project-details'),
    path('api/project_documents/<int:project_id>/', ProjectDocumentsAPIView.as_view(), name='api-project-documents'),
    path('api/remove-project', ProjectDeleteAPIView.as_view(), name='api-project-delete'),
    path('api/download_document/<int:document_id>/', DocumentDownloadAPIView.as_view(), name='api-download-document'),
    path('api/remove-s3-file/', RemoveS3FileAPIView.as_view(), name='remove_s3_file'),
    path('api/signup/', PotentialUserCreateAPIView.as_view(), name='potential-user-signup'),
    path('api/approve/', ApproveUserAPIView.as_view(), name='approve-user'),
    path('api/all/potential/users/', MultiplePotentialDetailsAPIView.as_view(), name='all-potential-user-details'),
    path('api/companies/create/', CompanyCreateAPIView.as_view(), name='company-create'),

]
