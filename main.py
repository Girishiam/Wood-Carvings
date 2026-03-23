"""
AI Image Generation System — FastAPI entry point.

Endpoints:
  GET  /health               — liveness check
  GET  /cache/status         — returns cache stub (Dropbox removed)
  POST /cache/refresh        — stub
  DELETE /cache              — stub
  POST /generate             — main generation endpoint
  GET  /difficulty-levels    — list available difficulty levels
"""

import sys
import os

# CRITICAL FIX for Python 3.14 (experimental) compatibility
# Setting these modules to None in sys.modules forces Google's libraries 
# to skip the broken C-extensions and fall back to pure-Python mode.
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None

# Explicitly force pure-python implementation for protobuf
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

# Singleton services (instantiated once at startup)
_prompt: PromptService | None = None
_vertex: VertexService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise singleton services on startup; clean up on shutdown."""
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-production-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
# Dependency injectors                                                 #
# ------------------------------------------------------------------ #

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


@app.get(
    "/difficulty-levels",
    response_model=list[DifficultyLevelInfo],
    tags=["Config"],
)
async def get_difficulty_levels():
    """Return the available difficulty levels and their descriptions."""
    return [
        {
            "id": "beginner",
            "label": "Beginner Level",
            "desc": "Simple bold forms, no cut-throughs",
            "details": "The focus is on providing simple, bold, and durable designs that are approachable for new carvers. Subject: A single standing figure with no props, objects, or multiple character interactions. Pose: Static and relaxed with the head facing forward. Arms are attached to the body (often with hands in pockets), and legs are mostly one solid mass. Detail: Minimal detail with simplified or hidden hands. Technical Constraints: No cut-through areas are permitted."
        },
        {
            "id": "intermediate",
            "label": "Intermediate Level",
            "desc": "Movement, props, expressive",
            "details": "This level bridges the gap between basic shapes and professional complexity by introducing movement and situational humor. Subject: Includes simple accessories (tools, animals, or props) to enhance character-driven storytelling. Pose & Movement: Figures may be leaning, walking, or running, though extreme torso twisting is avoided. Heads may be turned or slightly tilted. Detail: Faces are more expressive (open mouths, raised eyebrows), and hands are visible and more defined, though they avoid intricate finger detail. Technical Constraints: Cut-throughs are encouraged (e.g., arms/legs separated from the body), but they must not create fragile structures or be excessively difficult to reach with standard tools."
        },
        {
            "id": "professional",
            "label": "Professional Level",
            "desc": "Complex scenes, deep details",
            "details": "Professional patterns represent the highest level of craftsmanship, characterized by deep exaggeration and complex narratives. Subject: Often features multiple figures, complex scenes, and strong character interactions. Imaginative, layered humor is a primary driver of the design. Pose & Movement: Figures demonstrate dynamic movement, including twisting, bending, and rotation at the hips and shoulders. Heads may be angled in complex ways. Detail: Highly refined anatomy and expressive facial features. Intricate textures are used for hair, hats, and clothing (e.g., stitching, deep folds, and layered garments). Hands are fully visible with individual fingers. Technical Constraints: Extensive use of challenging cut-throughs, negative spaces, and advanced undercutting in hard-to-reach areas."
        }
    ]


@app.get(
    "/cache/status",
    response_model=CacheStatusResponse,
    tags=["Cache"],
)
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
    Generate a 4-view character sheet (front / back / left / right).

    - **mode=sketch** → black & white ink line art
    - **mode=color**  → full color wood-carving folk art style
    """
    t_start = time.monotonic()

    # 1. Build optimised prompt
    try:
        final_prompt = await prompt_svc.build_prompt(
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

    try:
        raw_views = await vertex.generate_views(final_prompt, target_model)
    except Exception as e:
        logger.error(f"[/generate] Imagen 3 failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    # 3. Package response
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
        prompt_used=final_prompt,
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


# ------------------------------------------------------------------ #
# Dev runner                                                           #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)