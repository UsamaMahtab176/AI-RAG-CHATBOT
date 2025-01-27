from django.urls import path
from superadmin.views import CreateUserAdminView, SetUserAdminPasswordView, ListUserAdminsView, DeleteUserAdminView,SuperAdminStatsView,UserAdminStatsView,UserAdminDetailsView,GetAPISettingsView,UpdateAPISettingsView

urlpatterns = [
    path('create-user-admin/', CreateUserAdminView.as_view(), name='create-user-admin'),
    path('set-user-admin-password/<str:token>/', SetUserAdminPasswordView.as_view(), name='set-user-admin-password'),
    path('list-user-admins/', ListUserAdminsView.as_view(), name='list-user-admins'),
    path('delete-user-admin/<int:user_id>/', DeleteUserAdminView.as_view(), name='delete-user-admin'),



    #dashboard
    path('superadmin/stats/', SuperAdminStatsView.as_view(), name='super_admin_stats'),
    path('superadmin/user-admin-stats/', UserAdminStatsView.as_view(), name='user_admin_stats'),
    path('useradmin/details/<int:user_admin_id>/', UserAdminDetailsView.as_view(), name='user_admin_details'),


    #credentials get 
    path('api-settings/', GetAPISettingsView.as_view(), name='get_api_settings'),
    path('api-settings/update/', UpdateAPISettingsView.as_view(), name='update_api_settings'),
]