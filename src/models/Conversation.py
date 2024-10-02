from typing import List, Dict, Any

from pydantic import BaseModel


class Conversation(BaseModel):
    """Represents a conversation with multiple messages."""
    messages: List[Dict[str, Any]]
