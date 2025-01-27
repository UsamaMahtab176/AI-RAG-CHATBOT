from django.urls import path
from accountprofile.views import LogoutView,UpdateProfileView,GetProfileView

urlpatterns = [
    path('profileinfo/', GetProfileView.as_view(), name='user-profile'),
    path('updateprofileinfo/', UpdateProfileView.as_view(), name='user-profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
]