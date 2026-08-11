import requests
print("Testing...")
try:
    resp = requests.post("http://localhost:8000/chat", json={"message": "15% of 200 ?"}, timeout=300)
    print(resp.status_code, resp.text)
except Exception as e:
    print("Error:", e)
