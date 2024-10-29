import os
from litellm import completion
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the model setup using environment variables
model = "azure/gpt-4o-mini"
api_key = os.getenv("AZURE_API_KEY")
api_base = os.getenv("AZURE_API_BASE")
api_version = os.getenv("AZURE_API_VERSION")

# Ensure the necessary environment variables are set
if not all([api_key, api_base, api_version]):
    raise ValueError("Missing Azure configuration environment variables.")

# Azure call using the loaded environment variables
response = completion(
    model=model, 
    messages=[{ "content": "Hello, how are you?", "role": "user" }]
)

print(response)
