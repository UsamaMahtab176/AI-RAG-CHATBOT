from django.urls import path
from account.views import ( SuperAdminSignupView,UserAdminSignupView,
    UserLoginView, UserAdminLoginView, SuperAdminLoginView,
    PasswordResetRequestView, PasswordResetConfirmView, ChangePasswordView,VerifyEmailView,ResendVerificationOTPView
)

urlpatterns = [
    # Signup Endpoints
    # path('signup/user/', UserSignupView.as_view(), name='user-signup'),
    path('signup/useradmin/', UserAdminSignupView.as_view(), name='user-signup'),
    path('resend-verification-otp/', ResendVerificationOTPView.as_view(), name='resend-verification-otp'),
    # path('signup/super-admin/', SuperAdminSignupView.as_view(), name='super-admin-signup'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    # Login Endpoints
    path('login/user/', UserLoginView.as_view(), name='user-login'),
    path('login/user-admin/', UserAdminLoginView.as_view(), name='user-admin-login'),
    path('login/super-admin/', SuperAdminLoginView.as_view(), name='super-admin-login'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # Change Password Endpoint
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]