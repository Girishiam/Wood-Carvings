import sys
sys.modules['google._upb._message']=None
sys.modules['google.protobuf.pyext._message']=None
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']='python'

from dotenv import load_dotenv
load_dotenv()

from google import genai

client = genai.Client() # Uses GEMINI_API_KEY from environment

try:
    with open("models.txt", "w") as f:
        for m in client.models.list():
            if "generate" in m.name or "imagen" in m.name:
                f.write(f"Model: {m.name}\n")
except Exception as e:
    print("Error:", e)
