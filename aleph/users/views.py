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
from mimetypes import guess_type
from users.ocr import perform_ocr
from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from .permissions import IsAdminUser
from django.utils import timezone
from helpers.s3 import *

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        user.last_login = timezone.now()
        user.save()

        _,token = AuthToken.objects.create(user)
        return Response({
            "user": serializer.data,
            "token": token
        })

class SingleUserDetailsAPIView(APIView):
    def get(self, request, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserViewSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MultipleUserDetailsAPIView(APIView):
    def get(self, request):
        users = User.objects.all()
        if not users:
            return Response({"error": "No users found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserViewSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.create(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserUpdateAPIView(APIView):
    def put(self, request, *args, **kwargs):
        try:
            user = User.objects.get(email=request.data.get('email'))
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(f"Data has been updated with these parameters: {serializer.data}", status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDeleteAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        try:
            user = User.objects.get(email=request.data.get('email'))
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response(f"User has been deleted successfully", status=status.HTTP_200_OK)

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

            # Upload file to S3
            file = request.FILES['file']  # Assuming the file is passed in the 'file' field
            s3_service = S3Service(region_name=os.getenv('REGION'), aws_access_key_id=os.getenv(
            'AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
            bucket_name = os.getenv('ALEPH_BUKCET')
            file_name = file.name

            # Save the file locally temporarily
            with open(file_name, 'wb+') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            # Upload to S3
            s3_service.s3_push(file_name, bucket_name, file_name)

            # Clean up the local file after upload
            os.remove(file_name)

            # Save the document information to the database with the S3 URL
            document_url = s3_service.get_document_url(s3_file=file_name, s3_bucket=bucket_name)
            document = serializer.save(project=project, file_url=document_url)

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

class ProjectCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            # Save the new project
            project = serializer.save()
            return Response({'project_id': project.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MultipleProjectDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,):
        projects = Project.objects.all()
        if not projects:
            return Response({"error": "No projects found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentDownloadAPIView(APIView):
    def get(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({'error': 'Document does not exist'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'document_url': document.file_url}, status=status.HTTP_200_OK)


class ProjectDocumentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve all documents associated with the project
        documents = Document.objects.filter(project=project)
        if documents:
            # Serialize the documents
            serializer = PageDocumentSerializer(documents, many=True)

            return Response(serializer.data)
        return Response({'error': 'Document does not exist against this project'}, status=status.HTTP_404_NOT_FOUND)

class PotentialUserCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = PotentialUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MultiplePotentialDetailsAPIView(APIView):
    def get(self, request):
        users = PotentialUser.objects.all()
        if not users:
            return Response({"error": "No potential users found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = PotentialUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ApproveUserAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        is_approved = data.get('is_approved')
        email = data.get('email')

        try:
            potential_user = PotentialUser.objects.get(email=email)
        except PotentialUser.DoesNotExist:
            return Response({'error': 'Potential user not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_approved:
            # Generate a password
            password = potential_user.generate_temporary_password()

            # Get the User model
            User = get_user_model()

            # Create the user
            user = User.objects.create_user(
                email=potential_user.email,
                password=password,
                first_name=potential_user.first_name,
                last_name=potential_user.last_name,
                group='admin',  # Default group or customize as needed
                status='active'
            )

            # Send email with the generated password
            send_mail(
                'Your Initial Password',
                f'Your initial password is: {password}',
                'talhaayub998@gmail.com',  # Sender's email address
                [user.email],  # Recipient's email address
                fail_silently=False,
            )

            # Delete the potential user entry
            potential_user.delete()

            return Response({'message': 'User approved and email sent'}, status=status.HTTP_200_OK)
        
        # If not approved, delete the potential user entry
        potential_user.delete()
        return Response({'message': 'User not approved and potential user entry deleted'}, status=status.HTTP_200_OK)


class CompanyCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        company_serializer = CompanySerializer(data=request.data)
        if company_serializer.is_valid():
            company = company_serializer.save()
            user_email = request.data.get('email')

            try:
                user = User.objects.get(email=user_email)
                user.company = company
                user.save()
                return Response(company_serializer.data, status=status.HTTP_201_CREATED)
            except User.DoesNotExist:
                company.delete()  # Clean up the created company if the user does not exist
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(company_serializer.errors, status=status.HTTP_400_BAD_REQUEST)