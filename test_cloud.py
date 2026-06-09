import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = "https://api.ollama.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama3",
    "messages": [
        {
            "role": "user",
            "content": "Diga oi em português"
        }
    ]
}

response = requests.post(
    url,
    headers=headers,
    json=payload
)

print("STATUS:")
print(response.status_code)

print("\nRESPOSTA:")
print(response.text)