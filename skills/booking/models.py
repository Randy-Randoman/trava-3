"""Pydantic models for Booking.com search."""

from pydantic import BaseModel
from typing import Optional


class SearchParams(BaseModel):
    destination: str
    checkin: str       # YYYY-MM-DD
    checkout: str      # YYYY-MM-DD
    adults: int = 2
    rooms: int = 1


class Hotel(BaseModel):
    name: str
    price: Optional[str] = None        # e.g. "€150"
    currency: Optional[str] = None
    rating: Optional[str] = None       # e.g. "8.7"
    review_count: Optional[str] = None # e.g. "1,234"
    distance: Optional[str] = None     # e.g. "1.2 km from center"
    url: Optional[str] = None          # Booking.com URL
    image_url: Optional[str] = None
    affiliate_url: Optional[str] = None
