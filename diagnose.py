import sys
import os

# Set the fix first
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

with open("diag_output.txt", "w") as f:
    try:
        import vertexai.preview.vision_models as vm
        f.write("Vision Models Attributes:\n")
        for attr in sorted(dir(vm)):
            if not attr.startswith("__"):
                f.write(f"- {attr}\n")
    except Exception as e:
        f.write(f"Error importing vision_models: {e}\n")

    try:
        import google.generativeai as genai
        f.write("\nGenerative AI imported successfully\n")
    except Exception as e:
        f.write(f"\nError importing generativeai: {e}\n")
