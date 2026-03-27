"""
Vertex AI / Imagen service (Migrated to Google GenAI SDK for API Key support).

Cost & Quality optimisation strategy (The Anchor Pipeline):
- Generate ONE image (the Front View Anchor).
- Use the Front View as a Subject Reference to generate Left, Back, and Right views in parallel.
- Stitch the resulting 4 images together horizontally using PIL.
"""

import sys
import os
import io
import base64
import asyncio
import logging
from PIL import Image

# Fix for Python 3.14 compatibility with protobuf
sys.modules["google._upb._message"] = None
sys.modules["google.protobuf.pyext._message"] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Individual portrait format
_ASPECT_RATIO = "3:4"

class VertexService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
             raise ValueError("GEMINI_API_KEY is not set in environment. Please check your .env file.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'imagen-3.0-generate-002' # Can be overridden in method call
        logger.info(f"[Imagen] Ready — Pipeline mode using GenAI SDK")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def generate_views(
        self,
        prompts_dict: dict[str, str],
        model_name: str = 'imagen-3.0-generate-002'
    ) -> list[dict]:
        """
        Generates views. Routes Single Characters to 16:9 Sheet, and Groups to 4-way parallel.
        """
        loop = asyncio.get_event_loop()
        
        is_group = prompts_dict.get("is_group") == "True"
        
        if is_group:
            logger.info(f"[Imagen] GROUP detected. Using 4-way Parallel Generation fallback via {model_name}...")
            view_keys = ["indiv_front", "indiv_left", "indiv_back", "indiv_right"]
            tasks = []
            for key in view_keys:
                tasks.append(loop.run_in_executor(
                    None, self._generate_single_view, prompts_dict[key], model_name
                ))
                
            results_bytes = await asyncio.gather(*tasks)
            
            logger.info("[Imagen] Phase 2: Stitching 4 separate images horizontally...")
            final_bytes = await loop.run_in_executor(
                None, self._stitch_images_horizontally, results_bytes
            )
        else:
            logger.info(f"[Imagen] Single Character detected. Generating Character Sheet via {model_name}...")
            prompt = prompts_dict["sheet"]
            final_bytes = await loop.run_in_executor(
                None, self._generate_sheet_image, prompt, model_name
            )

        logger.info("[Imagen] Pipeline complete. Returning generated sheet.")
        
        # Return as a single "sheet" to maintain compatibility with the frontend
        return [{
            "view": "sheet",
            "image_b64": base64.b64encode(final_bytes).decode("utf-8"),
            "mime_type": "image/png"
        }]

    # ------------------------------------------------------------------ #
    # Private — Generation Calls                                          #
    # ------------------------------------------------------------------ #

    def _generate_sheet_image(self, prompt: str, model_name: str) -> bytes:
        """Generates the single Character Sheet image."""
        response = self.client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9", # Wide format to fit 4 characters side-by-side
            )
        )
        if not response.generated_images:
            raise RuntimeError("Imagen returned no images for Character Sheet.")
            
        return response.generated_images[0].image.image_bytes

    def _generate_single_view(self, prompt: str, model_name: str) -> bytes:
        """Generates a single 3:4 portrait view."""
        response = self.client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=_ASPECT_RATIO,
            )
        )
        if not response.generated_images:
            raise RuntimeError("Imagen returned no images for single view.")
            
        return response.generated_images[0].image.image_bytes

    # ------------------------------------------------------------------ #
    # Private — Image Stitching                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _stitch_images_horizontally(image_bytes_list: list[bytes]) -> bytes:
        """Opens bytes in PIL, stitches side-by-side, and returns new bytes."""
        images = [Image.open(io.BytesIO(img_bytes)) for img_bytes in image_bytes_list]
        
        width, height = images[0].size
        total_width = width * len(images)
        
        stitched_image = Image.new('RGB', (total_width, height), color='white')
        
        for index, img in enumerate(images):
            x_offset = index * width
            stitched_image.paste(img, (x_offset, 0))
            
        buf = io.BytesIO()
        stitched_image.save(buf, format="PNG")
        return buf.getvalue()