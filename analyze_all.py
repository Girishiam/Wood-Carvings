"""
Cost-effective single-image analysis script.
Processes every image in the assets folder one by one.
Generates: Color Description, Sketch Translation, and 4-Sided Extrapolation.
Saves all output to assets/individual_analysis.md.
"""

import os
import sys
import time
from pathlib import Path

# Fix protobuf compatibility for Python 3.14
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from dotenv import load_dotenv
from google import genai
from PIL import Image

ASSETS_DIR = Path("assets")
OUTPUT_FILE = ASSETS_DIR / "individual_analysis.md"
MODEL_NAME = "gemini-2.5-flash"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

_PROMPT = """\
You are an expert art director and character designer.
Analyze this reference photo of a wood carving character. Because the photo usually only shows one side (front or 3/4), you must extrapolate the rest of the character design.

Provide your analysis strictly in the following format:

**1. COLOR WOOD CARVING PORTRAIT**
Describe the character exactly as they appear in this color wood carving photograph. Include their pose, expression, clothing, held props, and visible carving textures or paint finishes.

**2. SKETCH TRANSLATION**
Describe how this exact same character would look if translated into a clean, highly polished black-and-white professional pencil character design sketch. Focus on line weight, shading, and lack of color.

**3. 4-SIDED TURNAROUND PREDICTION**
Predict and describe the unseen angles to complete a 4-view orthographic turnaround sheet for this character:
- **Left Side Profile:** (Describe silhouette, arm setup, and how props look from the left)
- **Back View:** (Describe the back of the clothing, hat/hair, and posture)
- **Right Side Profile:** (Describe silhouette, arm setup, and how props look from the right)

Keep the descriptions highly specific but concise. Do not use filler text.
"""

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    print(f"Using model: {MODEL_NAME}")

    valid_images = sorted([
        f for f in ASSETS_DIR.rglob("*") 
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])
    
    print(f"Found {len(valid_images)} images to analyze.")

    # Create or overwrite the master markdown file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Master Individual Image Analysis\n\n")

    for i, path in enumerate(valid_images, start=1):
        print(f"[{i}/{len(valid_images)}] Analyzing {path.name}...")
        try:
            # Load and downscale image to save tokens & money
            img = Image.open(path).convert("RGB")
            img.thumbnail((768, 768), Image.LANCZOS)
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[img, _PROMPT]
            )
            
            # Append result immediately
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"## Image: {path.name}\n")
                f.write(response.text.strip() + "\n\n---\n\n")
                
            # Sleep slightly to avoid rate limit bursts
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ Error processing {path.name}: {e}")

    print(f"\n✅ Analysis complete! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
