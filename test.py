import sys
sys.modules['google._upb._message']=None
sys.modules['google.protobuf.pyext._message']=None
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']='python'
import google.generativeai as genai

out = [attr for attr in dir(genai) if not attr.startswith('_')]
with open("test_out2.txt", "w") as f:
    f.write("\n".join(out))
