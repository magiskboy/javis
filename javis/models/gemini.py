from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.gemini import GeminiModel

GEMINI_API_KEY = "AIzaSyAVjdXvHzmAz2SlUTv53hNRNwHTHF8Kqg0"

google_provider = GoogleGLAProvider(api_key=GEMINI_API_KEY)

gemini = GeminiModel(model_name='gemini-2.0-flash-exp', provider=google_provider)

__all__ = [
    "gemini",
]