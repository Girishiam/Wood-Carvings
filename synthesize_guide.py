"""
Synthesizes the individual image analyses into a master dual-mode Artist Style Guide.
Reads the first ~100 images' worth of analysis data from individual_analysis.md.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Fix protobuf compatibility for Python 3.14
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

ASSETS_DIR = Path("assets")
ANALYSIS_FILE = ASSETS_DIR / "individual_analysis.md"
OUTPUT_FILE = ASSETS_DIR / "artist_style_guide.txt"
MODEL_NAME = "gemini-2.5-flash"

_PROMPT = """\
You are the lead art director for an AI image generation pipeline.
Below is a massive dataset of analysis describing hundreds of individual character designs based on a specific artist's carving style. Each entry describes the character as a Color Wood Carving, a Pencil Sketch, and a 4-Sided Turnaround.

Your task: Read this data and synthesize it into ONE definitive, authoritative master Artist Style Guide.

The output will be injected verbatim into an AI image generator prompt as absolute law. Write as direct, imperative rules — not observations. Every sentence should be actionable.

Structure the output into exactly these three sections, with detailed bullet points or paragraphs for each:

=========================================
SECTION 1 — UNIVERSAL CHARACTER PROPORTIONS & ANATOMY:
(Rules that apply to BOTH sketches and color carvings: exact body ratios, head size, hand/foot thickness, facial features, caricature style, posture tendencies).

=========================================
SECTION 2 — RENDER MODE: COLOR WOOD CARVING
(Rules that ONLY apply when rendering the color wood carving: specific tooling marks, V-tool/U-gouge cuts, paint method, wood grain visibility, finish, lighting).

=========================================
SECTION 3 — RENDER MODE: CLEAN PENCIL SKETCH
(Rules that ONLY apply when rendering the black-and-white sketch: line quality, shading style, lack of color/wood texture, clean polished look).

Output ONLY these three sections. No preamble, no meta-commentary.
"""

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    if not ANALYSIS_FILE.exists():
        print("Analysis file not found.")
        sys.exit(1)

    # Read the first ~80,000 characters (plenty of examples, stays well within context)
    with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
        data = f.read(80000)

    print(f"Loaded {len(data)} characters of analysis data.")
    print("Synthesizing Master Style Guide...")

    contents = [_PROMPT, f"--- RAW DATA ---\n{data}"]
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text.strip())

    print(f"✅ Master Style Guide generated and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
