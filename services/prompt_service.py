"""
Prompt service: builds Imagen-optimized prompts for sequential character generation.
Generates an Anchor prompt (Front) and 3 Reference prompts (Left, Back, Right).
"""

import re
import sys
import os
import logging
import asyncio
from google import genai

# Fix for Python 3.14 compatibility
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

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
# Content-safe remapping & Suppressions                                   #
# ---------------------------------------------------------------------- #

_CONTENT_SAFE_MAP = [
    # Firearms & Weapons
    (r"\bgun\b",       "prominent old-fashioned carved musket prop"),
    (r"\bguns\b",      "prominent carved muskets props"),
    (r"\bpistol\b",    "prominent carved flintlock pistol prop"),
    (r"\brifle\b",     "prominent carved long-rifle prop"),
    (r"\bshotgun\b",   "prominent carved shotgun prop"),
    (r"\bfirearm\b",   "prominent carved firearm prop"),
    (r"\bweapon\b",    "prominent carved prop weapon"),
    (r"\bknife\b",     "prominent carved whittling knife prop"),
    (r"\bsword\b",     "prominent carved wooden sword prop"),
    (r"\baxe\b",       "prominent carved wooden axe prop"),
    (r"\bdagger\b",    "prominent carved wooden dagger prop"),
    (r"\bspear\b",     "prominent carved wooden spear prop"),
    (r"\bpitchfork\b", "oversized carved wooden pitchfork prop"),
    (r"\bbow\b",       "prominent carved wooden bow prop"),
    (r"\bcrossbow\b",  "prominent carved wooden crossbow prop"),
    (r"\bwhip\b",      "prominent carved coiled whip prop"),
    (r"\bshield\b",    "oversized carved wooden shield prop"),
    
    # Explosives
    (r"\bbomb\b",      "prominent carved round cartoon bomb prop"),
    (r"\bdynamite\b",  "prominent carved bundle of dynamite sticks prop"),
    (r"\bexplosive\b", "prominent carved cartoon explosive prop"),
    
    # Smoking & Drinking
    (r"\bcigarette\b", "prominent carved prop cigarette"),
    (r"\bcigger\b",    "prominent carved prop cigar"),
    (r"\bcigar\b",     "prominent carved prop cigar"),
    (r"\bsmoking\b",   "holding a prominent carved prop cigar in mouth"),
    (r"\bpipe\b",      "prominent carved wooden smoking pipe prop"),
    (r"\bbeer\b",      "oversized carved root beer mug prop"),
    (r"\balcohol\b",   "prominent carved jug prop"),
    (r"\bwhiskey\b",   "prominent carved jug prop"),
    (r"\bbooze\b",     "prominent carved jug prop"),
    (r"\bwine\b",      "prominent carved prop bottle"),
    (r"\bflask\b",     "prominent carved metal-looking flask prop"),
    
    # Edgy/Gore elements mapped to folk-art
    (r"\bskull\b",     "prominent carved wooden skull prop"),
    (r"\bblood\b",     "red painted detail"),
    (r"\bgore\b",      "red painted detail"),
]

def _apply_safe_map(text: str) -> str:
    result = text
    for pattern, replacement in _CONTENT_SAFE_MAP:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result

# Shared exclusions safe for both modes
_NEGATIVE_PROMPT_BASE = (
    "text, watermark, writing, labels, numbers, angle labels, degree symbols, "
    "measurement annotations, view labels, panel titles, "
    "3D CGI render, Pixar, Disney, video game asset, "
    "photorealistic photograph, cinematic lighting, "
    "anime, manga, cartoon illustration, "
    "plastic toy, mass manufactured figurine, "
    "real weapons, shirtless, nudity, "
    "missing view, different outfit per angle, different face per angle, "
    "perspective distortion, vanishing point, foreshortening, "
    "three-quarter view, isometric view, worm's eye view, bird's eye view, "
    "realistic human proportions, tall slim figure, elegant proportions, model proportions"
)

# Sketch mode: ban color AND all consistency drift between panels
_NEGATIVE_PROMPT_SKETCH = (
    _NEGATIVE_PROMPT_BASE + ", "
    "color, colors, colored, colorful, full color, "
    "gray, grey, gray tones, grayscale, tonal fills, gradient fills, "
    "painted, oil painting, acrylic painting, watercolor, digital painting, "
    "photorealistic, photograph, 3D render, CGI, "
    "solid black filled areas, large black silhouette fills, blacked-out areas, "
    "dark back view, silhouette back view, blacked-out back view, "
    "three-quarter view, 3/4 angle, diagonal angle view, "
    "different hat shape between views, different hat size between views, "
    "different face between views, different outfit between views, "
    "prop missing in any panel, prop switching hands, "
    "inconsistent line weight between panels, different art style between panels"
)

# Color mode: ban B&W and ban smooth/plastic look — push toward painted wood carving
_NEGATIVE_PROMPT_COLOR = (
    _NEGATIVE_PROMPT_BASE + ", "
    "black and white, monochrome, grayscale, colorless, desaturated, "
    "sketch, line art, pen and ink, pencil drawing, stencil, "
    "smooth skin, smooth surfaces, blended surfaces, airbrushed, "
    "glossy finish, shiny, specular highlights, plastic texture, rubber texture, "
    "uncarved wood, raw unpainted wood, polished wood"
)

_DIFFICULTY_MODS = {
    "beginner": (
        "POSE: fully upright, static. Arms at sides or resting on belly. "
        "Legs as one solid block. No gaps between body parts. "
        "EXPRESSION: one clear readable emotion — happy, grumpy, or smug. "
        "STYLE: simple and bold — the personality comes through the face, not the pose."
    ),
    "intermediate": (
        "POSE: slight weight shift, mild lean, or one arm raised holding prop. "
        "Arms can separate from torso. Expressive body language. "
        "EXPRESSION: highly exaggerated — wide grin, deep frown, raised eyebrow, puffed cheeks. "
        "PROPS: oversized and comical — the prop should look HUGE relative to the stumpy body. "
        "STYLE: funky and characterful — the figure should feel alive and humorous."
    ),
    "professional": (
        "POSE: fully dynamic — leaning, gesturing, reacting, mid-action. "
        "Arms and legs in expressive positions. Body twist allowed. "
        "EXPRESSION: extreme caricature — bugged eyes, gaping mouth, exaggerated grimace. "
        "PROPS: elaborate and story-telling — the prop defines who this character is. "
        "STYLE: maximum personality and humor — push every feature to its comic extreme. "
        "Gnome proportions (giant head, tiny legs) must stay dominant even in dynamic poses."
    ),
}

# ---------------------------------------------------------------------- #
# Prompt Service                                                          #
# ---------------------------------------------------------------------- #

class PromptService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        logger.info("[Prompt] Service ready — sequential Anchor & Reference mode.")

    async def _augment_concept(self, concept: str, style_guide: str, diff_block: str, mode: str = "color") -> str:
        """Uses Gemini Flash to expand a short concept into a locked visual blueprint for cross-angle consistency."""
        if not self.client:
            return concept

        is_sketch = (mode == "sketch")

        loop = asyncio.get_event_loop()

        if is_sketch:
            prompt = f"""
You are writing a character identity lock for a woodcarving pattern generator.
Concept: '{concept}'

⚠️ PRESERVE THE CONCEPT EXACTLY: If the user said "dentist", the character IS a dentist.
If the user said "funny" or "silly", the expression MUST reflect that. Never substitute a generic character.

IDENTIFY THE CHARACTER TYPE:
- ANIMAL concept → anthropomorphized animal: upright, wearing clothes, animal head/face. Do NOT humanize.
- HUMAN concept → human caricature in profession-specific outfit with profession-specific prop.

Output ONE SHORT PARAGRAPH of 40–55 words.
Describe ONLY the large silhouette elements:
1. EXACT character type from the user's concept (use their exact words)
2. Proportions: enormous head, squat body, stumpy legs, oversized hands
3. ONE hat or hair item
4. ONE profession-specific top garment
5. ONE profession-specific bottom garment
6. ONE profession-specific prop — which hand
7. ONE expression word (use the user's adjective if given: funny, grumpy, angry, jolly)

NO colors. NO fabric textures. NO surface detail.
POSE: upright, spine straight, feet flat.
Return ONLY the locked description. No intro. No bullets.

Difficulty: {diff_block}
"""
        else:
            prompt = f"""
You are an expert prompt engineer for an AI image generator specializing in Chris Hammack folk-art wood carving caricatures.
The user wants a 4-angle orthographic carving pattern. Concept: '{concept}'

⚠️ MOST CRITICAL RULE: You MUST preserve the user's EXACT character concept.
- If the user said "dentist" → the character IS a dentist. White coat, dental tools. No substitutions.
- If the user said "pirate" → the character IS a pirate. Eye patch, tricorn hat. No substitutions.
- If the user said "funny" or "silly" → give the character a comical exaggerated expression or pose.
- NEVER replace the stated profession/archetype with a generic craftsman, farmer, or tradesman.
- NEVER ignore the user's adjectives ("grumpy", "funny", "angry", "jolly") — they define the expression.

IDENTIFY THE CHARACTER TYPE:
- ANIMAL concept (bear, wolf, raccoon…) → anthropomorphized animal: upright, wearing clothes, animal head/face. Do NOT humanize.
- HUMAN concept (dentist, pirate, chef…) → human caricature wearing the EXACT profession-specific outfit and holding the EXACT profession-specific prop.

Output: ONE paragraph (60–100 words), a locked visual identity card.

DEFINE ALL OF:
1. EXACT CHARACTER TYPE from the user's concept — use their words, not substitutes
2. BODY: squat barrel-chest, enormous head (40% of height), stumpy legs, oversized hands, wide flat feet
3. FACE: nose, eyes, mouth — and the EXACT EXPRESSION the user described
4. PROFESSION-SPECIFIC OUTFIT: the clothing this character type actually wears
5. PROFESSION-SPECIFIC PROP: the tool/item this character type actually uses — ONE prop, which hand
6. HAT or HAIR: one specific item and color
7. FOOTWEAR: flat-bottomed, specific color

Difficulty: {diff_block}
Style: {style_guide}

RULES:
- Keep the character exactly what the user described — do not drift to generic folk-art archetypes
- Commit to specific colors for all garments
- Return ONLY the locked description paragraph. No intro, no bullets, no headers.
"""
        try:
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
            )
            if response.text:
               logger.info(f"[Prompt] LLM Augmentation Success: expanded to {len(response.text)} chars.")
               return response.text.strip()
        except Exception as e:
            logger.error(f"[Prompt] Concept augmentation failed: {e}")
            
        return concept

    async def build_sequential_prompts(self, user_concept: str, mode: str, difficulty: str) -> dict[str, str]:
        if not user_concept or user_concept.lower().strip() in ["i need an idea", "idea", "beginner idea", ""]:
            user_concept = "A stocky portly tradesman with a bushy mustache, wearing overalls and a work cap."

        safe_concept = _apply_safe_map(user_concept)
        if safe_concept != user_concept:
            logger.info(f"[Prompt] Safe-map applied: '{user_concept}' → '{safe_concept}'")

        if mode == "sketch":
            style_guide_active = f"{_STYLE_GUIDE_UNIVERSAL}\n{_STYLE_GUIDE_SKETCH}"
            negative_prompt_text = _NEGATIVE_PROMPT_SKETCH
        else:
            style_guide_active = f"{_STYLE_GUIDE_UNIVERSAL}\n{_STYLE_GUIDE_COLOR}"
            negative_prompt_text = _NEGATIVE_PROMPT_COLOR

        diff_block = _DIFFICULTY_MODS.get(difficulty, _DIFFICULTY_MODS["intermediate"])

        # ------------------------------------------------------------------ #
        # Augment concept — mode-specific
        # ------------------------------------------------------------------ #
        augmented_concept = await self._augment_concept(safe_concept, style_guide_active, diff_block, mode)

        # ------------------------------------------------------------------ #
        # Mode-specific prompt blocks
        # ------------------------------------------------------------------ #

        if mode == "sketch":
            render_line = (
                "Black and white orthographic character design turnaround sheet. "
                "Medium: clean pen-and-ink on white paper. "
                "Style: professional concept art line drawing — bold outer silhouette contour, "
                "angular interior lines only at major form plane transitions "
                "(cheek planes, brow ridge, shoulder breaks, arm cylinders, clothing folds, boot soles). "
                "Faceted low-poly style — lines are geometric and angular, not smooth or curved. "
                "No shading. No gray. No cross-hatching. No color. No texture fills. "
                "Pure black ink on pure white background only."
            )
            identity_lock = (
                f"CHARACTER IDENTITY — identical across all 4 views, only angle changes:\n"
                f"{augmented_concept}"
            )
            carver_rules = (
                f"C.A.R.V.E.R. PATTERN RULES:\n"
                f"- Each view is perfectly ORTHOGRAPHIC — no perspective, no foreshortening\n"
                f"- Outer silhouette is BOLD and CLOSED — this is the bandsaw cut line\n"
                f"- Feet are on the bottom edge (flat for beginner, slight lift allowed for professional)\n"
                f"- Proportions: enormous head (40% of height), squat torso, stumpy legs, oversized hands\n"
                f"- EXPRESSION and POSTURE: follow the difficulty level below — {diff_block}\n"
                f"- Interior lines only where carving planes change — keep line count LOW\n"
                f"- All 4 views identical height and aligned on same baseline\n"
                f"- The character's PERSONALITY must read clearly — exaggerate the expression and pose"
            )
        else:
            render_line = (
                "Full color painted basswood folk-art carved figurine. "
                "Bold vivid saturated acrylic paint. Flat matte finish. "
                "Faceted angular carved wood surface with visible gouge marks at every plane junction. "
                "Pure white background."
            )
            identity_lock = (
                f"IDENTITY LOCK — THIS IS ONE PHYSICAL FIGURINE ROTATED ON A TURNTABLE. "
                f"The figurine does NOT change between views — only the camera angle changes. "
                f"Every visual trait below is physically carved and cannot change between views:\n"
                f"{augmented_concept}"
            )
            carver_rules = (
                f"C.A.R.V.E.R. REQUIREMENTS:\n"
                f"- ORTHOGRAPHIC: Perfectly flat view, zero perspective distortion, zero foreshortening.\n"
                f"- SILHOUETTE: Bold unambiguous closed outline — this is the bandsaw cut line.\n"
                f"- FEET: Flat on the bottom edge.\n"
                f"- PROPORTIONS: Enormous head (40% of height), squat barrel torso, "
                f"  stumpy legs, oversized hands, large flat feet. Gnome/troll caricature.\n"
                f"- POSE & EXPRESSION: follow difficulty level — {diff_block}\n"
                f"- The character's PERSONALITY must be immediately readable — "
                f"  exaggerate the expression, push the pose, make the prop feel OVERSIZED and comical.\n"
                f"- SIMPLICITY: Every carved line must serve a purpose.\n"
                f"- BANDSAW TEST: Could someone print this, glue it to a wood block, "
                f"  and cut it out cleanly? If not — simplify."
            )

        view_configs = {
            "front": (
                "FRONT VIEW",
                "Camera faces character directly, 0 degrees. "
                "Character faces viewer. Perfectly flat — zero perspective."
            ),
            "left": (
                "LEFT SIDE VIEW",
                "Camera at character's true left, 90 degrees. "
                "Pure side profile facing left. Perfectly flat — zero perspective."
            ),
            "back": (
                "BACK VIEW",
                "Camera directly behind character, 180 degrees. "
                "Character faces away. Perfectly flat — zero perspective. "
                "Same height as front view."
            ),
            "right": (
                "RIGHT SIDE VIEW",
                "Camera at character's true right, 270 degrees. "
                "Pure side profile facing right — EXACT MIRROR of the left side view. "
                "Same silhouette width as left side."
            ),
        }

        sheet_layout = (
            "OUTPUT FORMAT: Single wide horizontal image with exactly 4 equal panels side by side.\n"
            "NO TEXT, NO LABELS, NO NUMBERS anywhere in the image — pure illustration only.\n"
            "Left to right:\n"
            "  Panel 1 — FRONT: character faces viewer directly. Pure flat orthographic.\n"
            "  Panel 2 — LEFT SIDE: pure side profile, character faces left. NOT a 3/4 view.\n"
            "  Panel 3 — BACK: character faces completely away. Same hat and outfit visible from behind.\n"
            "  Panel 4 — RIGHT SIDE: pure side profile, character faces right. "
            "EXACT HORIZONTAL MIRROR of Panel 2 — identical silhouette, just flipped.\n\n"
            "CONSISTENCY LAWS — these are absolute, not suggestions:\n"
            "1. HAT: exact same hat in all 4 panels — same brim width, same crown shape, same tilt\n"
            "2. FACE: same nose, same jaw, same expression in all views — no simplification between panels\n"
            "3. CLOTHING: exact same shirt, pants, footwear in every panel\n"
            "4. PROP: the prop stays in the SAME HAND in every panel where it is visible — "
            "do not switch hands, do not drop the prop in any panel\n"
            "5. HEIGHT: all 4 figures are IDENTICAL HEIGHT — align their feet on one baseline, "
            "their hat tops on one ceiling line\n"
            "6. SILHOUETTE: Panel 4 RIGHT SIDE is the exact horizontal mirror of Panel 2 LEFT SIDE — "
            "same outline width, same hat brim overhang, same boot profile\n"
            "7. No 3/4 views — panels 2 and 4 must be pure 90-degree side profiles\n"
            "8. No perspective — all panels are perfectly flat orthographic drawings"
        )

        prompts = {
            "is_group": "False",
            "negative_prompt": negative_prompt_text,
            "convert_to_sketch": "False",
            "sheet": "",
            "front": "",
        }

        for view_name, (label, angle_desc) in view_configs.items():
            indiv_prompt = (
                f"{render_line}\n\n"
                f"VIEW: {label}\n"
                f"{angle_desc}\n\n"
                f"{identity_lock}\n\n"
                f"{carver_rules}\n\n"
                f"Fully clothed. Centered on white background. No drop shadow.\n"
                f"Do not generate: {negative_prompt_text}"
            )
            prompts[f"indiv_{view_name}"] = indiv_prompt.strip()

        prompts["sheet"] = (
            f"{render_line}\n\n"
            f"{sheet_layout}\n\n"
            f"{identity_lock}\n\n"
            f"{carver_rules}\n\n"
            f"Fully clothed. Pure white background. No drop shadow.\n"
            f"Do not generate: {negative_prompt_text}"
        )
        prompts["front"] = prompts["indiv_front"]

        logger.info(f"[Prompt] Built C.A.R.V.E.R.-compliant 4-view set for '{safe_concept[:50]}...'")
        return prompts