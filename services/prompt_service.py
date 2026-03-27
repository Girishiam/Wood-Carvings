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

_NEGATIVE_PROMPT = (
    "text, watermark, signature, writing, font, typography, numbers, "
    "text labels, panel labels, annotations, callouts, words, letters, "
    # --- Kill the CGI/digital art look ---
    "3D CGI render, 3D octane render, Blender render, Unreal Engine, "
    "Pixar style, Disney style, video game character, mobile game asset, "
    "plastic action figure, vinyl toy, smooth plastic sheen, "
    "subsurface scattering, specular highlights, glossy skin, "
    "photorealistic human, real life photograph, cinematic live action, "
    "anime, manga, cartoon illustration, digital painting, concept art, "
    "airbrushed skin, soft gradients, smooth blended surfaces, "
    "rounded organic forms, rubber texture, silicone texture, "
    # --- Enforce wood carving look ---
    "smooth surfaces anywhere on figure, uncarved surfaces, "
    "machine-made, factory-produced, mass manufactured, "
    # --- Content rules ---
    "shirtless unless specified, naked unless specified, topless unless specified, "
    "real weapons, real animals, "
    # --- Consistency rules ---
    "only three views, missing fourth view, only 3 angles, "
    "different outfit per angle, different face per angle, different props per angle, "
    "extra characters, wrong character"
)

_CLOTHING_RULE = (
    "Every character MUST be fully clothed with appropriate garments unless requested. "
    "DEFAULT: shirt/top, trousers/pants, shoes/boots."
)

_SKETCH_MEDIUM = (
    "MEDIUM — PROFESSIONAL 2D PENCIL AND INK LINE ART SKETCH. "
    "Clean flat 2D character design illustration. Pure white background. "
    "Strict black ink outlines. Pencil cross-hatching for shading. NO color whatsoever. "
    "Pure grayscale tonal range only, from bright white highlights to deep black shadows."
)

_COLOR_MEDIUM = (
    "MEDIUM -- PHYSICAL HAND-CARVED BASSWOOD FOLK-ART FIGURINE. "
    "This is NOT a 3D render, NOT a CGI character, NOT a digital painting. "
    "This is a REAL CARVED WOODEN OBJECT painted with thin wash acrylics. "
    "SURFACE TEXTURE IS CRITICAL: Every surface -- face, cheeks, nose, hat, shirt, pants, boots, hair -- "
    "must be composed entirely of flat angular geometric FACETS meeting at SHARP CARVED EDGES. "
    "Like a low-poly sculpture where every plane is a deliberate knife cut. "
    "Deep V-tool gouge marks visible everywhere. NO smooth transitions between planes whatsoever. "
    "PAINT STYLE: Thin semi-transparent wash acrylic. Wood grain texture visible beneath the paint. "
    "Matte finish only. Darker paint pooled into carved recesses for shadow. NO gloss, NO sheen. "
    "SKIN COLOR: Warm terracotta brick-pink base, deeper reddish-brown in deep-carved recesses. "
    "HAIR AND BEARD: Carved in blocky directional gouge-cut chunks, not smooth strands. "
    "Pure white background. Looks like a photograph of a real physical carved wooden object."
)

_DIFFICULTY_MODS = {
    "beginner": """DIFFICULTY — BEGINNER:
The beginner level focuses on approachability and durability, utilizing simple and bold shapes. Composition: The design must feature a single standing figure with no interactions, multiple characters, or held props/objects. Pose & Movement: The character should be in a relaxed, static pose with their head facing forward. Arms must be attached to the body, typically at the sides or with hands in pockets, and legs should be carved as mostly one solid mass. Details: Carvings should have minimal detail, with hands that are either simplified or hidden. The character can have any body type but should have a simple expression, such as happy, neutral, or grumpy. Technical Constraints: There are absolutely no cut-through areas permitted. Style: Despite being simple, the pattern must still clearly reflect Chris Hammack's recognizable carving style and avoid looking generic.""",
    "intermediate": """DIFFICULTY — INTERMEDIATE:
The intermediate level introduces movement, story elements, and situational humor without introducing extreme technical difficulties. Composition: Carvings can include simple accessories, animals, tools, or props (e.g., a fish, dog, or hammer) to enhance storytelling. Pose & Movement: Figures can be in motion—such as leaning, walking, or running—and their limbs can vary independently in position. However, carvers should avoid extreme twisting of the torso. Facial Features: Faces should be more expressive and exaggerated, featuring open mouths or raised/lowered eyebrows. Heads may be turned or slightly tilted, and hair or hats can be more elaborate and positioned askew. Details & Clothing: Both hands may be visible and more defined, though overly intricate finger detail should still be avoided. Clothing can show movement with moderate folds, wrinkles, and manageable textures. Technical Constraints: Cut-throughs are allowed and encouraged, meaning arms and legs can be partially separated from the body. However, designs should not include excessively difficult undercuts or create fragile structural challenges.""",
    "professional": """DIFFICULTY — PROFESSIONAL:
The professional level represents the highest degree of complexity, craftsmanship, and imaginative storytelling. Composition: Designs frequently feature multiple figures, complex scenes, and strong interactions between elements. Environments, props, and supporting structures are heavily used to enhance the narrative. Pose & Movement: Characters should demonstrate dynamic movement, including twisting, bending, leaning, and interacting with other elements. Advanced body positioning, such as rotation at the hips and shoulders, is encouraged. Facial Features & Anatomy: Faces require highly expressive and detailed features, utilizing subtle expressions and deep exaggeration. Heads can be angled in complex ways, and anatomy should be refined with a believable structure. Details & Clothing: Hands must be fully visible and detailed, including carving individual fingers when appropriate. Clothing can feature complex folds, layered garments, and detailed textures like stitching and fabric patterns. Technical Constraints: Professional designs demand extensive use of cut-throughs and challenging negative spaces. Carvers are expected to execute advanced undercutting techniques, including in hard-to-reach areas."""
}

_VIEWS = {
    "front": "STRICT FRONT VIEW (0 degrees) — character faces viewer directly. Both arms visible.",
    "left": "STRICT LEFT PROFILE (90 degrees) — character faces the left edge. Left arm raised slightly.",
    "back": "STRICT BACK VIEW (180 degrees) — character faces directly away. View from behind.",
    "right": "STRICT RIGHT PROFILE (270 degrees) — character faces the right edge. Right arm relaxed."
}

# ---------------------------------------------------------------------- #
# Prompt Service                                                          #
# ---------------------------------------------------------------------- #

class PromptService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        logger.info("[Prompt] Service ready — sequential Anchor & Reference mode.")

    async def _augment_concept(self, concept: str, style_guide: str, diff_block: str) -> str:
        """Uses Gemini Flash to expand a short concept into a locked visual blueprint for cross-angle consistency."""
        if not self.client:
            return concept
            
        loop = asyncio.get_event_loop()
        prompt = f"""
You are an expert prompt engineer for an AI image generator specializing in Chris Hammack folk-art wood carving caricatures.
The user wants to generate a 4-angle character reference sheet. Their brief concept is: '{concept}'

Your job is to produce a LOCKED VISUAL IDENTITY CARD — a single highly specific paragraph (60-100 words) that pins down every visual trait so precisely that an image generator cannot deviate between the front, left, back, and right views of the same character.

You MUST explicitly define ALL of the following without exception:
1. BODY TYPE: One of — squat/portly with tiny legs and large gut, OR tall/wiry/spindly with oversized head. Be specific.
2. HEAD & FACE: Nose shape (bulbous? beak-like? droopy?), eye style (squinted? wide? deep-set?), mouth (open grin? clenched? showing teeth?), stubble/beard/mustache exact description.
3. HAT OR HAIR: Exact hat type and color, OR hair style and color. One or the other, be decisive.
4. TOP GARMENT: Specific item, specific color (e.g. "faded mustard-yellow flannel shirt", "orange hunting vest over brown plaid").
5. BOTTOM GARMENT: Specific item, specific color (e.g. "olive drab cargo pants", "worn denim jeans with belt").
6. FOOTWEAR: Specific (e.g. "chunky brown leather boots", "battered white sneakers").
7. PROPS: If any — exactly one or two items, exactly what they look like.
8. EXPRESSION/POSE: One clear emotion and stance.

Adhere strictly to these difficulty constraints: {diff_block}
Adhere strictly to this style: {style_guide}

CRITICAL RULES:
- Every detail you invent must be REPEATED IDENTICALLY across all 4 views — you are locking the character's identity.
- Do NOT use vague words like "colorful", "various", "some", "appropriate". Be concrete and specific.
- Do NOT describe multiple outfit options. Pick ONE and commit to it.
- Return ONLY the locked visual description paragraph. No intro, no bullet points, no headers.
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

        multi = _is_multi_character(safe_concept)
        char_label = "GROUP" if multi else "CHARACTER"

        if mode == "sketch":
            # Force black and white override directly on the concept to fight user color descriptions
            safe_concept = f"BLACK AND WHITE PENCIL SKETCH of {safe_concept}"
            medium_block = _SKETCH_MEDIUM + "\nCRITICAL: DO NOT USE ANY COLOR. Ignore any colors mentioned in the description. Pure grayscale only."
            style_guide_active = f"{_STYLE_GUIDE_UNIVERSAL}\n{_STYLE_GUIDE_SKETCH}"
        else:
            medium_block = _COLOR_MEDIUM
            style_guide_active = f"{_STYLE_GUIDE_UNIVERSAL}\n{_STYLE_GUIDE_COLOR}"

        diff_block = _DIFFICULTY_MODS.get(difficulty, _DIFFICULTY_MODS["intermediate"])
        
        # ------------------------------------------------------------------ #
        # Inject Context Augmentation (LLM expands details for consistency)
        # ------------------------------------------------------------------ #
        augmented_concept = await self._augment_concept(safe_concept, style_guide_active, diff_block)

        # ------------------------------------------------------------------ #
        # Consistency Lock Header — prepended to every prompt
        # ------------------------------------------------------------------ #
        consistency_lock = f"""IDENTITY LOCK — THIS IS ONE SINGLE CHARACTER VIEWED FROM DIFFERENT ANGLES:
The character described below has ONE fixed identity. Every visual trait — face, hat, clothing colors, props, body shape — is IDENTICAL across all views. Do not change, add, or remove any detail between angles. Treat this like rotating a physical carved figurine: the object does not change, only the camera angle changes.
LOCKED CHARACTER IDENTITY:
{augmented_concept}"""

        sheet_desc = ("FOUR-VIEW CHARACTER REFERENCE SHEET. "
                     "Exactly 4 views of the SAME character arranged side by side in a single row, left to right: "
                     "(1) FRONT VIEW facing viewer, (2) LEFT PROFILE facing left edge, "
                     "(3) BACK VIEW facing away, (4) RIGHT PROFILE facing right edge. "
                     "All 4 views MUST appear. Single continuous pure white background. "
                     "Full body head-to-toe in every view. Equal spacing between views.")

        final_prompt = f"""
CAMERA ANGLE AND LAYOUT:
{sheet_desc}

{consistency_lock}

MANDATORY TRAIT ENFORCEMENT:
- CLOTHING: {_CLOTHING_RULE}
- Do NOT substitute props. Draw exactly what is requested.
- MUST show the exact SAME character 4 times on the same image.
- Face, hat, shirt color, pants color, boots, and props must be PIXEL-IDENTICAL in design across all 4 views.

MEDIUM & STYLE:
{medium_block}
{style_guide_active}
{diff_block}

NEVER GENERATE:
{_NEGATIVE_PROMPT}
"""
        prompts = {
            "is_group": str(multi),
            "front": final_prompt.strip(), 
            "sheet": final_prompt.strip()
        }

        # Build individual angle prompts for group fallback
        for view_name, angle_desc in _VIEWS.items():
            indiv_prompt = f"""
CAMERA ANGLE AND LAYOUT:
{angle_desc}
Centered. Full body head-to-toe. Pure white background. Single isolated view.

{consistency_lock}

MANDATORY TRAIT ENFORCEMENT:
- CLOTHING: {_CLOTHING_RULE}
- Do NOT substitute props. Draw exactly what is requested.
- This is ONE specific angle of a physical carved figurine — the character does not change, only the camera rotates.
- Face shape, hat, clothing colors, and all props must match the locked identity above exactly.

MEDIUM & STYLE:
{medium_block}
{style_guide_active}
{diff_block}

NEVER GENERATE:
{_NEGATIVE_PROMPT}
"""
            prompts[f"indiv_{view_name}"] = indiv_prompt.strip()

        logger.info(f"[Prompt] Built dynamic prompt map (Group: {multi}) for '{safe_concept[:50]}...'")
        return prompts