"""
Vertex AI / Imagen 4 service (Migrated to Google GenAI SDK for API Key support).

Cost optimisation strategy:
- Generate ONE image (the full 4-view character sheet grid) per request.
- The single returned image is then sliced into 4 quadrants and returned as separate views.
"""

import sys
import os

# Fix for Python 3.14 compatibility with protobuf
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import io
import base64
import asyncio
import logging
from PIL import Image

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# 16:9 wide format — essential for a 4-panel horizontal turnaround sheet
_ASPECT_RATIO = "16:9"

class VertexService:
    def __init__(self):
        # We use the GEMINI_API_KEY which the user already set in .env
        # This completely bypasses the need for complex Google Cloud ADC auth!
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
             raise ValueError("GEMINI_API_KEY is not set in environment. Please checking your .env file.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'imagen-4.0-generate-001'
        logger.info(f"[Imagen] Ready — using {self.model_name} via GenAI SDK")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def generate_views(
        self,
        prompt: str,
        model_name: str = 'imagen-3.0-generate-002'
    ) -> list[dict]:
        """
        Generate a 4-view character sheet and return 4 cropped views.
        Each item in the return list: {"view": str, "image_b64": str, "mime_type": str}
        """
        loop = asyncio.get_event_loop()
        grid_image_b64 = await loop.run_in_executor(
            None, self._generate_grid, prompt, model_name
        )
        return self._split_grid(grid_image_b64)

    # ------------------------------------------------------------------ #
    # Private — generation                                                #
    # ------------------------------------------------------------------ #

    def _generate_grid(self, prompt: str, model_name: str) -> str:
        """
        Blocking call to Imagen. Returns the full grid as base64 PNG.
        """
        logger.info(f"[Imagen] Requesting generation from {model_name}...")
        response = self.client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=_ASPECT_RATIO,
            )
        )

        if not response.generated_images:
            raise RuntimeError("Imagen 4 returned no images")

        # Convert generated image bytes to base64
        raw_bytes = response.generated_images[0].image.image_bytes
        # Load into PIL to ensure it's a valid image and save as PNG just covering all bases
        img = Image.open(io.BytesIO(raw_bytes))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # ------------------------------------------------------------------ #
    # Private — return full image                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _split_grid(grid_b64: str) -> list[dict]:
        """
        Returns the full character sheet as a single image (no splitting).
        The prompt already arranges all 4 views horizontally inside one image.
        """
        return [{
            "view": "sheet",
            "image_b64": grid_b64,
            "mime_type": "image/png",
        }]