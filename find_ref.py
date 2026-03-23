import sys
import os

# Set the fix first
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

def search_class(module_name):
    try:
        mod = __import__(module_name, fromlist=['*'])
        for attr in dir(mod):
            if attr == "ReferenceImage":
                return f"Found ReferenceImage in {module_name}"
            # Recursively check submodules if they are already loaded or common
            if not attr.startswith("_") and hasattr(getattr(mod, attr), "__path__"):
                sub = f"{module_name}.{attr}"
                res = search_class(sub)
                if res: return res
    except:
        pass
    return None

print(search_class("vertexai"))
