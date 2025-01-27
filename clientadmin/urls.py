from django.urls import path
from clientadmin.views import (
    CreateUserView,
    SetPasswordView,
    ListUsersCreatedByAdminView,
    UserChatbotAccessView,
    DeleteUserView,
    CreateKnowledgeBaseView,
    DeleteKnowledgeBaseView,
    KnowledgeBaseDetailView,
    UpdateKnowledgeBaseView,
    ListKnowledgeBasesView,
    CreateChatbotView,
    UpdateChatbotView,
    DeleteChatbotView,
    ListChatbotsView,
    GetChatbotByIdView,
    UpdateUserRoleView,
    GetUserDetailsView,
    ViewNamespaceView,
    UpdateVector,
    DeleteVectorView,
    GoogleDriveInitView,
    GoogleDriveCallbackView,
    GoogleDriveFolderFilesView,
    UploadFileToS3View,
    MicrosoftInitView,
    MicrosoftCallbackView,
    RecreatePineConeIndexView,
    CheckUserPineconeIndexView,
    CreateEmptyPineConeIndexView
    # SaveGoogleDriveCredentialsView
)

urlpatterns = [
    # User Management
    path('useradmin/createuser/', CreateUserView.as_view(), name='create_user'),
    path('useradmin/user-set-password/<str:token>/', SetPasswordView.as_view(), name='set_password'),
    path('useradmin/getallusers/', ListUsersCreatedByAdminView.as_view(), name='list_users'),
    path('users/chatbots-access/', UserChatbotAccessView.as_view(), name='user_chatbot_access'),
    path('useradmin/delete/<int:user_id>/', DeleteUserView.as_view(), name='delete_user'),

    # Knowledge Base Management
    path('useradmin/knowledge-base/create/', CreateKnowledgeBaseView.as_view(), name='create_knowledge_base'),
    path('useradmin/knowledge-base/check/', CheckUserPineconeIndexView.as_view(), name='check_user_pinecone_index'),
    path('useradmin/knowledge-base/delete/<uuid:knowledge_base_id>/', DeleteKnowledgeBaseView.as_view(), name='delete_knowledge_base'),
    path('useradmin/get-knowledge-base/<uuid:knowledge_base_id>/', KnowledgeBaseDetailView.as_view(), name='knowledge_base_detail'),
    path('useradmin/knowledge-base/update/<uuid:knowledge_base_id>/', UpdateKnowledgeBaseView.as_view(), name='update_knowledge_base'),
    path('useradmin/getallknowledge-bases/', ListKnowledgeBasesView.as_view(), name='list_knowledge_bases'),

    # Chatbot Management
    path('useradmin/chatbot/create/', CreateChatbotView.as_view(), name='create_chatbot'),
    path('useradmin/chatbot/update/<uuid:chatbot_id>/', UpdateChatbotView.as_view(), name='update_chatbot'),
    path('useradmin/chatbot/delete/<uuid:chatbot_id>/', DeleteChatbotView.as_view(), name='delete_chatbot'),
    path('useradmin/getallchatbots/', ListChatbotsView.as_view(), name='list_chatbots'),
    path('useradmin/get-chatbot/<uuid:chatbot_id>/', GetChatbotByIdView.as_view(), name='get_chatbot_by_id'),

    #User k Roles
    path('useradmin/update-user-role/<int:user_id>/', UpdateUserRoleView.as_view(), name='update_user_role'),
    path('useradmin/userdetails/<int:user_id>/', GetUserDetailsView.as_view(), name='get_user_details'),
    
    #namespace vector view
    path('useradmin/namespaceview/', ViewNamespaceView.as_view(), name='name_space_view'),
    path('knowledgebase/vector/update/', UpdateVector.as_view(), name='update_vector'),
    path('vectors/delete/<int:admin_id>/<str:vector_id>/<str:namespace>/', DeleteVectorView.as_view(), name='delete_vector'),

    #google-drive endpoints
    path('google-drive/init/', GoogleDriveInitView.as_view(), name='google_drive_init'),  # Starts OAuth flow
    path('google-drive/oauth2callback/', GoogleDriveCallbackView.as_view(), name='google_drive_callback'),  # OAuth callback handler
    path('google-drive/folder-files-View/', GoogleDriveFolderFilesView.as_view(), name='google-drive-folder-files'),
    # path('google-drive/save-credentials/', SaveGoogleDriveCredentialsView.as_view(), name='save_google_drive_credentials'),

    # Upload files to s3 bucket
    path('upload-to-s3/', UploadFileToS3View.as_view(), name='upload_to_s3'),

    # Microsoft Sharepoint endpoints ...
    path('microsoft/init/', MicrosoftInitView.as_view(), name='microsoft-init'),
    path('microsoft/callback/', MicrosoftCallbackView.as_view(), name='microsoft-callback'),

    # Pinecone endpoints 
    path('useradmin/recreate-pinecone-index/', RecreatePineConeIndexView.as_view(), name='recreate_pinecone_index'),
    path('useradmin/create-empty-pinecone-index/', CreateEmptyPineConeIndexView.as_view(), name='create_empty_pinecone_index'),
]

# google-drive/folder-files/
