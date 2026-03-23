from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum


class GenerationMode(str, Enum):
    SKETCH = "sketch"
    COLOR = "color"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    PROFESSIONAL = "professional"


class ModelProvider(str, Enum):
    IMAGEN_4 = "imagen_4"
    IMAGEN_3 = "imagen_3"


class DifficultyLevelInfo(BaseModel):
    id: DifficultyLevel
    label: str
    desc: str
    details: str



class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, description="Character description (e.g. 'grumpy cowboy with sombrero')")
    mode: GenerationMode = Field(..., description="'sketch' for ink line art, 'color' for painted wood carving")
    difficulty: DifficultyLevel = Field(DifficultyLevel.INTERMEDIATE, description="Pattern complexity level")
    model_provider: ModelProvider = Field(ModelProvider.IMAGEN_3, description="Which AI model to use")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "grumpy cowboy with mustache and sombrero",
                "mode": "sketch",
                "difficulty": "intermediate"
            }
        }


class GeneratedView(BaseModel):
    view: Literal["front", "back", "left", "right", "sheet"]
    image_b64: str
    mime_type: str = "image/png"


class GenerateResponse(BaseModel):
    success: bool
    views: list[GeneratedView]
    mode: GenerationMode
    prompt_used: str
    cached_references: bool
    generation_time_ms: int


class CacheStatusResponse(BaseModel):
    cached: bool
    image_count: int
    dropbox_link: Optional[str]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None