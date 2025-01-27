from celery import shared_task
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import base64
import io
import uuid
from PyPDF2 import PdfReader
from docx import Document
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import default_storage
from django.conf import settings
from .models import GoogleDriveAccount, KnowledgeBase, KnowledgeBaseDocument
from .views import PineconeInitializer
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from celery import shared_task
from google.auth.transport.requests import Request
import logging


logger = logging.getLogger(__name__)


@shared_task
def check_google_drive():
    """
    Celery task to periodically check Google Drive folders of each user
    and update the knowledge base if files are added or deleted.
    """
    accounts = GoogleDriveAccount.objects.all()  # Get all Google Drive accounts

    for account in accounts:
        try:
            credentials_data = json.loads(account.credentials)
            credentials = Credentials(**credentials_data)

            # Check if the token is expired and refresh it if necessary
            if credentials.expired and credentials.refresh_token:
                print(f"Token expired for user {account.user.username}. Refreshing token...")
                credentials.refresh(Request())  # This refreshes the access token

                # Save the refreshed credentials back to the database
                updated_credentials = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes,
                }
                account.credentials = json.dumps(updated_credentials)
                account.save()
                print(f"Refreshed token saved for user {account.user.username}.")

            # Retrieve the knowledge base and folder ID
            try:
                knowledge_base = KnowledgeBase.objects.get(
                    created_by=account.user,
                    google_drive_folder_id__isnull=False
                )

                folder_id = knowledge_base.google_drive_folder_id  # Get folder_id from KnowledgeBase
            except KnowledgeBase.DoesNotExist:
                print(f"No knowledge base found for user {account.user.username}. Skipping.")
                continue

            # Build the Google Drive service with the (possibly refreshed) credentials
            service = build('drive', 'v3', credentials=credentials)

            # Get the list of files in the user's Google Drive folder
            query = f"'{folder_id}' in parents and trashed = false"
            results = service.files().list(q=query).execute()
            drive_items = results.get('files', [])
            drive_files = {item['name']: item['id'] for item in drive_items}

            # Get the existing documents in the knowledge base
            existing_documents = KnowledgeBaseDocument.objects.filter(knowledge_base=knowledge_base)
            existing_files = {doc.document_name for doc in existing_documents}

            # Check if there is a difference (file addition or deletion)
            if set(drive_files.keys()) != existing_files:
                # Files have changed (addition or deletion)
                update_knowledge_base_from_gdrive(knowledge_base, drive_files, account, service)

        except Exception as e:
            print(f"Error checking Google Drive for user {account.user}: {str(e)}")


def update_knowledge_base_from_gdrive(knowledge_base, drive_files, account, service):
    """
    Update the knowledge base with the new set of files from Google Drive,
    clearing existing Pinecone data and S3 URLs, and re-adding the files.
    """
    try:
        # If the knowledge base exists, clear the Pinecone namespace and delete existing documents
        if knowledge_base:
            clear_existing_knowledge_base(knowledge_base)

        # If no knowledge base exists, create one for the user
        if not knowledge_base:
            knowledge_base = KnowledgeBase.objects.create(
                name=f"KB-{account.user.username}",
                namespace=f"namespace-{account.user.id}",
                created_by=account.user
            )

        # Initialize Pinecone
        pinecone_initializer = PineconeInitializer(pinecone_api=settings.PINECONE_API, open_ai_api=settings.OPENAI_API_KEY)

        s3_urls = []
        # Process each file from Google Drive and update knowledge base
        for file_name, file_id in drive_files.items():
            file_content = get_file_content_from_gdrive(service, file_id)
            if file_content:
                document_text, s3_url = process_and_upload_file(file_content, file_name)
                s3_urls.append(s3_url)
                save_document_to_knowledge_base(knowledge_base, file_name, s3_url)

                # Chunk the text and embed it in Pinecone
                embed_document_in_pinecone(pinecone_initializer, document_text, knowledge_base, account.user.id)

        print(f"Knowledge base updated successfully for user {account.user.username}")

    except Exception as e:
        print(f"Error updating knowledge base for user {account.user}: {str(e)}")

from urllib.parse import urlparse

def get_s3_key_from_url(s3_url):
    parsed_url = urlparse(s3_url)
    return parsed_url.path.lstrip('/')

def clear_existing_knowledge_base(knowledge_base):
    """
    Clear the existing knowledge base by removing Pinecone embeddings and S3 documents.
    """
    try:
        pinecone_initializer = PineconeInitializer(pinecone_api=settings.PINECONE_API, open_ai_api=settings.OPENAI_API_KEY)

        # Clear the Pinecone namespace
        pinecone_initializer.delete_namespace_from_pinecone(
            index_name=knowledge_base.created_by.pinecone_index,
            namespace=knowledge_base.namespace
        )

        # Delete existing documents from S3 and database
        existing_documents = KnowledgeBaseDocument.objects.filter(knowledge_base=knowledge_base)
        for document in existing_documents:
            try:
                s3_key = get_s3_key_from_url(document.s3_url)
                default_storage.delete(s3_key)  # Corrected to use s3_key
            except Exception as e:
                print(f"Error deleting file {document.s3_url} from S3: {str(e)}")
        
        # Ensure database entries are deleted even if S3 deletion fails
        existing_documents.delete()  # Remove from database

    except Exception as e:
        print(f"Error clearing existing knowledge base: {str(e)}")


def get_file_content_from_gdrive(service, file_id):
    """
    Retrieve the file content from Google Drive using the file ID.
    """
    try:
        request = service.files().get_media(fileId=file_id)
        return request.execute()
    except Exception as e:
        print(f"Error retrieving file content from Google Drive: {str(e)}")
        return None


def process_and_upload_file(file_content, file_name):
    """
    Process the file (extract text based on type) and upload it to S3.
    Returns the extracted text and the S3 URL.
    """
    document_type = file_name.split('.')[-1].lower()
    document_text = ""

    # Extract text based on the file type
    if document_type == 'pdf':
        pdf_reader = PdfReader(io.BytesIO(file_content))
        for page_num in range(len(pdf_reader.pages)):
            document_text += pdf_reader.pages[page_num].extract_text() + "\n\n"
    elif document_type == 'docx':
        doc_stream = io.BytesIO(file_content)
        doc = Document(doc_stream)
        document_text += "\n\n".join([para.text for para in doc.paragraphs]) + "\n\n"
    elif document_type == 'txt':
        document_text += file_content.decode('utf-8') + "\n\n"
    elif document_type == 'html':
        try:
            document_text = extract_text_from_html(file_content, file_name)
        except Exception as e:
            print(f"Failed to process HTML for document {file_name}: {str(e)}")
            return "", None
    else:
        print(f"Unsupported document type: {document_type} for document {file_name}")
        return "", None

    # Upload the file to S3
    try:
        file_io = io.BytesIO(file_content)
        file_io.seek(0)
        in_memory_file = InMemoryUploadedFile(
            file_io,
            None,
            file_name,
            'application/octet-stream',
            len(file_content),
            None
        )
        s3_key = f"documents/{uuid.uuid4()}_{file_name}"
        default_storage.save(s3_key, in_memory_file)
        s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
        return document_text, s3_url
    except Exception as e:
        print(f"Failed to upload document to S3: {str(e)}")
        return "", None


def extract_text_from_html(self,file_content, document_name):
    """
    Extracts text from HTML content.
    """
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(file_content, 'html.parser')
        # Extract text from HTML
        text = soup.get_text(separator='\n\n')
        return text
    except Exception as e:
        logger.exception(f"Error extracting text from HTML for {document_name}: {e}")
        raise ValueError(f"Error extracting text from HTML: {str(e)}")


def save_document_to_knowledge_base(knowledge_base, file_name, s3_url):
    """
    Save the document metadata to the KnowledgeBaseDocument model.
    """
    KnowledgeBaseDocument.objects.create(
        knowledge_base=knowledge_base,
        document_name=file_name,
        s3_url=s3_url,
        document_type=file_name.split('.')[-1].lower()
    )


def embed_document_in_pinecone(pinecone_initializer, document_text, knowledge_base, user_id):
    """
    Chunk the document text and embed the chunks in Pinecone.
    """
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = text_splitter.split_text(document_text)

        pinecone_initializer.Embeding_Text_list_to_pinecone(
            texts=chunks,
            index_name=knowledge_base.created_by.pinecone_index,
            namespace=knowledge_base.namespace,
            Agent_id=user_id
        )
    except Exception as e:
        print(f"Error embedding document in Pinecone: {str(e)}")
