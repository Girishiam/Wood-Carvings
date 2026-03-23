"""
Multi-batch Vision Style Extraction Script.

Strategy (industry standard for large reference sets):
  - Split 1000+ images into diverse batches
  - Run Gemini Vision on 3 batches of 25 images each (~75 images total)
  - Do a final synthesis pass to merge all batch findings into one master guide
  - Saves the final guide to assets/artist_style_guide.txt

Cost estimate: ~$0.05–$0.10 total for all 4 API calls (3 batches + 1 synthesis)
"""

import os
import sys
import random
from pathlib import Path

# Fix protobuf compatibility for Python 3.14
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# ------------------------------------------------------------------ #
# Configuration
# ------------------------------------------------------------------ #

ASSETS_DIR = Path("assets")
STYLE_GUIDE_PATH = ASSETS_DIR / "artist_style_guide.txt"

BATCH_SIZE = 25       # Images per analysis batch
NUM_BATCHES = 3       # Number of batches = 75 total images analyzed
MODEL_NAME = "gemini-2.5-flash"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

# ------------------------------------------------------------------ #
# HEIC Support
# ------------------------------------------------------------------ #

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    print("✅ HEIC support: enabled via pillow-heif.")
except ImportError:
    print("⚠  HEIC support unavailable (pillow-heif not installed). HEIC files will be skipped.")
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# ------------------------------------------------------------------ #
# Per-batch analysis prompt
# ------------------------------------------------------------------ #

_BATCH_PROMPT = """\
You are a master art director and folk-art character design analyst.
Below is a batch of photographs of a professional wood carver's finished sculptures.

Analyze this batch and extract highly specific, actionable style rules for an AI image generator.

Cover ALL of the following in dense detail:

ANATOMY & PROPORTIONS:
- Head-to-body ratio (be specific, e.g. "head is roughly 1/3 of total height")
- Hand and foot size relative to body
- Torso shape, leg length and mass
- Specific posture tendencies

FACIAL FEATURES:
- Eye shape, lid heaviness, pupil rendering
- Nose style and size (be very specific — bulbous? aquiline? upturned?)
- Mouth and expression tendencies
- Chin, jaw, jowl characteristics
- Beard/mustache treatment if present

WOOD CARVING TEXTURE:
- Which specific tools are visible? (V-tool? U-gouge? straight knife?)
- How do tool marks follow the forms? (hair, clothing, skin)
- Surface finish? (raw? painted? antiqued wash? varnished?)
- Paint application method? (dry-brushed? full coverage wash? stain?)
- Is wood grain visible through paint?

CLOTHING & ACCESSORIES:
- How are fabric folds represented in carved form?
- How are belts, buttons, straps handled?
- How are hats rendered?
- How are boots/shoes carved?
- Any signature accessory patterns?

POSE & CHARACTER ARCHETYPE:
- What types of characters appear? (age, occupation, personality)
- Common pose tendencies?
- Expression range?

Output ONLY the raw descriptive rules. No preamble, no summary, no conclusions.
Be maximally specific and dense.
"""

# ------------------------------------------------------------------ #
# Synthesis prompt — merges all batch findings into one master guide
# ------------------------------------------------------------------ #

_SYNTHESIS_PROMPT = """\
You are the lead art director for an AI image generation pipeline.
Below are three separate style analysis reports from different batches of the same artist's wood carving work.

Your task: Merge, deduplicate, and synthesize these three reports into ONE definitive, authoritative master Artist Style Guide.

The output will be injected VERBATIM into an AI image generator prompt as absolute law.
Write as direct, imperative rules — not observations. Every sentence should be actionable.

Structure the output into exactly these six sections:

SECTION 1 — CHARACTER SHEET LAYOUT:
Rules for the 4-panel turnaround sheet structure, labels, background, body framing.

SECTION 2 — ANATOMICAL PROPORTIONS & CARICATURE:
Exact body ratios, hand/foot size rules, torso and leg specifications.

SECTION 3 — FACIAL FEATURES:
The complete facial formula: eyes, nose, mouth, chin, ears, expressions.

SECTION 4 — WOOD CARVING TEXTURE & MEDIUM:
Specific tooling marks, paint method, finish, grain visibility rules.

SECTION 5 — CLOTHING & COSTUMING:
Fabric fold carving, buttons, belts, hats, boots — all specifics.

SECTION 6 — LINE ART STYLE (Sketch Mode):
Rules for ink turnaround sketches: line weight, hatching, quality target.

Output ONLY the six sections. No preamble, no meta-commentary. Make it dense and directive.
"""

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def load_image_batch(paths: list[Path]) -> list:
    """Load and resize a list of image paths, skipping errors."""
    images = []
    for path in paths:
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((1024, 1024), Image.LANCZOS)
            images.append(img)
        except Exception as e:
            print(f"  ⚠ Skipping {path.name}: {e}")
    return images


def analyze_batch(model, batch_images: list, batch_num: int) -> str:
    """Send one batch of images + prompt to Gemini Vision. Returns the analysis text."""
    print(f"\n  Contacting Gemini Vision (batch {batch_num})...")
    contents = [_BATCH_PROMPT] + batch_images
    response = model.generate_content(contents)
    return response.text.strip()


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"Using model: {MODEL_NAME}\n")

    # ── Discover images ─────────────────────────────────────────────
    if not ASSETS_DIR.exists():
        print(f"ERROR: '{ASSETS_DIR}' folder not found.")
        sys.exit(1)

    all_files = list(ASSETS_DIR.rglob("*"))
    valid_images = sorted(
        [f for f in all_files if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS],
        key=lambda f: f.stat().st_size,
        reverse=True,          # Largest first — best quality photos
    )
    print(f"Found {len(valid_images)} usable images in '{ASSETS_DIR}'.")

    # Pool: top 300 largest images gives the most interesting carving photos
    pool = valid_images[:300]
    total_needed = BATCH_SIZE * NUM_BATCHES
    if len(pool) < total_needed:
        total_needed = len(pool)

    # Non-overlapping random selection across all batches
    selected = random.sample(pool, total_needed)
    batches = [selected[i * BATCH_SIZE:(i + 1) * BATCH_SIZE] for i in range(NUM_BATCHES)]

    print(f"\n{'='*60}")
    print(f"PHASE 1: Running {NUM_BATCHES} analysis batches × {BATCH_SIZE} images")
    print(f"Total images analyzed: {total_needed}")
    print(f"{'='*60}")

    batch_results = []
    for i, batch_paths in enumerate(batches, start=1):
        print(f"\nBATCH {i}/{NUM_BATCHES}: Loading {len(batch_paths)} images...")
        for p in batch_paths:
            print(f"  → {p.name} ({p.stat().st_size // 1024}KB)")

        images = load_image_batch(batch_paths)
        if not images:
            print(f"  ❌ No images loaded for batch {i}. Skipping.")
            continue

        print(f"  Loaded {len(images)} images. Sending to Gemini...")
        try:
            result = analyze_batch(model, images, i)
            batch_results.append(result)
            print(f"  ✅ Batch {i} complete — {len(result)} chars extracted.")
        except Exception as e:
            print(f"  ❌ Batch {i} failed: {e}")

    if not batch_results:
        print("\nERROR: All batches failed. Cannot generate style guide.")
        sys.exit(1)

    # ── Synthesis pass ──────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("PHASE 2: Synthesizing all batch findings into master guide...")
    print(f"{'='*60}\n")

    synthesis_input = _SYNTHESIS_PROMPT
    for i, result in enumerate(batch_results, start=1):
        synthesis_input += f"\n\n{'─'*40}\nBATCH {i} ANALYSIS:\n{'─'*40}\n{result}"

    try:
        print("Sending synthesis request to Gemini...")
        synthesis_response = model.generate_content(synthesis_input)
        master_guide = synthesis_response.text.strip()
    except Exception as e:
        print(f"Synthesis failed: {e}. Concatenating batch results as fallback.")
        master_guide = "\n\n".join(
            [f"=== BATCH {i+1} ===\n{r}" for i, r in enumerate(batch_results)]
        )

    # ── Save ────────────────────────────────────────────────────────
    STYLE_GUIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STYLE_GUIDE_PATH, "w", encoding="utf-8") as f:
        f.write(master_guide)

    print("\n" + "=" * 60)
    print("✅ MASTER STYLE GUIDE COMPLETE")
    print("=" * 60)
    print(f"\nImages analyzed: {len(selected)} across {len(batch_results)} batches")
    print(f"Style guide length: {len(master_guide)} characters")
    print(f"Saved to: {STYLE_GUIDE_PATH}")
    print("\n--- MASTER GUIDE PREVIEW (first 800 chars) ---")
    print(master_guide[:800])
    print("...\n[Full guide saved to file]")


if __name__ == "__main__":
    main()
