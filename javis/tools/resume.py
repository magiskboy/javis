import asyncpg
from javis import settings


def get_top_match_resume(skills: list[str], experience: list[str]):
    """Retrieves resumes that best match the given skills and experience.
    
    This function searches the database for resumes that have the highest
    match rate with the provided skills and experience requirements.
    
    Args:
        skills: A list of strings representing required technical skills.
        experience: A list of strings representing required work experience.
        
    Returns:
        A list of matching resume objects sorted by relevance score.
        
    Raises:
        ConnectionError: If unable to connect to the resume database.
    """
    db = asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )

    