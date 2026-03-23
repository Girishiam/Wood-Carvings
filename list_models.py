import sys
sys.modules['google._upb._message']=None
sys.modules['google.protobuf.pyext._message']=None
import os; os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']='python'
from dotenv import load_dotenv; load_dotenv()
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
with open("gemini_models.txt", "w") as f:
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            f.write(m.name + "\n")
print("done")
