import os
import sys

sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from google import genai
import inspect

def read_source():
    client = genai.Client(api_key="DUMMY")
    with open("output8.txt", "w", encoding="utf-8") as f:
        try:
            f.write("--- edit_image ---\n")
            f.write(inspect.getsource(client.models.edit_image))
            
            f.write("\n\n--- generate_images ---\n")
            f.write(inspect.getsource(client.models.generate_images))
        except Exception as e:
            f.write(str(e))

if __name__ == "__main__":
    read_source()
