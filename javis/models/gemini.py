from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.gemini import GeminiModel

from javis import settings

google_provider = GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)

gemini = GeminiModel(model_name=settings.GEMINI_MODEL, provider=google_provider)

__all__ = [
    "gemini",
]