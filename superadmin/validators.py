import requests

def validate_openai_api_key(api_key):
    try:
        # Send a test request to OpenAI's API to validate the API key
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "gpt-4o-mini",  # Example model
                "messages": [{"role": "user", "content": "Say this is a test!"}],
                "temperature": 0.7
            }
        )
        # Check if the response is successful
        return response.status_code == 200
    except requests.RequestException:
        return False

from pinecone import Pinecone, ServerlessSpec

def validate_pinecone_api_key(api_key):
    try:
        # Initialize a connection to Pinecone using the provided API key
        pc = Pinecone(api_key=api_key, environment=ServerlessSpec())
        # Check if connection is established
        if pc:
            return True
        return False
    except Exception as e:
        # If there’s an exception, the API key is invalid
        print(f"Error validating Pinecone API key: {e}")
        return False

import anthropic

def validate_claude_api_key(api_key):
    try:
        # Initialize the Anthropic client with the provided API key
        client = anthropic.Anthropic(api_key=api_key)

        # Send a test message to validate the API key
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Example model
            max_tokens=1,  # Minimal token usage for testing
            messages=[{"role": "user", "content": "Hello, Claude"}]
        )
        # Check if the message content is returned successfully
        return bool(message.get("completion", None))
    except Exception as e:
        print(f"Error validating Claude API key: {e}")
        return False