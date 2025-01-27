from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from django.core.mail import send_mail
from .models import EmailVerificationOTP,PasswordResetOTP
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# class UserSignupView(APIView):
#     def post(self, request):
#         data = request.data
#         data['is_user_admin'] = False
#         data['is_super_admin'] = False
#         serializer = UserSerializer(data=data)
#         if serializer.is_valid():
#             user = serializer.save()
#             user.set_password(data['password'])
#             user.is_active = False  # Make the user inactive until email is verified
#             user.save()

#             # Generate and send OTP for email verification
#             otp = EmailVerificationOTP(user=user)
#             otp.generate_otp()

#             send_mail(
#                 'Your OTP Code',
#                 f'Your OTP code is {otp.otp_code}',
#                 'from@example.com',
#                 [user.email],
#                 fail_silently=False,
#             )
#             return Response({'message': 'User created, please verify your email'}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class UserAdminSignupView(APIView):
    def post(self, request):
        data = request.data
        data['is_user_admin'] = True
        data['is_super_admin'] = False
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(data['password'])
            user.is_active = False
            user.save()

            # Generate and send OTP for email verification
            otp = EmailVerificationOTP(user=user)
            otp.generate_otp()

            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp.otp_code}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
            return Response({'message': 'User admin created, please verify your email'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ResendVerificationOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
            
            # Ensure that the user is not already active
            if user.is_active:
                return Response({'error': 'User is already verified'}, status=status.HTTP_400_BAD_REQUEST)

            otp, created = EmailVerificationOTP.objects.get_or_create(user=user)

            # If the OTP is expired or created newly, regenerate it
            if otp.expires_at < timezone.now() or created:
                otp.generate_otp()

            # Resend the OTP via email
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp.otp_code}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
            return Response({'message': 'OTP has been resent to your email'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)


class SuperAdminSignupView(APIView):
    def post(self, request):
        data = request.data
        data['is_user_admin'] = False
        data['is_super_admin'] = True
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(data['password'])
            user.is_active = False
            user.save()

            # Generate and send OTP for email verification
            otp = EmailVerificationOTP(user=user)
            otp.generate_otp()

            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp.otp_code}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
            return Response({'message': 'Super admin created, please verify your email'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



class UserLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            # Check if the user exists and is not an admin or super admin
            user = User.objects.get(email=email)
            if user.is_user_admin or user.is_super_admin:
                return Response({'error': 'Invalid credentials or incorrect role'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Authenticate the user
            user = authenticate(request, username=user.username, password=password)
            if user:
                if not user.is_active:
                    return Response({'error': 'Email not verified'}, status=status.HTTP_400_BAD_REQUEST)

                # Generate tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'id': user.id,
                    'role':user.role,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)


class UserAdminLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            # Check if a user exists with the specified email and is a user admin
            user = User.objects.get(email=email, is_user_admin=True)
            
            # Check if the user's email is verified (is_active is True)
            if not user.is_active:
                return Response({'error': 'email not verified'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Authenticate the user
            user = authenticate(request, username=user.username, password=password)
            if user:
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'id': user.id,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist:
            return Response({'error': 'User Admin does not exist or incorrect email'}, status=status.HTTP_404_NOT_FOUND)
        
        
class SuperAdminLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            # Check if the user exists and is a super admin
            user = User.objects.get(email=email, is_super_admin=True)
            
            # Authenticate the user
            user = authenticate(request, username=user.username, password=password)
            if user:
                if not user.is_active:
                    return Response({'error': 'Email not verified'}, status=status.HTTP_400_BAD_REQUEST)

                # Generate tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'id': user.id,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_404_NOT_FOUND)




class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
            
            # Generate and send OTP for password reset
            otp, created = PasswordResetOTP.objects.get_or_create(user=user)
            otp.generate_otp()  # This will now correctly set otp_code and expires_at

            send_mail(
                'Your Password Reset OTP',
                f'Your OTP code is {otp.otp_code}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
            return Response({'message': 'Password reset OTP sent to your email'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')
        new_password = request.data.get('new_password')

        try:
            user = User.objects.get(email=email)
            otp = PasswordResetOTP.objects.get(user=user)

            if otp.expires_at < timezone.now():
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

            if otp.otp_code == otp_code:
                user.password = make_password(new_password)
                user.save()

                # OTP verified and password reset, so delete the OTP
                otp.delete()

                return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except PasswordResetOTP.DoesNotExist:
            return Response({'error': 'OTP does not exist or has already been used'}, status=status.HTTP_404_NOT_FOUND)
        



class VerifyEmailView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')

        try:
            user = User.objects.get(email=email)
            otp = EmailVerificationOTP.objects.get(user=user)

            if otp.expires_at < timezone.now():
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

            if otp.otp_code == otp_code:
                user.is_active = True
                user.save()

                otp.delete()  # OTP verified and email confirmed, so delete it

                return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except EmailVerificationOTP.DoesNotExist:
            return Response({'error': 'OTP does not exist or has already been used'}, status=status.HTTP_404_NOT_FOUND)







# User = get_user_model()

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # Authenticate the user with the old password
        if not user.check_password(old_password):
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password has been changed successfully'}, status=status.HTTP_200_OK)