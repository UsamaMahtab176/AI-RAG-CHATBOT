from django.urls import path
from .views import (
    GetAllAdminsView,
    GetAllChatbotsForUserView,
    GetAllChatbotsForUserADminView,
    CreateConversationView,
    GetUserChatbotConversationsView,
    GetConversationMessagesView,
    DeleteConversationView,
    ContinueConversationView,
    RegenerateFromMessageWithEditView,
    DeleteConversationMessageView
)

urlpatterns = [
    path('user/admins/', GetAllAdminsView.as_view(), name='get_all_admins'),
    path('user/chatbots/', GetAllChatbotsForUserView.as_view(), name='get_all_chatbots_for_user'),
    path('user/chatbotsbyadmin/<int:admin_id>/', GetAllChatbotsForUserADminView.as_view(), name='get_chatbots_for_user_admin'),

    #create convo
    path('user/conversations/create/', CreateConversationView.as_view(), name='create_conversation'),

    #continue converastions
    path('conversations/<uuid:conversation_id>/continue/', ContinueConversationView.as_view(), name='continue_conversation'),
    #regenerate response
    path('conversations/<uuid:conversation_id>/messages/<uuid:message_id>/regenerate/', RegenerateFromMessageWithEditView.as_view(),name='regenerate_message_with_edit'),



    #get all conversations of chabot with user
    path('conversations/user-chatbot/', GetUserChatbotConversationsView.as_view(), name='user_chatbot_conversations'),
    #get specific conversation by id
    path('conversations/<uuid:conversation_id>/messages/', GetConversationMessagesView.as_view(), name='conversation_messages'),

    #delete convo
    path('conversations/delete/<uuid:conversation_id>/', DeleteConversationView.as_view(), name='delete_conversation'),

    #delete messsage by id
    path('conversations/<uuid:conversation_id>/messages/<uuid:message_id>/delete/', DeleteConversationMessageView.as_view(), name='delete_conversation_message')


]
