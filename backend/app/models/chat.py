"""
Chat schemas - Message & History data validation
"""

from pydantic import BaseModel
from typing import List
from datetime import datetime


class ChatRequest(BaseModel):
    """Incoming chat request from frontend"""
    trip_id: str  # REQUIRED - conversation is linked to trip
    message: str
    # NO history field - backend loads from database

