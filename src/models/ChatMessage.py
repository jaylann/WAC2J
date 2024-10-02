from datetime import datetime

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Represents a single chat message."""
    sender: str
    timestamp: datetime
    content: str
