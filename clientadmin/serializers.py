from rest_framework import serializers
from clientadmin.models import Chatbot, KnowledgeBase, GoogleDriveAccount

class KnowledgeBaseSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeBase
        fields = ['id', 'name',  'document_type', 'created_at', 'created_by','creator']
        read_only_fields = ['id', 's3_url', 'created_by', 'created_at','creator']

    def get_created_by(self, obj):
        return {
            'id': obj.created_by.id,
            'username': obj.created_by.username,
            'email': obj.created_by.email,
            'creator_id': obj.creator.id,
            'creator_username': obj.creator.username,
            'creator_email': obj.creator.email
        }
    def get_creator(self,obj):
        return {
            'id': obj.creator.id,
            'username': obj.creator.username,
            'email': obj.creator.email
        }

    


class ChatbotSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Chatbot
        fields = [
            'id', 'name', 'description', 'instructions', 'conversation_starter','model_name',
            'temperature', 'max_tokens', 'top_p', 'knowledge_base',
            'created_by', 'created_at', 'chatbot_profile_url',
            'category'  # Add the new category field here
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_created_by(self, obj):
        return {
            'id': obj.created_by.id,
            'username': obj.created_by.username,
            'email': obj.created_by.email
        }
    


class GoogleDriveAccountSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = GoogleDriveAccount
        fields = ['user', 'credentials', 'folder_id']
        read_only_fields = ['user', 'credentials']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }
