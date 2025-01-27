from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_user_admin', 'is_super_admin']
        extra_kwargs = {
            'password': {'write_only': True}
        }