"""
Chat schemas - Message & History data validation
"""

from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime


class Message(BaseModel):
    """Single chat message"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Incoming chat request from frontend"""
    trip_id: str  # REQUIRED - conversation is linked to trip
    message: str
    # NO history field - backend loads from database


class ChatResponse(BaseModel):
    """Chat response to frontend"""
    response: str
    status: Optional[str] = None
