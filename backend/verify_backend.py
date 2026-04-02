import requests
import json
import uuid

base_url = "http://127.0.0.1:5000"

user_email = f"test_{uuid.uuid4().hex[:6]}@gmail.com"
print(f"0. Testing register {user_email}...")
res = requests.post(f"{base_url}/register", json={"username": "testuser", "email": user_email, "password": "password"})
print("Register:", res.status_code, res.text)

print("1. Testing login...")
res = requests.post(f"{base_url}/login", json={"email": user_email, "password": "password"})
print("Login Status:", res.status_code)
if res.status_code != 200:
    print("Login Failed:", res.text)
    exit(1)

token = res.json().get("token")
print("Token:", token)

print("2. Testing /summary...")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
data = {"keyword": "ABAP", "historyId": None}

res = requests.post(f"{base_url}/summary", json=data, headers=headers)
print("Summary Status:", res.status_code)
try:
    print("Summary Body JSON:", res.json())
except:
    print("Summary Body Raw:", res.text[:200])

