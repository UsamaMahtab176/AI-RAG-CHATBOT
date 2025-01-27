from django.db import models
from django.conf import settings
import uuid
from account.models import User

class KnowledgeBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500)
    namespace = models.CharField(max_length=500)
    document_type = models.CharField(max_length=10)
    k_type = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='knowledge_bases')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_knowledge_bases')  # The editor or admin
    created_at = models.DateTimeField(auto_now_add=True)  # Correct field name
    # New field to store Google Drive folder ID for this knowledge base
    google_drive_folder_id = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return self.name
    

class KnowledgeBaseDocument(models.Model):
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=255)  # New field to store the document's name
    s3_url = models.URLField(max_length=1024)
    document_type = models.CharField(max_length=100, default='pdf')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document {self.document_name} in {self.knowledge_base.name} - {self.document_type}"


class Chatbot(models.Model):
    MODEL_CHOICES = [
        ('gpt-3.5-turbo-0125', 'GPT-3.5 Turbo 0125'),
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4o-mini', 'GPT-4o Mini'),
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        # Claude-3 models
        ('claude-3-sonnet-20240229', 'Claude 3 Sonnet 20240229'),
        ('claude-3-haiku-20240307', 'Claude 3 Haiku 20240307'),
        ('claude-3-opus-20240229', 'Claude 3 Opus 20240229'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=30, choices=MODEL_CHOICES, default='gpt-3.5-turbo')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)
    conversation_starter = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chatbots')
    created_at = models.DateTimeField(auto_now_add=True)  # Correct field name
    chatbot_profile_url = models.URLField(max_length=1024)
    category = models.CharField(max_length=100, null=True, blank=True)

    # Knowledge base fields
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.SET_NULL, null=True, blank=True, related_name='chatbots')

    # Parameters
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=150)
    top_p = models.FloatField(default=0.9)

    def __str__(self):
        return self.name
    


# GDive Creds Model
class GoogleDriveAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credentials = models.TextField()  # OAuth tokens (access and refresh) stored securely
    # folder_id = models.CharField(max_length=255, null=True, blank=True)  # The ID of the selected Google Drive folder

    def __str__(self):
        return f"{self.user.username}'s Google Drive Account"
    







class MicrosoftAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='microsoft_account')
    credentials = models.JSONField()

    def __str__(self):
        return f"MicrosoftAccount for {self.user.username}"