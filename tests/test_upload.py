import requests

# Create a dummy file
with open("test_upload.txt", "w") as f:
    f.write("This is a test transcript content.")

url = "http://127.0.0.1:8000/upload"
files = {'file': open('test_upload.txt', 'rb')}

try:
    response = requests.post(url, files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(e)
