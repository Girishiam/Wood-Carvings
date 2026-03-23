"""
Prompt service: builds Imagen-optimized prompts for sketch and color modes.

Key design principles (v3):
- User description is injected FIRST, TWICE — highest Imagen weight.
- Multi-character detection: if user mentions a "friend", "buddy", "companion"
  etc. the layout enforces ALL characters appear in EVERY panel.
- Clothing default: characters get appropriate default clothing unless specified.
- Gemini enrichment DISABLED (was hallucinating replacements).
- Per-panel gesture variation for visual interest.
- Content-safe remapping for weapon terms.
"""

import re
import sys
import os

# Fix for Python 3.14 compatibility
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------- #
# Load the local Artist Style Guide                                       #
# ---------------------------------------------------------------------- #

_STYLE_GUIDE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "services", "artist_style_guide.txt"
)
try:
    with open(_STYLE_GUIDE_PATH, "r", encoding="utf-8") as _f:
        _RAW_GUIDE = _f.read().strip()
        _SECTIONS = _RAW_GUIDE.split("=========================================")
        if len(_SECTIONS) >= 4:
            _STYLE_GUIDE_UNIVERSAL = _SECTIONS[1].strip()
            _STYLE_GUIDE_COLOR = _SECTIONS[2].strip()
            _STYLE_GUIDE_SKETCH = _SECTIONS[3].strip()
        else:
            _STYLE_GUIDE_UNIVERSAL = _RAW_GUIDE
            _STYLE_GUIDE_COLOR = ""
            _STYLE_GUIDE_SKETCH = ""
    logger.info("[Prompt] Artist style guide loaded.")
except Exception as _e:
    logger.warning(f"[Prompt] Could not load style guide: {_e}. Using fallback.")
    _STYLE_GUIDE_UNIVERSAL = "Chris Hammack folk-art caricature style. Strict anatomical consistency."
    _STYLE_GUIDE_COLOR = "Basswood carving texture with visible tool marks."
    _STYLE_GUIDE_SKETCH = "Clean black and white character sketch."

# ---------------------------------------------------------------------- #
# Multi-character detection                                               #
# ---------------------------------------------------------------------- #

_MULTI_CHAR_PATTERNS = [
    r"\bfriend\b", r"\bbuddy\b", r"\bpal\b", r"\bcompanion\b",
    r"\band his\b", r"\band her\b", r"\band a\b", r"\band an\b",
    r"\btwo\b", r"\b2\b", r"\bpair\b", r"\bduo\b", r"\bcouple\b",
    r"\bbrother\b", r"\bsister\b", r"\bpartner\b", r"\bcolleague\b",
    r"\bmate\b", r"\band the\b", r"\bwith his\b", r"\bwith her\b",
    r"\bwith a\b", r"\bwith an\b",
]


def _is_multi_character(text: str) -> bool:
    for pattern in _MULTI_CHAR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------- #
# Content-safe keyword remapping                                          #
# ---------------------------------------------------------------------- #

_CONTENT_SAFE_MAP = [
    (r"\bgun\b",      "old-fashioned carved musket prop"),
    (r"\bguns\b",     "carved muskets props"),
    (r"\bpistol\b",   "carved flintlock pistol prop"),
    (r"\brifle\b",    "carved long-rifle prop"),
    (r"\bshotgun\b",  "carved shotgun prop"),
    (r"\bfirearm\b",  "carved firearm prop"),
    (r"\bweapon\b",   "carved prop weapon"),
    (r"\bknife\b",    "carved whittling knife prop"),
    (r"\bsword\b",    "carved wooden sword prop"),
    (r"\baxe\b",      "carved wooden axe prop"),
    (r"\bdagger\b",   "carved wooden dagger prop"),
    (r"\bcigarette\b","carved prop cigarette"),
    (r"\bcigger\b",   "carved prop cigar"),
    (r"\bcigar\b",    "carved prop cigar"),
    (r"\bsmoking\b",  "holding a carved prop cigar in mouth"),
]


def _apply_safe_map(text: str) -> str:
    result = text
    for pattern, replacement in _CONTENT_SAFE_MAP:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


# ---------------------------------------------------------------------- #
# Negative prompt — broad suppression                                     #
# ---------------------------------------------------------------------- #

# ---------------------------------------------------------------------- #
# Negative prompt — broad suppression                                     #
# ---------------------------------------------------------------------- #

_NEGATIVE_PROMPT = (
    # Layout suppressions (Forces exactly 4 horizontal panels)
    "2 panels, 3 panels, 5 panels, 6 panels, 2x2 grid, square grid, "
    "missing views, incomplete turnaround, overlapping characters, "
    
    # Text suppressions (Strengthened)
    "text, watermark, signature, writing, font, typography, numbers, "
    "text labels, panel labels, annotations, callouts, words, letters, "
    
    # Style and content suppressions
    "photorealistic human, real life photograph, cinematic live action, "
    "3D CGI render, 3D octane render, plastic action figure, anime, manga, "
    "shirtless unless specified, naked unless specified, topless unless specified, "
    "different number of characters per panel, missing character, "
    "extra characters, wrong character, real weapons, real animals"
)

# ---------------------------------------------------------------------- #
# Layout blocks (single-character vs multi-character group)               #
# ---------------------------------------------------------------------- #

_LAYOUT_SINGLE = """\
COMPOSITION — 4-PANEL ORTHOGRAPHIC TURNAROUND SHEET:
This is an official character design turnaround sheet. ONE image split into \
EXACTLY FOUR equal vertical columns (25% width each):
  Column 1 (25%): FRONT VIEW — character faces directly toward viewer.
  Column 2 (25%): LEFT SIDE PROFILE — character faces the left edge.
  Column 3 (25%): BACK VIEW — character faces directly away from viewer.
  Column 4 (25%): RIGHT SIDE PROFILE — character faces the right edge.
All 4 columns on the same ground plane. Full body head-to-toe in every column.
Pure white background. ZERO text. ZERO labels. ZERO borders. Pure illustration only.
ZOOM OUT: all 4 views must fit comfortably with clear white space between them.
HORIZONTAL ROW ONLY — do NOT use a 2×2 grid.

CONSISTENCY LAW: ALL FOUR PANELS SHOW THE EXACT SAME CHARACTER.
Same body shape, same face, same clothing, same props. ONLY the camera angle changes.
This is ONE character seen from 4 directions — NOT 4 different characters.\
"""

_LAYOUT_MULTI = """\
COMPOSITION — 4-PANEL ORTHOGRAPHIC GROUP TURNAROUND SHEET:
This is an official character design turnaround sheet for a GROUP of characters. \
ONE image split into EXACTLY FOUR equal vertical columns (25% width each):
  Column 1 (25%): FRONT VIEW — all characters face directly toward viewer.
  Column 2 (25%): LEFT SIDE PROFILE — all characters face the left edge.
  Column 3 (25%): BACK VIEW — all characters face directly away from viewer.
  Column 4 (25%): RIGHT SIDE PROFILE — all characters face the right edge.
All 4 columns on the same ground plane. Full body head-to-toe in every column.
Pure white background. ZERO text. ZERO labels. ZERO borders. Pure illustration only.
ZOOM OUT: all characters in all 4 views must fit comfortably.
HORIZONTAL ROW ONLY — do NOT use a 2×2 grid.

CRITICAL GROUP CONSISTENCY LAW:
EVERY SINGLE PANEL MUST CONTAIN ALL CHARACTERS DESCRIBED. 
If two characters are described, BOTH must appear in ALL 4 panels.
Do NOT drop or omit any character in any panel. 
The same characters, same clothing, same props appear in every panel — only the camera angle changes.
Characters MUST stand next to each other in every panel, maintaining the same relative positions.\
"""

# ---------------------------------------------------------------------- #
# Clothing enforcement                                                    #
# ---------------------------------------------------------------------- #

_CLOTHING_RULE = """\
CLOTHING RULE (MANDATORY):
Every character MUST be fully clothed with appropriate garments unless the prompt \
explicitly says "shirtless", "topless", or "naked".
DEFAULT CLOTHING (apply if not specified): shirt or top garment, trousers or pants, shoes or boots.
Invent reasonable period-appropriate or character-appropriate clothing based on the character description.
Do NOT generate bare skin on torso, chest, or legs unless explicitly requested.\
"""

# ---------------------------------------------------------------------- #
# Mode-specific medium instructions                                       #
# ---------------------------------------------------------------------- #

_SKETCH_MEDIUM = """\
MEDIUM — PROFESSIONAL 2D PENCIL AND INK LINE ART SKETCH (MANDATORY):
This is a clean professional 2D FLAT character design illustration, NOT a 3D render.
Style: thick confident ink outlines with clean interior pencil sketch lines.
Rendering: soft hatching for shadow areas, NO heavy cross-hatching, NO dark scribbling.
Look: a professional concept artist's character sheet — polished, readable, beautiful line art.
Clean pure white paper background. Black ink lines only. Soft grey pencil shading for depth.
NO color of any kind. NO fills. NO gradient washes. NO digital painting style.
NO 3D render look. NO CGI lighting. NO plastic surface appearance. Flat 2D illustration only.
The linework must be clean, intentional, and elegant — like a professional animation studio's \
character design reference sheet.\
"""

_COLOR_MEDIUM = """\
MEDIUM — HAND-CARVED BASSWOOD FOLK-ART FIGURINE (MANDATORY):
This looks like a PHYSICAL hand-carved basswood wood toy figurine, NOT a real person.
Every surface shows visible V-tool chisel cuts and U-gouge ripple texture.
Paint: thin translucent folk-art acrylic wash — actual raw wood grain visible through color.
Earth-tone base palette with selective accent colors. Dark antiquing wash in crevices.
Studio photography lighting with a soft true cast shadow.
NOT photorealistic. NOT anime. NOT 3D CGI. NOT an action figure or plastic toy.
Genuine hand-carved wood caricature figurine aesthetic.\
"""

# ---------------------------------------------------------------------- #
# Gesture variation per panel                                             #
# ---------------------------------------------------------------------- #

_GESTURE_BLOCK = """\
GESTURE VARIATION (each panel must show a DIFFERENT arm/leg position):
- FRONT VIEW: Arms at slightly different heights — one arm lower, one mid-level. \
  Feet shoulder-width apart or with one foot slightly forward.
- LEFT SIDE PROFILE: Slight weight shift — one leg forward, one back. \
  Prop arm raised, free arm relaxed.
- BACK VIEW: Shoulders at slightly different angles from behind. \
  Arms positioned differently than the front. Slight head turn.
- RIGHT SIDE PROFILE: Contrapposto stance — weight on one leg, slight relaxed lean. \
  Different arm angle from the left side view.\
"""

# ---------------------------------------------------------------------- #
# Difficulty constraints                                                  #
# ---------------------------------------------------------------------- #

_DIFFICULTY_MODS = {
    "beginner": (
        "DIFFICULTY — BEGINNER:\n"
        "Ultra-smooth simplified surfaces. Bold simple forms. Minimal surface detail.\n"
        "Props are simplified but still present and clearly identifiable.\n"
        "Static conservative pose. Legs mostly one solid form. No fragile thin areas."
    ),
    "intermediate": (
        "DIFFICULTY — INTERMEDIATE:\n"
        "Standard moderate surface detail and texture throughout.\n"
        "Props rendered clearly with basic detail. Hands visible with thick sturdy fingers.\n"
        "Follow the gesture variation. Gentle believable movement in pose."
    ),
    "professional": (
        "DIFFICULTY — PROFESSIONAL:\n"
        "Maximum detail everywhere: fabric folds, stitching, buckles, layered textures.\n"
        "Props fully detailed — every component rendered. Individual thick fingers visible.\n"
        "Dynamic expressive poses. Complex undercutting and negative spaces."
    ),
}


# ---------------------------------------------------------------------- #
# Prompt Service                                                          #
# ---------------------------------------------------------------------- #

class PromptService:
    def __init__(self):
        # Gemini enrichment intentionally DISABLED — it hallucinated replacement characters.
        logger.info("[Prompt] Service ready — direct injection mode (enrichment disabled).")

    async def build_prompt(
        self, user_concept: str, mode: str, difficulty: str
    ) -> str:
        if not user_concept or user_concept.lower().strip() in [
            "i need an idea", "idea", "beginner idea", ""
        ]:
            user_concept = (
                "A stocky portly tradesman with a bushy mustache, "
                "wearing overalls and a work cap."
            )

        # Apply content-safe remapping
        safe_concept = _apply_safe_map(user_concept)
        if safe_concept != user_concept:
            logger.info(f"[Prompt] Safe-map applied: '{user_concept}' → '{safe_concept}'")

        # Detect multi-character scene
        multi = _is_multi_character(safe_concept)
        layout_block = _LAYOUT_MULTI if multi else _LAYOUT_SINGLE
        char_label = "GROUP" if multi else "CHARACTER"
        logger.info(f"[Prompt] Multi-character: {multi}")

        # Pick mode blocks
        if mode == "sketch":
            medium_block = _SKETCH_MEDIUM
            style_guide_active = f"{_STYLE_GUIDE_UNIVERSAL}\n\n{_STYLE_GUIDE_SKETCH}"
            style_label = "PENCIL SKETCH STYLE REFERENCE (lowest priority):"
        else:
            medium_block = _COLOR_MEDIUM
            style_guide_active = f"{_STYLE_GUIDE_UNIVERSAL}\n\n{_STYLE_GUIDE_COLOR}"
            style_label = "WOOD CARVING STYLE REFERENCE (lowest priority):"

        diff_block = _DIFFICULTY_MODS.get(difficulty, _DIFFICULTY_MODS["intermediate"])

        # ---------------------------------------------------------------
        # PROMPT ASSEMBLY
        # Order = priority. Earlier text = higher Imagen weight.
        # ---------------------------------------------------------------
        final_prompt = f"""\
================================================================
{char_label} TO DRAW — ABSOLUTE TOP PRIORITY. DO NOT CHANGE:
================================================================
{safe_concept}

IMPORTANT — READ THIS AGAIN BEFORE DRAWING:
{safe_concept}
NEVER GENERATE: {_NEGATIVE_PROMPT}

MANDATORY TRAIT ENFORCEMENT:
- BODY TYPE: If the description says "fat", "chubby", "heavy", "portly" — draw an \
obviously obese character with a large protruding belly, wide hips, thick arms, and double chin.
  If the description says "skinny", "thin", "slim", "lanky" — draw a very lean bony character \
with visible angular features and narrow frame.
- FACIAL FEATURES: If a beard, moustache, or specific face feature is described — it MUST be \
clearly visible and prominent in every single panel.
- PROPS AND ITEMS: Every prop, tool, or item mentioned MUST appear in every panel, \
held/worn correctly in the character's hand or on their body.
- CLOTHING: {_CLOTHING_RULE}
- SUBSTITUTION FORBIDDEN: Do NOT substitute any prop or trait with something else. \
If a cigar is described, draw a cigar — not a pipe, not a lantern.

================================================================
{layout_block}
================================================================

{medium_block}

================================================================
{_GESTURE_BLOCK}
================================================================

{diff_block}

================================================================
{style_label}
Apply only where it does not conflict with anything above.
{style_guide_active}
================================================================

FINAL SELF-CHECK — verify all before rendering:
1. Does every panel show: {safe_concept}?
2. Are there exactly 4 panels in a single horizontal row?
3. Are all clothing and props present and correct in every panel?
4. Is there ZERO text, ZERO labels, ZERO annotations on the image?
5. Is the medium correct: {mode}?


"""

        logger.info(
            f"[Prompt] Built ({mode}/{difficulty}, multi={multi}) — "
            f"{len(final_prompt)} chars | '{safe_concept[:80]}'"
        )
        return final_prompt