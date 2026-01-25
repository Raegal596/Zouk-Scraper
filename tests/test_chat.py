import requests
import json

try:
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"message": "Hello", "history": []}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(e)
