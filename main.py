"""
AI Image Generation System — FastAPI entry point.

Endpoints:
  GET  /health               — liveness check
  GET  /cache/status         — returns cache stub
  POST /cache/refresh        — stub
  DELETE /cache              — stub
  POST /generate             — main generation endpoint
  GET  /difficulty-levels    — list available difficulty levels
"""

import sys
import os
import json

# CRITICAL FIX for Python 3.14 (experimental) compatibility
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from dotenv import load_dotenv
load_dotenv()

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.schemas import (
    GenerateRequest,
    GenerateResponse,
    GeneratedView,
    CacheStatusResponse,
    ErrorResponse,
    DifficultyLevelInfo,
)
from services.prompt_service import PromptService
from services.vertex_service import VertexService

# ------------------------------------------------------------------ #
# Bootstrap                                                            #
# ------------------------------------------------------------------ #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_prompt: PromptService | None = None
_vertex: VertexService | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _prompt, _vertex
    logger.info("Starting up services …")
    _prompt = PromptService()
    _vertex = VertexService()
    yield
    logger.info("Shutting down …")

# ------------------------------------------------------------------ #
# App                                                                  #
# ------------------------------------------------------------------ #

app = FastAPI(
    title="Chris Carves — AI Image Generation API",
    description="Generate sketch and color character sheets using Imagen 3",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
# Get allowed origins from environment variable or use defaults
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,https://woodcarvings-frontend.onrender.com"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_prompt() -> PromptService:
    if _prompt is None:
        raise HTTPException(status_code=503, detail="Prompt service unavailable")
    return _prompt

def get_vertex() -> VertexService:
    if _vertex is None:
        raise HTTPException(status_code=503, detail="Vertex service unavailable")
    return _vertex

# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "active", "version": "1.0.0"}

@app.get("/difficulty-levels", response_model=list[DifficultyLevelInfo], tags=["Config"])
async def get_difficulty_levels():
    return [
        {
            "id": "beginner",
            "label": "Beginner Level",
            "desc": "Simple bold forms, no cut-throughs",
            "details": "The beginner level focuses on approachability and durability, utilizing simple and bold shapes. Composition: The design must feature a single standing figure with no interactions, multiple characters, or held props/objects. Pose & Movement: The character should be in a relaxed, static pose with their head facing forward. Arms must be attached to the body, typically at the sides or with hands in pockets, and legs should be carved as mostly one solid mass. Details: Carvings should have minimal detail, with hands that are either simplified or hidden. The character can have any body type but should have a simple expression, such as happy, neutral, or grumpy. Technical Constraints: There are absolutely no cut-through areas permitted. Style: Despite being simple, the pattern must still clearly reflect Chris Hammack's recognizable carving style and avoid looking generic."
        },
        {
            "id": "intermediate",
            "label": "Intermediate Level",
            "desc": "Movement, props, expressive",
            "details": "The intermediate level introduces movement, story elements, and situational humor without introducing extreme technical difficulties. Composition: Carvings can include simple accessories, animals, tools, or props (e.g., a fish, dog, or hammer) to enhance storytelling. Pose & Movement: Figures can be in motion—such as leaning, walking, or running—and their limbs can vary independently in position. However, carvers should avoid extreme twisting of the torso. Facial Features: Faces should be more expressive and exaggerated, featuring open mouths or raised/lowered eyebrows. Heads may be turned or slightly tilted, and hair or hats can be more elaborate and positioned askew. Details & Clothing: Both hands may be visible and more defined, though overly intricate finger detail should still be avoided. Clothing can show movement with moderate folds, wrinkles, and manageable textures. Technical Constraints: Cut-throughs are allowed and encouraged, meaning arms and legs can be partially separated from the body. However, designs should not include excessively difficult undercuts or create fragile structural challenges."
        },
        {
            "id": "professional",
            "label": "Professional Level",
            "desc": "Complex scenes, deep details",
            "details": "The professional level represents the highest degree of complexity, craftsmanship, and imaginative storytelling. Composition: Designs frequently feature multiple figures, complex scenes, and strong interactions between elements. Environments, props, and supporting structures are heavily used to enhance the narrative. Pose & Movement: Characters should demonstrate dynamic movement, including twisting, bending, leaning, and interacting with other elements. Advanced body positioning, such as rotation at the hips and shoulders, is encouraged. Facial Features & Anatomy: Faces require highly expressive and detailed features, utilizing subtle expressions and deep exaggeration. Heads can be angled in complex ways, and anatomy should be refined with a believable structure. Details & Clothing: Hands must be fully visible and detailed, including carving individual fingers when appropriate. Clothing can feature complex folds, layered garments, and detailed textures like stitching and fabric patterns. Technical Constraints: Professional designs demand extensive use of cut-throughs and challenging negative spaces. Carvers are expected to execute advanced undercutting techniques, including in hard-to-reach areas."
        }
    ]

@app.get("/cache/status", response_model=CacheStatusResponse, tags=["Cache"])
async def cache_status():
    return CacheStatusResponse(cached=False, image_count=0, dropbox_link=None)

@app.post("/cache/refresh", tags=["Cache"])
async def refresh_cache():
    return {"refreshed": True, "image_count": 0}

@app.delete("/cache", tags=["Cache"])
async def clear_cache():
    return {"cleared": True}

@app.post(
    "/generate",
    response_model=GenerateResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["Generation"],
)
async def generate(
    body: GenerateRequest,
    prompt_svc: PromptService = Depends(get_prompt),
    vertex: VertexService = Depends(get_vertex),
):
    """
    Generate a 4-view character sheet using the Anchor Pipeline (front / back / left / right).
    """
    t_start = time.monotonic()

    # 1. Build optimised prompt dictionary (Front, Left, Back, Right)
    try:
        prompts_dict = await prompt_svc.build_sequential_prompts(
            body.prompt, 
            body.mode.value, 
            body.difficulty.value
        )
    except Exception as e:
        logger.error(f"[/generate] Prompt build failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prompt building failed: {e}")

    # 2. Determine target model based on user selection
    model_map = {
        "imagen_4": "imagen-4.0-generate-001",
        "imagen_3": "imagen-3.0-generate-002",
    }
    target_model = model_map.get(body.model_provider.value, "imagen-3.0-generate-002")

    # 3. Generate views via the Anchor & Reference Pipeline
    try:
        raw_views = await vertex.generate_views(prompts_dict, target_model)
    except Exception as e:
        logger.error(f"[/generate] Imagen Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    # 4. Package response
    elapsed_ms = int((time.monotonic() - t_start) * 1000)
    views = [GeneratedView(**v) for v in raw_views]

    logger.info(
        f"[/generate] Done — mode={body.mode} views={len(views)} "
        f"time={elapsed_ms}ms"
    )

    return GenerateResponse(
        success=True,
        views=views,
        mode=body.mode,
        prompt_used=prompts_dict["front"], # Returning the Anchor prompt for schema compliance
        cached_references=False,
        generation_time_ms=elapsed_ms,
    )

# ------------------------------------------------------------------ #
# Global error handler                                                 #
# ------------------------------------------------------------------ #

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "detail": str(exc)},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)