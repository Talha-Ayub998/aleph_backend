from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.serializers import LoginSerializer
from django.contrib.auth.hashers import check_password

# class LoginAPIView(APIView):
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             password = serializer.validated_data['password']
#             user = authenticate(request, email=email, password=password)  # Authenticate using email
#             if user and check_password(password, user.password):
#                 login(request, user)
#                 return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
#             else:
#                 return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.models import User  # Import your custom User model
from backend.serializers import LoginSerializer

class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('email')
        user = get_object_or_404(User, email=email)  # Fetch user by email
        if password == user.password:  # Compare entered password with stored password
            # Authentication successful
            # Implement your custom login logic here, if needed
            return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        else:
            # Authentication failed due to incorrect password
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

