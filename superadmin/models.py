from django.db import models
from django.contrib.auth.models import User

class APISettings(models.Model):
    openai_api_key = models.CharField(max_length=255, blank=True, null=True)
    pinecone_api_key = models.CharField(max_length=255, blank=True, null=True)
    claude_api_key = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and APISettings.objects.exists():
            raise ValueError("Only one APISettings instance is allowed.")
        super(APISettings, self).save(*args, **kwargs)

    def __str__(self):
        return f"API Settings"
