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


# Configure root logger with basic settings
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    stream=sys.stdout, 
    datefmt="%Y-%m-%d %H:%M:%S"
)

for logger_name in logging.root.manager.loggerDict:
    if logger_name.startswith('javis.'):
        logger = logging.getLogger(logger_name)
        logger.setLevel(LOG_LEVEL)
