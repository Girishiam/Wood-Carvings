import os
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"

payload = {
    "instances": [
        {"prompt": "A cute cartoon owl"}
    ],
    "parameters": {
        "sampleCount": 1
    }
}

try:
    resp = httpx.post(url, json=payload, timeout=30.0)
    print("STATUS:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Success! Keys in response:", data.keys())
        if "predictions" in data:
            print("Predictions found!", len(data["predictions"]))
    else:
        print(resp.text)
except Exception as e:
    print("Error:", e)
