import asyncpg
from javis import settings
from google import genai

async def get_database_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )


def embed_contents(contents: list[str]) -> list[float]:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=contents,
    )

    return [embedding.values for embedding in response.embeddings]