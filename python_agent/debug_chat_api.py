import requests
import json

def test_chat():
    url = "http://localhost:8000/api/chat"
    payload = {
        "message": "我要對 Turkey-Syria Earthquake Relief 這個提案直接捐贈 1 USDC。提案 ID 0",
        "context": {}
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
