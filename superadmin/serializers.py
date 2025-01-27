from rest_framework import serializers
from .models import APISettings

class APISettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = APISettings
        fields = ['openai_api_key', 'pinecone_api_key', 'claude_api_key']