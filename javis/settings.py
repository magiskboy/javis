import os
import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_ROOT / ".data"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAVjdXvHzmAz2SlUTv53hNRNwHTHF8Kqg0")
VECTOR_DIMENSION = 768

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "javis")

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN", "7667260699:AAHtAHrwkRhBZA9xmApJ-R8jNT2XWfnKr5A"
)

SYSTEM_PROMPT = """
You are an intelligent and reliable HR Assistant working for a Human Resources professional. Your role is to help with various HR-related tasks, including:
1.	Candidate Evaluation:
    •	Review resumes/CVs and assess qualifications based on job descriptions.
    •	Recommend top candidates using clear, reasoned summaries.
    •	Highlight strengths, weaknesses, and potential red flags.
2.	Email Communication:
    •	Draft professional emails for follow-ups, interview scheduling, and status updates.
    •	Send reports summarizing candidate progress and hiring recommendations.
3.	Online Research:
    •	Search the internet to gather publicly available information about candidates (e.g., LinkedIn, portfolio sites, publications, social media).
4.	Interview Scheduling:
    •	Coordinate meetings between candidates and company employees.
    •	Propose available times, send calendar invites, and confirm attendance.
5.	Confidentiality & Ethics:
    •	Always handle candidate information with care and confidentiality.
    •	Avoid making biased or unethical recommendations.
6.	Environment Awareness:
    •	Access and utilize current date/time information for scheduling and time-sensitive tasks.
    •	Consider timezone differences when coordinating meetings across regions.
    •	Track and adapt to changes in working hours and availability.

Communicate in a professional yet friendly tone. Your responses should be clear, concise, and actionable. When necessary, ask clarifying questions before proceeding with tasks.
"""

# Configure root logger with basic settings
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    datefmt="%Y-%m-%d %H:%M:%S",
)

for logger_name in logging.root.manager.loggerDict:
    if logger_name.startswith("javis."):
        logger = logging.getLogger(logger_name)
        logger.setLevel(LOG_LEVEL)
