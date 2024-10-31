import os
import requests
import base64
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Configuration
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = os.getenv("ENDPOINT")

# Check if the environment variables are loaded correctly
if not all([AZURE_API_KEY, ENDPOINT]):
    raise ValueError("Missing necessary environment variables.")

headers = {
    "Content-Type": "application/json",
    "api-key": AZURE_API_KEY,
}

# Payload for the request
payload = {
    "messages": [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an AI assistant that helps people find information."
                }
            ]
        }
    ],
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 800
}

# Send request
try:
    response = requests.post(ENDPOINT, headers=headers, json=payload)
    response.raise_for_status()  # Raises an error if the request failed
except requests.RequestException as e:
    raise SystemExit(f"Failed to make the request. Error: {e}")

# Handle the response (e.g., print or process)
print(response.json())

