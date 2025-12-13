import requests
import sys

URL = "http://127.0.0.1:8000"

print(f"Testing connection to {URL}...")

try:
    # 1. Test Root/Docs (GET)
    print("1. Attempting to reach /docs...")
    response = requests.get(f"{URL}/docs", timeout=5)
    print(f"   Success! Status Code: {response.status_code}")
except Exception as e:
    print(f"   FAILED: {e}")

try:
    # 2. Test Stats (GET)
    print("2. Attempting to reach /stats...")
    response = requests.get(f"{URL}/stats", timeout=5)
    print(f"   Success! Status Code: {response.status_code}")
    print(f"   Response: {response.text[:100]}...")
except Exception as e:
    print(f"   FAILED: {e}")

print("\nDiagnostics complete.")
