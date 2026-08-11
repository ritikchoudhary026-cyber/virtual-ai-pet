import requests
while True:
    msg = input("You: ")
    if msg == "quit": break
    resp = requests.post("http://localhost:8000/chat", json={"message": msg})
    print("Pet:", resp.json()["response"])