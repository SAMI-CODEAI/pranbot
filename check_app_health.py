import requests
import sys

try:
    print("Checking App Health...")
    r = requests.get('http://localhost:5000/health', timeout=2)
    print(f"App responded with: {r.status_code}")
    print(r.text)
except Exception as e:
    print(f"App check FAILED: {e}")
