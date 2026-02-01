
import os
import requests
from dotenv import load_dotenv

from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Error: OPENAI_API_KEY not found in environment.")
    exit(1)

print(f"Testing API Key: {api_key[:8]}...{api_key[-4:]}")

try:
    response = requests.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10
    )
    
    if response.status_code == 200:
        print("Success! API Key is valid.")
        data = response.json()
        print(f"Available models count: {len(data['data'])}")
    else:
        print(f"Error: API request failed with status code {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Exception occurred: {e}")
