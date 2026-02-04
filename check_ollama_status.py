import requests
import sys

try:
    print("Checking Ollama...")
    r = requests.get('http://localhost:11434/api/tags', timeout=2)
    if r.status_code == 200:
        print("Ollama is RUNNING")
        data = r.json()
        models = [m['name'] for m in data.get('models', [])]
        print(f"Available models: {models}")
        if 'gemma2:9b' in models or 'gemma2:latest' in models: # Adjust match as needed
             print("Required model FOUND")
        else:
             print("Required model gemma2:9b MISSING")
    else:
        print(f"Ollama responded with status: {r.status_code}")
except Exception as e:
    print(f"Ollama check FAILED: {e}")
