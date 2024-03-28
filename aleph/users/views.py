from rest_framework.response import Response
from knox.models import AuthToken
from users.serializers import LoginSerializer
from rest_framework import generics

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

