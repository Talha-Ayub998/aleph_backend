from knox.models import AuthToken
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users.serializers import *
from rest_framework.response import Response
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics
from users.ocr import perform_ocr

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        _,token = AuthToken.objects.create(user)
        return Response({
            "user": serializer.data,
            "token": token
        })

class PageImageView(APIView):
    def get(self, request, image_id):
        # Retrieve the PageImage object
        page_image = get_object_or_404(PageImage, id=image_id)
        # Open and return the image file
        return FileResponse(page_image.image, content_type='image/jpeg')

class PageDocumentUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PageDocumentSerializer(data=request.data)
        if serializer.is_valid():
            # Retrieve the project from request data
            project_id = request.data.get('project_id')
            if not project_id:
                return Response({'error': 'Project ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response({'error': 'Project does not exist'}, status=status.HTTP_404_NOT_FOUND)

            # Save the document with the associated project
            document = serializer.save(project=project)
            return Response({'document_id': document.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PageDocumentImagesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        document_id = self.kwargs['document_id']
        return PageImage.objects.filter(document_id=document_id)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        image_urls = [page_image.image.url for page_image in queryset]
        return JsonResponse({'image_urls': image_urls})