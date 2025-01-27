from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from clientadmin.models import Chatbot, KnowledgeBase
from clientuser.models import Conversation,Message
from clientadmin.serializers import ChatbotSerializer, KnowledgeBaseSerializer
from django.shortcuts import get_object_or_404
from account.models import UserAdminUserRelationship
from django.conf import settings
from langchain_openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from helper.helper import PineconeInitializer
import logging
from langchain_anthropic import ChatAnthropic
import os
from superadmin.models import APISettings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)



class GetAllAdminsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        admin_relationships = UserAdminUserRelationship.objects.filter(user=user)
        admins_data = [
            {
                'id': relationship.user_admin.id,
                'username': relationship.user_admin.username,
                'email': relationship.user_admin.email,
                'knowledge_base_count': KnowledgeBase.objects.filter(created_by=relationship.user_admin).count(),
                'chatbot_count': Chatbot.objects.filter(created_by=relationship.user_admin).count(),
            }
            for relationship in admin_relationships
        ]
        return Response({'admins': admins_data}, status=status.HTTP_200_OK)
    

class GetAllChatbotsForUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_admin_ids = user.admin_relationships.values_list('user_admin', flat=True)
        if not user_admin_ids:
            return Response({'error': 'This user is not associated with any admins so no chatbots'}, status=status.HTTP_404_NOT_FOUND)
        chatbots = Chatbot.objects.filter(created_by__in=user_admin_ids)
        serializer = ChatbotSerializer(chatbots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class GetAllChatbotsForUserADminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, admin_id):
        user = request.user
        
        # Check if the user has an association with the given user admin
        if not UserAdminUserRelationship.objects.filter(user=user, user_admin_id=admin_id).exists():
            return Response({'error': 'This user is not associated with the specified admin'}, status=status.HTTP_404_NOT_FOUND)

        # Fetch chatbots created by the specified user admin
        chatbots = Chatbot.objects.filter(created_by_id=admin_id)
        
        # Check if there are no chatbots for the specified admin
        if not chatbots.exists():
            return Response({'error': 'No chatbots found for the specified admin'}, status=status.HTTP_200_OK)
        
        # Serialize the chatbots
        serializer = ChatbotSerializer(chatbots, many=True)
        
        # Return the response with the serialized data
        return Response(serializer.data, status=status.HTTP_200_OK)


#conversation with chatbot
class CreateConversationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        chatbot_id = request.data.get('chatbot_id')

        # Check if chatbot ID is provided
        if not chatbot_id:
            return Response({'error': 'Chatbot ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the chatbot based on the provided ID
        chatbot = get_object_or_404(Chatbot, id=chatbot_id)

        # Create a new conversation
        conversation = Conversation.objects.create(
            user=user,
            chatbot=chatbot,
        )

        # Check if the chatbot has a conversation starter message
        conversation_starter = chatbot.conversation_starter or f"Hello {user.username}! I am {chatbot.name}, how can I assist you?"

        # Add the conversation starter message as the first message in the conversation
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            message=conversation_starter
        )

        # Prepare response data
        conversation_data = {
            'conversation_id': conversation.id,
            'user': {
                'id': user.id,
                'username': user.username
            },
            'chatbot': {
                'id': chatbot.id,
                'name': chatbot.name
            },
            'conversation_starter': conversation_starter,
            'created_at': conversation.created_at
        }

        return Response({
            'message': 'Conversation created successfully.',
            'conversation': conversation_data
        }, status=status.HTTP_201_CREATED)









class GetUserChatbotConversationsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        chatbot_id = request.query_params.get('chatbot_id')

        # Check if chatbot ID is provided
        if not chatbot_id:
            return Response({'error': 'Chatbot ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the chatbot based on the provided ID
        chatbot = get_object_or_404(Chatbot, id=chatbot_id)

        # Retrieve all conversations for the user and the specified chatbot
        conversations = Conversation.objects.filter(user=user, chatbot=chatbot)

        # Prepare the response data
        conversations_data = [
            {
                'conversation_id': conversation.id,
                'chatbot_name': conversation.chatbot.name,
                'created_at': conversation.created_at,
                'updated_at': conversation.updated_at
            }
            for conversation in conversations
        ]

        return Response({
            'user': {
                'id': user.id,
                'username': user.username
            },
            'chatbot': {
                'id': chatbot.id,
                'name': chatbot.name
            },
            'conversations': conversations_data
        }, status=status.HTTP_200_OK)
    




class GetConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        user = request.user

        # Get the conversation by ID and ensure it belongs to the user
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)

        # Get all messages related to the conversation
        messages = conversation.messages.all()

        # Prepare the messages data
        messages_data = [
            {
                'message_id': message.id,
                'role': message.role,
                'message': message.message,
                'timestamp': message.timestamp
            }
            for message in messages
        ]

        return Response({
            'conversation_id': conversation.id,
            'chatbot_name': conversation.chatbot.name,
            'messages': messages_data
        }, status=status.HTTP_200_OK)
    






class DeleteConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, conversation_id):
        user = request.user

        # Get the conversation by ID and ensure it belongs to the user
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)

        # Delete the conversation
        conversation.delete()

        return Response({'message': 'Conversation deleted successfully'}, status=status.HTTP_200_OK)
    








from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from clientadmin.models import Chatbot, KnowledgeBase
from clientuser.models import Conversation,Message
from clientadmin.serializers import ChatbotSerializer, KnowledgeBaseSerializer
from django.shortcuts import get_object_or_404
from account.models import UserAdminUserRelationship
from django.conf import settings
from langchain_openai import OpenAI,ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA

class GetAllAdminsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        admin_relationships = UserAdminUserRelationship.objects.filter(user=user)
        admins_data = [
            {
                'id': relationship.user_admin.id,
                'username': relationship.user_admin.username,
                'email': relationship.user_admin.email,
                'knowledge_base_count': KnowledgeBase.objects.filter(created_by=relationship.user_admin).count(),
                'chatbot_count': Chatbot.objects.filter(created_by=relationship.user_admin).count(),
            }
            for relationship in admin_relationships
        ]
        return Response({'admins': admins_data}, status=status.HTTP_200_OK)
    

class GetAllChatbotsForUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_admin_ids = user.admin_relationships.values_list('user_admin', flat=True)
        if not user_admin_ids:
            return Response({'error': 'This user is not associated with any admins so no chatbots'}, status=status.HTTP_404_NOT_FOUND)
        chatbots = Chatbot.objects.filter(created_by__in=user_admin_ids)
        serializer = ChatbotSerializer(chatbots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class GetAllChatbotsForUserADminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, admin_id):
        user = request.user
        
        # Check if the user has an association with the given user admin
        if not UserAdminUserRelationship.objects.filter(user=user, user_admin_id=admin_id).exists():
            return Response({'error': 'This user is not associated with the specified admin'}, status=status.HTTP_404_NOT_FOUND)

        # Fetch chatbots created by the specified user admin
        chatbots = Chatbot.objects.filter(created_by_id=admin_id)
        
        # Check if there are no chatbots for the specified admin
        if not chatbots.exists():
            return Response({'error': 'No chatbots found for the specified admin'}, status=status.HTTP_200_OK)
        
        # Serialize the chatbots
        serializer = ChatbotSerializer(chatbots, many=True)
        
        # Return the response with the serialized data
        return Response(serializer.data, status=status.HTTP_200_OK)


#conversation with chatbot
class CreateConversationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        chatbot_id = request.data.get('chatbot_id')

        # Check if chatbot ID is provided
        if not chatbot_id:
            return Response({'error': 'Chatbot ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the chatbot based on the provided ID
        chatbot = get_object_or_404(Chatbot, id=chatbot_id)

        # Create a new conversation
        conversation = Conversation.objects.create(
            user=user,
            chatbot=chatbot,
        )

        # Check if the chatbot has a conversation starter message
        conversation_starter = chatbot.conversation_starter or f"Hello {user.username}! I am {chatbot.name}, how can I assist you?"

        # Add the conversation starter message as the first message in the conversation
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            message=conversation_starter
        )

        # Prepare response data
        conversation_data = {
            'conversation_id': conversation.id,
            'user': {
                'id': user.id,
                'username': user.username
            },
            'chatbot': {
                'id': chatbot.id,
                'name': chatbot.name
            },
            'conversation_starter': conversation_starter,
            'created_at': conversation.created_at
        }

        return Response({
            'message': 'Conversation created successfully.',
            'conversation': conversation_data
        }, status=status.HTTP_201_CREATED)









class GetUserChatbotConversationsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        chatbot_id = request.query_params.get('chatbot_id')

        # Check if chatbot ID is provided
        if not chatbot_id:
            return Response({'error': 'Chatbot ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the chatbot based on the provided ID
        chatbot = get_object_or_404(Chatbot, id=chatbot_id)

        # Retrieve all conversations for the user and the specified chatbot
        conversations = Conversation.objects.filter(user=user, chatbot=chatbot)

        # Prepare the response data
        conversations_data = [
            {
                'conversation_id': conversation.id,
                'chatbot_name': conversation.chatbot.name,
                'created_at': conversation.created_at,
                'updated_at': conversation.updated_at
            }
            for conversation in conversations
        ]

        return Response({
            'user': {
                'id': user.id,
                'username': user.username
            },
            'chatbot': {
                'id': chatbot.id,
                'name': chatbot.name
            },
            'conversations': conversations_data
        }, status=status.HTTP_200_OK)
    




class GetConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        user = request.user

        # Get the conversation by ID and ensure it belongs to the user
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)

        # Get all messages related to the conversation
        messages = conversation.messages.all()

        # Prepare the messages data
        messages_data = [
            {
                'message_id': message.id,
                'role': message.role,
                'message': message.message,
                'timestamp': message.timestamp
            }
            for message in messages
        ]

        return Response({
            'conversation_id': conversation.id,
            'chatbot_logo':conversation.chatbot.chatbot_profile_url,
            'chatbot_name': conversation.chatbot.name,
            'starter_message': conversation.chatbot.conversation_starter,
            'messages': messages_data
        }, status=status.HTTP_200_OK)
    





class DeleteConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, conversation_id):
        user = request.user

        # Get the conversation by ID and ensure it belongs to the user
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)

        # Delete the conversation
        conversation.delete()

        return Response({'message': 'Conversation deleted successfully'}, status=status.HTTP_200_OK)
    








class ContinueConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        user = request.user
        user_message = request.data.get('message')

        # Step 1: Get the conversation by ID and ensure it belongs to the user
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)

        # Step 2: Save the user's message
        Message.objects.create(
            conversation=conversation,
            role='user',
            message=user_message
        )

        # Step 3: Retrieve the last 20 messages from this conversation
        last_20_messages = Message.objects.filter(conversation=conversation).order_by('-timestamp')[:20]
        last_20_messages = reversed(last_20_messages)

        # Step 4: Get chatbot configuration
        chatbot = conversation.chatbot
        temperature = chatbot.temperature
        max_tokens = chatbot.max_tokens
        model_name = chatbot.model_name or "gpt-3.5-turbo-0125"
        top_p = chatbot.top_p
        chatbot_instructions = chatbot.instructions or f"Hello {user.username}, how can I assist you?"

        # Prepare conversation history
        conversation_history = ""
        for message in last_20_messages:
            conversation_history += f"{message.role.capitalize()}: {message.message}\n"

        # Step 5: Retrieve relevant chunks with a strict similarity threshold
        knowledge_base = chatbot.knowledge_base
        retrieved_info = ""
        references = []  # To hold relevant document references
        similarity_threshold = 0.8  # Higher threshold to filter relevance
        max_retrieved_docs = 2      # Retrieve a maximum of 2 relevant documents

        if knowledge_base:
            index_name = knowledge_base.created_by.pinecone_index
            namespace = knowledge_base.namespace

            try:
                api_settings = APISettings.objects.first()
                if not api_settings:
                    raise ImproperlyConfigured("APISettings instance not found.")

                # Initialize Pinecone retrieval
                OPENAI_API_KEY = api_settings.openai_api_key or os.getenv("OPENAI_API_KEY")
                PINECONE_API_KEY = api_settings.pinecone_api_key or os.getenv("PINECONE_API_KEY")
                pinecone_initializer = PineconeInitializer(pinecone_api=PINECONE_API_KEY, open_ai_api=OPENAI_API_KEY)
                embed = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

                # Connect to Pinecone vector store
                docsearch = PineconeVectorStore.from_existing_index(
                    index_name=index_name,
                    embedding=embed,
                    namespace=namespace
                )

                # Retrieve relevant documents based on the user's message
                retriever = docsearch.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={"score_threshold": similarity_threshold, "k": max_retrieved_docs}
                )
                relevant_docs = retriever.get_relevant_documents(user_message)

                # Gather retrieved content and references if relevant documents exist
                if relevant_docs:
                    retrieved_info = " ".join([doc.page_content for doc in relevant_docs])
                    references = [
                        {
                            "document_name": doc.metadata.get("document_name", "Unknown Document"),
                            "s3_url": doc.metadata.get("s3_url", "No URL available"),
                        }
                        for doc in relevant_docs
                    ][:max_retrieved_docs]  # Limit references to two documents

            except Exception as e:
                logger.error(f"Error retrieving from Pinecone: {str(e)}", exc_info=True)
                return Response({
                    'error': 'Failed to retrieve relevant knowledge base info',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 6: Prepare the prompt for OpenAI with instructions based on the presence of retrieved information
        if retrieved_info:
            # Instruction to reference the document if retrieved info is included
            reference_text = "\n\nWhen answering, if relevant, include the source as follows: 'Reference: [Document Name](URL)'."
            # Prepare additional reference information for LLM context
            reference_instructions = ""
            if references:
                ref = references[0]  # Use only the most relevant reference
                reference_instructions = f"\n\nSource Document:\n- Name: {ref['document_name']}\n- URL: {ref['s3_url']}"
        else:
            # No reference instruction if no relevant info is retrieved
            reference_text = ""
            reference_instructions = ""

        prompt = f"""
        {chatbot_instructions}
        Conversation history:
        {conversation_history}

        Knowledge base retrieved info:
        {retrieved_info}

        User: {user_message}
        Assistant:{reference_text}{reference_instructions}
        """

        try:
            # Step 7: Generate response from OpenAI
            if model_name.startswith('claude'):
                llm = ChatAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                    model=model_name,
                    temperature=temperature,
                    max_tokens_to_sample=max_tokens
                )
            else:
                llm = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p
                )
            assistant_message = llm.invoke(prompt)
            assistant_message_content = dict(assistant_message)['content']

            # Step 8: Save assistant's response to the messages
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                message=assistant_message_content
            )

            # Step 9: Return the assistant's response
            return Response({
                'assistant_message': assistant_message_content,
                'conversation_id': conversation.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to generate assistant response',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class RegenerateFromMessageWithEditView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id, message_id):
        user = request.user
        new_text = request.data.get('new_message', None)

        # Step 1: Verify the conversation belongs to the user
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)

        # Step 2: Retrieve the specific message by ID
        target_message = get_object_or_404(Message, id=message_id, conversation=conversation)

        # Step 3: Update the target message if new text is provided
        if new_text:
            target_message.message = new_text
            target_message.save()  # Save the updated message content

        # Step 4: Delete all messages after this message
        Message.objects.filter(conversation=conversation, timestamp__gt=target_message.timestamp).delete()

        # Step 5: Prepare conversation history for regenerating response
        remaining_messages = Message.objects.filter(conversation=conversation).order_by('timestamp')[:20]
        remaining_messages = reversed(remaining_messages) 
        conversation_history = "\n".join(
            f"{msg.role.capitalize()}: {msg.message}" for msg in remaining_messages
        )

        # Step 6: Get chatbot settings and instructions
        chatbot = conversation.chatbot
        temperature = chatbot.temperature
        max_tokens = chatbot.max_tokens
        model_name = chatbot.model_name or "gpt-3.5-turbo-0125"
        top_p = chatbot.top_p
        chatbot_instructions = chatbot.instructions or f"Hello {user.username}, how can I assist you?"

        # Step 7: Retrieve knowledge base information from Pinecone (if available)
        knowledge_base = chatbot.knowledge_base
        retrieved_info = ""

        if knowledge_base:
            index_name = knowledge_base.created_by.pinecone_index
            namespace = knowledge_base.namespace

            try:
                # Initialize Pinecone retrieval process
                api_settings = APISettings.objects.first()
                if not api_settings:
                            raise ImproperlyConfigured("APISettings instance not found.")
                    # Initialize Pinecone and clear the existing namespace
                OPENAI_API_KEY = api_settings.openai_api_key or os.getenv("OPENAI_API_KEY")
                PINECONE_API_KEY = api_settings.pinecone_api_key or os.getenv("PINECONE_API_KEY")
                pinecone_initializer = PineconeInitializer(pinecone_api=PINECONE_API_KEY, open_ai_api=OPENAI_API_KEY)
                embed = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

                # Connect to Pinecone vector store
                docsearch = PineconeVectorStore.from_existing_index(
                    index_name=index_name,
                    embedding=embed,
                    namespace=namespace
                )

                # Retrieve relevant information based on the updated message
                retriever = RetrievalQA.from_chain_type(
                    llm=ChatOpenAI(api_key=settings.OPENAI_API_KEY, temperature=temperature),
                    chain_type="stuff",
                    retriever=docsearch.as_retriever()
                )

                # Perform the retrieval based on the updated message
                retrieved_docs  = retriever.invoke(new_text)
                if retrieved_docs:
                    for doc in retrieved_docs['documents']:
                        document_name = doc.get('metadata', {}).get('document_name', 'Unknown Document')
                        s3_url = doc.get('metadata', {}).get('s3_url', '#')
                        text_content = doc.get('text', '')

                        # Append document reference to each chunk of retrieved info
                        retrieved_info += f"{text_content}\n\n(Source: [{document_name}]({s3_url}))\n\n"

            except Exception as e:
                logger.error(f"Error retrieving from Pinecone: {str(e)}", exc_info=True)
                return Response({
                    'error': 'Failed to retrieve relevant knowledge base info',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 8: Construct the prompt
        prompt = f"""
        {chatbot_instructions}
        Conversation history:
        {conversation_history}

        Knowledge base retrieved info:
        {retrieved_info}

        User: {new_text}
        Assistant:
        """

        try:
            # Step 9: Initialize LLM and generate response
            llm = self.initialize_llm(model_name, temperature, max_tokens, top_p)
            assistant_response = llm.invoke(prompt)

            # Access content directly if `AIMessage` is returned
            if hasattr(assistant_response, 'content'):
                assistant_message_content = assistant_response.content
            else:
                # Otherwise, assume it returns a dictionary and use 'content' key
                assistant_message_content = dict(assistant_response).get('content', '')

            # Step 10: Save the regenerated assistant message
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                message=assistant_message_content
            )

            return Response({
                'regenerated_message': assistant_message_content,
                'conversation_id': conversation.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to regenerate assistant response',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def initialize_llm(self, model_name, temperature, max_tokens, top_p):
        if model_name.startswith('claude'):
            return ChatAnthropic(api_key=settings.ANTHROPIC_API_KEY, model=model_name, temperature=temperature, max_tokens_to_sample=max_tokens)
        return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=model_name, temperature=temperature, max_tokens=max_tokens, top_p=top_p)
    






class DeleteConversationMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, conversation_id, message_id):
        user = request.user

        # Step 1: Get the conversation by ID and ensure it belongs to the user
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)

        # Step 2: Get the specific message by ID within the conversation
        message = get_object_or_404(Message, id=message_id, conversation=conversation)

        # Step 3: Delete the message
        message.delete()

        # Step 4: Return a success response
        return Response({
            'message': f'Message with ID {message_id} has been deleted successfully.'
        }, status=status.HTTP_200_OK)