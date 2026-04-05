import requests
import json

def test_ollama_api():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma:2b",
        "prompt": "Summarize Machine Learning in 20 words plain text.",
        "stream": False
    }
    try:
        print(f"Calling Ollama API at {url}...")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        print("API Response successful!")
        print("Response Content:", data.get("response"))
    except Exception as e:
        print("API Call failed:", e)

if __name__ == "__main__":
    test_ollama_api()
