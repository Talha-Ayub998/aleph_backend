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
from helpers.checksum import *
import time

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

class PageDocumentUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = MultiplePageDocumentSerializer(data=request.data)
        if serializer.is_valid():
            # Retrieve the project from request data
            project_id = serializer.validated_data['project_id']
            files = serializer.validated_data['files']

            if not project_id:
                return Response({'error': 'Project ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response({'error': 'Project does not exist'}, status=status.HTTP_404_NOT_FOUND)

            s3_service = S3Service(
                region_name=os.getenv('REGION'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            bucket_name = os.getenv('ALEPH_BUCKET')

            document_ids = []
            for file in files:
                file_name = file.name
                temp_file_path = f"/tmp/{file_name}"

                # Save the file locally temporarily
                with open(temp_file_path, 'wb+') as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)

                try:
                    # Calculate the checksum of the file
                    file_hash = calculate_checksum(temp_file_path, file_name)

                    # Generate a unique key by appending a timestamp
                    unique_key = f"{file_hash}_{int(time.time())}"

                    # Upload to S3 using the unique key name
                    if s3_service.upload_to_s3(temp_file_path, bucket_name, unique_key):
                        # Clean up the local file after upload
                        os.remove(temp_file_path)

                        # Save the document information to the database with the S3 URL
                        document_url = s3_service.get_document_url(s3_file=unique_key, s3_bucket=bucket_name)

                        # Use PageDocumentSerializer to serialize the data before saving to the database
                        doc_serializer = PageDocumentSerializer(data={'file_url': document_url,
                                                                        's3_file_name': unique_key,
                                                                        'project': project.id,
                                                                        'file_name': file_name})
                        if doc_serializer.is_valid():
                            doc_serializer.save()
                            document_ids.append(doc_serializer.data['id'])
                        else:
                            return Response(doc_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # Ensure local file is removed in case of an error
                        os.remove(temp_file_path)
                        return Response({'error': f'Failed to upload {file_name} to S3'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    os.remove(temp_file_path)  # Ensure local file is removed in case of an error
                    return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'document_ids': document_ids}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RemoveS3FileAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        # Extract document ID from request parameters
        document_id = request.data.get('document_id')

        # Validate input
        if not document_id:
            return Response({'error': 'document_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Initialize the S3 client
            bucket_name = os.getenv('ALEPH_BUCKET')
            s3_client = S3Service(
                region_name=os.getenv('REGION'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )

            # Find the document in the database using the document ID
            document = Document.objects.get(id=document_id)
            if not document:
                return Response({'error': 'Document not found in the database'}, status=status.HTTP_404_NOT_FOUND)

            # Extract the S3 file key from the document's file URL
            s3_file_key = document.s3_file_name
            # Delete the file from S3
            if s3_client.delete_file(s3_file=s3_file_key, s3_bucket=bucket_name):
                # Delete the document from the database
                document.delete()
                return Response({'message': f'File {s3_file_key} removed successfully from {bucket_name}'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Failed to delete file from S3'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Document.DoesNotExist:
            return Response({'error': 'Document not found in the database'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        try:
            bucket_name = os.getenv('ALEPH_BUCKET')
            s3_client = S3Service(
                region_name=os.getenv('REGION'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            project_id = request.data.get('project_id')
            project = Project.objects.get(id=project_id)

            # Retrieve all documents associated with the project
            documents = project.documents.all()

            # Extract S3 file keys from the document objects
            file_keys = [document.s3_file_name for document in documents]

            # Delete documents from S3 in bulk
            s3_response = s3_client.bulk_delete_files(file_keys, bucket_name)

            # Check if deletion from S3 was successful
            if 'Errors' in s3_response:
                # Handle errors if any files failed to delete from S3
                error_files = [error['Key'] for error in s3_response['Errors']]
                return Response({'error': f'Failed to delete files from S3: {error_files}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Delete the project, which will also delete associated documents
            project.delete()

            return Response(f"Project and associated documents have been deleted successfully", status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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