"""Pydantic models for Booking.com search."""

from pydantic import BaseModel
from typing import Optional


class SearchParams(BaseModel):
    destination: str
    checkin: str       # YYYY-MM-DD
    checkout: str      # YYYY-MM-DD
    adults: int = 2
    rooms: int = 1
    # Vibe / preference filters
    property_type: Optional[str] = None   # hotel, apartment, hostel, resort, villa, guesthouse, boutique
    min_review_score: Optional[int] = None  # 6, 7, 8, or 9 (maps to Booking.com's 60-90 scale)
    star_rating: Optional[int] = None     # 1-5
    sort_by: Optional[str] = None         # price, rating, distance, best_value


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
