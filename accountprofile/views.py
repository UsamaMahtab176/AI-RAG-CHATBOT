from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from accountprofile.serializers import UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model





User = get_user_model()



class GetProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        user_data = {
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'country': user.country,
            'address': user.address,
            'user_staus': user.is_active,
            'profile_photo_url' : user.profile_photo_url,
            'role':user.role,
            'id':user.id
        }

        return Response(user_data, status=status.HTTP_200_OK)


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        # Extract the fields to update
        phone_number = request.data.get('phone_number')
        country = request.data.get('country')
        address = request.data.get('address')
        profile_photo_url=request.data.get('profile_photo_url')

        if phone_number:
            user.phone_number = phone_number

        if country:
            user.country = country

        if address:
            user.address = address
        if profile_photo_url:
            user.profile_photo_url = profile_photo_url


        user.save()

        return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
