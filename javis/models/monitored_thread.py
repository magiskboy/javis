from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MonitoredThread(BaseModel):
    """Model for storing monitored email threads."""

    thread_id: str
    candidate_email: str
    hr_telegram_id: str
    expiry_time: datetime
    last_message_id: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        from_attributes = True
