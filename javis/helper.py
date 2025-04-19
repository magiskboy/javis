import asyncpg
from javis import settings
from google import genai
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


async def get_database_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )


def embed_contents(contents: list[str]) -> list[float]:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=contents,
    )

    return [embedding.values for embedding in response.embeddings]


def get_google_crendential():
    """Initialize and return the Google Calendar service.

    Returns:
        Resource: Google Calendar API service
    """

    CREDENTIALS_PATH = settings.DATA_DIR / "credentials.json"
    TOKEN_PATH = settings.DATA_DIR / "token.pickle"

    SCOPES = ["https://www.googleapis.com/auth/calendar", "https://mail.google.com/"]

    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Credentials file not found at: {CREDENTIALS_PATH}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=8000)
        # Save the credentials for the next run
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return creds
