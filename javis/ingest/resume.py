# Standard library imports
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Third-party imports
from google import genai
from pydantic import BaseModel

# Local application imports
from javis import settings

logger = logging.getLogger(__name__)

resume_folder = os.path.join(settings.DATA_DIR, "resume") 