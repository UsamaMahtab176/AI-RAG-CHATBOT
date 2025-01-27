from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string

class User(AbstractUser):
    ROLE_CHOICES = [
        ('tester', 'Tester'),
        ('editor', 'Editor'),
    ]
    
    email = models.EmailField(unique=True)
    is_user_admin = models.BooleanField(default=False)
    is_super_admin = models.BooleanField(default=False)
    profile_photo_url = models.URLField(max_length=1024, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    password_reset_token = models.CharField(max_length=50, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='tester')  
    pinecone_index = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username
    

class UserAdminUserRelationship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_relationships')
    user_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_users_relationships')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'user_admin')
        
class EmailVerificationOTP(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def generate_otp(self):
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.expires_at = timezone.now() + timezone.timedelta(minutes=500)
        self.save()


class PasswordResetOTP(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def generate_otp(self):
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        self.save()  # Ensure expires_at is set and then save

    def save(self, *args, **kwargs):
        # First, call the original save method to populate created_at
        if not self.created_at:
            self.created_at = timezone.now()

        if not self.expires_at:
            self.expires_at = self.created_at + timezone.timedelta(minutes=10)

        # Save the instance
        super(PasswordResetOTP, self).save(*args, **kwargs)
