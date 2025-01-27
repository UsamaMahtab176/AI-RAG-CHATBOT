from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from clientadmin.models import Chatbot
from account.models import User, UserAdminUserRelationship
from clientadmin.serializers import ChatbotSerializer,KnowledgeBaseSerializer
from account.serializers import UserSerializer
from clientadmin.models import KnowledgeBase
from superadmin.serializers import APISettingsSerializer


User = get_user_model()

# View for Super Admin to create a User Admin
class CreateUserAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        super_admin = request.user

        if not super_admin.is_super_admin:
            return Response({'error': 'Only Super Admins can create User Admins'}, status=status.HTTP_403_FORBIDDEN)

        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                try:
                    user_admin = User.objects.get(email=email)

                    if user_admin.is_super_admin:
                        return Response({
                        'error': 'You cannot add a Super Admin as a User Admin.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    

                    if user_admin.is_super_admin:
                        return Response({
                        'error': 'You cannot add a Super Admin as a User Admin.'
                    }, status=status.HTTP_400_BAD_REQUEST)


                    if user_admin.is_user_admin:
                        return Response({
                        'message': 'This user is already a User Admin.',
                        'email': user_admin.email,
                        'user_status': user_admin.is_active
                    }, status=status.HTTP_200_OK)

                    
                except User.DoesNotExist:
                    user_admin = User.objects.create(
                        username=email,
                        email=email,
                        is_active=False,
                        password_reset_token=get_random_string(20),
                        is_user_admin=True
                    )
                    user_created = True
                else:
                    user_created = False

                

                

                if user_created:
                    setup_link = "https://ai-rag-client-admin-git-staging-octalooptechnologies-projects.vercel.app/setup-account"
                    send_mail(
                        'Set Up Your User Admin Account Password',
                        f'Hello,\n\nYour User Admin account has been created by the Super Admin. Please set your password by following this link:\n\n{setup_link}\n\nYour token is {user_admin.password_reset_token} \n\nThis link will expire in 24 hours.',
                        'no-reply@example.com',
                        [user_admin.email],
                        fail_silently=False,
                    )
                    return Response({
                        'message': 'User Admin invitation sent.',
                        'email': user_admin.email,
                        'user_status': user_admin.is_active,
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'message': 'User Admin already existed.',
                        'email': user_admin.email,
                        'user_status': user_admin.is_active,
                    }, status=status.HTTP_200_OK)

        except IntegrityError:
            return Response({'error': 'A user with this email or username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from helper.helper import PineconeInitializer
import os
class SetUserAdminPasswordView(APIView):
    def post(self, request, token):
        try:
            user_admin = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        token_age = timezone.now() - user_admin.date_joined
        if token_age.total_seconds() > 86400:
            return Response({'error': 'Token has expired'}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('password')
        username = request.data.get('username')
        if not new_password or not username:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if User.objects.filter(username=username).exists():
                return Response({'error': 'Username already taken, please choose another.'}, status=status.HTTP_400_BAD_REQUEST)

            user_admin.set_password(new_password)
            user_admin.username = username
            user_admin.is_active = True
            user_admin.password_reset_token = ''
            user_admin.save()

            if not user_admin.pinecone_index:
                api_settings = APISettings.objects.first()
                if not api_settings:
                    return Response({'error': 'API settings not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Use stored or environment API keys
                OPENAI_API_KEY = api_settings.openai_api_key or os.getenv("OPENAI_API_KEY")
                PINECONE_API_KEY = api_settings.pinecone_api_key or os.getenv("PINECONE_API_KEY")
                
                # Initialize Pinecone index for the user
                pinecone_initializer = PineconeInitializer(pinecone_api=PINECONE_API_KEY, open_ai_api=OPENAI_API_KEY)
                index_name = f"index-{user_admin.id}"  # Unique index name for each user
                pinecone_initializer.initialize_pinecone(index_name)  # Initialize the index
                
                # Save the index name to the user model
                user_admin.pinecone_index = index_name
                user_admin.save()

                return Response({
                    'message': 'Password has been set successfully and Pinecone index has been created.',
                    'pinecone_index': index_name
                }, status=status.HTTP_200_OK)
            

            
            else:
                
                return Response({
                    'message': 'Password has been set successfully. Pinecone index already exists.',
                    'pinecone_index': user_admin.pinecone_index
                }, status=status.HTTP_200_OK)
            

        except IntegrityError:
            return Response({'error': 'An error occurred while setting the password. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListUserAdminsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        super_admin = request.user

        if not super_admin.is_super_admin:
            return Response({'error': 'Only Super Admin can view this list'}, status=status.HTTP_403_FORBIDDEN)

        user_admins = User.objects.filter(is_user_admin=True)
        user_admins_data = [{'user_id': user_admin.id, 'username': user_admin.username, 'email': user_admin.email, 'profile_image': user_admin.profile_photo_url, 'user_status': user_admin.is_active} for user_admin in user_admins]

        return Response({'user_admins': user_admins_data}, status=status.HTTP_200_OK)



class DeleteUserAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        super_admin = request.user

        if not super_admin.is_super_admin:
            return Response({'error': 'Only Super Admins can delete User Admins'}, status=status.HTTP_403_FORBIDDEN)

        user_admin_to_delete = get_object_or_404(User, id=user_id, is_user_admin=True)

        if user_admin_to_delete.is_super_admin:
            return Response({'error': 'You cannot delete a Super Admin'}, status=status.HTTP_403_FORBIDDEN)

        user_admin_to_delete.delete()

        return Response({'message': 'User Admin deleted successfully'}, status=status.HTTP_200_OK)














#dashboard

class SuperAdminStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_super_admin:
            return Response({'error': 'Only Super Admins can access this data'}, status=status.HTTP_403_FORBIDDEN)

        # Get total users and admins
        total_users = User.objects.count()
        total_admins = User.objects.filter(is_user_admin=True).count()

        # Get the time from one week ago
        one_week_ago = timezone.now() - timedelta(days=7)

        # Calculate the difference in user and admin numbers from the past week
        users_week_ago = User.objects.filter(date_joined__lte=one_week_ago).count()
        admins_week_ago = User.objects.filter(is_user_admin=True, date_joined__lte=one_week_ago).count()

        user_diff = total_users - users_week_ago
        admin_diff = total_admins - admins_week_ago


         # Total number of chatbots
        total_chatbots = Chatbot.objects.count()
        chatbots_by_model = Chatbot.objects.values('model_name').annotate(model_count=Count('model_name'))
        # Prepare response data
        data = {
            'total_users': total_users,
            'total_admins': total_admins,
            'user_diff_from_past_week': user_diff,
            'admin_diff_from_past_week': admin_diff,
            'total_chatbots': total_chatbots,
            'chatbots_by_model': chatbots_by_model,  # Chatbots count by model_name
        }

        return Response(data, status=status.HTTP_200_OK)

class UserAdminStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_super_admin:
            return Response({'error': 'Only Super Admins can access this data'}, status=status.HTTP_403_FORBIDDEN)

        # Aggregate the number of users, chatbots, and knowledge bases for each user admin
        user_admins = User.objects.filter(is_user_admin=True).annotate(
            total_users=Count('created_users_relationships__user'),
            total_chatbots=Count('chatbots'),
            total_knowledge_bases=Count('knowledge_bases')
        )

        user_admin_data = []
        for admin in user_admins:
            user_admin_data.append({
                'admin_id': admin.id,
                'admin_username': admin.username,
                'admin_email': admin.email,
                'total_users': admin.total_users,
                'total_chatbots': admin.total_chatbots,
                'total_knowledge_bases': admin.total_knowledge_bases
            })

        return Response({'user_admins': user_admin_data}, status=status.HTTP_200_OK)

    


class UserAdminDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_admin_id):
        # Ensure that only super admins can access this view or the current user is the same admin
        if not request.user.is_super_admin and request.user.id != user_admin_id:
            return Response({'error': 'Only Super Admins or the specific User Admin can view this information'}, status=status.HTTP_403_FORBIDDEN)

        # Get the User Admin
        user_admin = get_object_or_404(User, id=user_admin_id, is_user_admin=True)
        #tester
        # Fetch chatbots created by this User Admin
        chatbots = Chatbot.objects.filter(created_by=user_admin)
        chatbot_serializer = ChatbotSerializer(chatbots, many=True)

        # Fetch users associated with this User Admin via UserAdminUserRelationship
        user_relationships = UserAdminUserRelationship.objects.filter(user_admin=user_admin)
        associated_users = [relationship.user for relationship in user_relationships]
        user_serializer = UserSerializer(associated_users, many=True)

        # Fetch knowledge bases created by this User Admin
        knowledge_bases = KnowledgeBase.objects.filter(created_by=user_admin)
        knowledge_base_serializer = KnowledgeBaseSerializer(knowledge_bases, many=True)

        # Prepare the response data
        response_data = {
            'user_admin_id': user_admin.id,
            'user_admin_username': user_admin.username,
            'user_admin_email': user_admin.email,
            'chatbots': chatbot_serializer.data,
            'users': user_serializer.data,
            'knowledge_bases': knowledge_base_serializer.data  # Added knowledge bases
        }

        return Response(response_data, status=status.HTTP_200_OK)
    








from superadmin.models import APISettings

class UpdateAPISettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_super_admin:
            return Response({'error': 'Only Super Admins or the specific User Admin can view this information'}, status=status.HTTP_403_FORBIDDEN)
        # Retrieve or create API settings for the user
        api_settings, created = APISettings.objects.get_or_create(user=request.user)
        
        # Use serializer to validate and update API credentials
        serializer = APISettingsSerializer(api_settings, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'API credentials updated successfully.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




class GetAPISettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_super_admin:
            return Response({'error': 'Only Super Admins or the specific User Admin can view this information'}, status=status.HTTP_403_FORBIDDEN)
        # Retrieve the single instance of APISettings
        api_settings = get_object_or_404(APISettings)
        serializer = APISettingsSerializer(api_settings)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

from superadmin.validators import validate_openai_api_key, validate_pinecone_api_key, validate_claude_api_key
from superadmin.serializers import APISettingsSerializer



class UpdateAPISettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        # Retrieve the single instance of APISettings
        api_settings = get_object_or_404(APISettings)
        data = request.data
        validation_results = {}

        # Validate OpenAI API Key if provided
        if 'openai_api_key' in data:
            if validate_openai_api_key(data['openai_api_key']):
                api_settings.openai_api_key = data['openai_api_key']
                validation_results['openai_api_key'] = "Valid and updated"
            else:
                validation_results['openai_api_key'] = "Invalid API key or please check your balance"

        # Validate Pinecone API Key if provided
        if 'pinecone_api_key' in data:
            if validate_pinecone_api_key(data['pinecone_api_key']):
                api_settings.pinecone_api_key = data['pinecone_api_key']
                validation_results['pinecone_api_key'] = "Valid and updated"
            else:
                validation_results['pinecone_api_key'] = "Invalid API key or please check your balance"

        # Validate Claude API Key if provided
        if 'claude_api_key' in data:
            if validate_claude_api_key(data['claude_api_key']):
                api_settings.claude_api_key = data['claude_api_key']
                validation_results['claude_api_key'] = "Valid and updated"
            else:
                validation_results['claude_api_key'] = "Invalid API key or please check your balance"

        # Save only if there are valid updates
        if "Valid and updated" in validation_results.values():
            api_settings.save()

        # Return validation results
        return Response(validation_results, status=status.HTTP_200_OK)