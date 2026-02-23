"""
Trip schemas - The "Final JSON" output schema
"""

from pydantic import BaseModel
from typing import List, Literal, Optional


class Stop(BaseModel):
    """A stop/destination in the trip"""
    id: str
    name: str
    location: str
    date: str
    duration: str
    notes: Optional[str] = None


class Stay(BaseModel):
    """Accommodation details"""
    id: str
    name: str
    type: Literal["hotel", "airbnb", "hostel", "other"]
    location: str
    checkIn: str
    checkOut: str
    price: Optional[float] = None
    currency: Optional[str] = "USD"
    bookingUrl: Optional[str] = None


class Activity(BaseModel):
    """A planned activity"""
    id: str
    name: str
    description: Optional[str] = None
    location: str
    date: str
    time: Optional[str] = None
    duration: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "USD"
    category: Literal["sightseeing", "food", "adventure", "relaxation", "culture", "other"]


class TripSummary(BaseModel):
    """Trip overview information"""
    destination: str
    startDate: str
    endDate: str
    budget: Optional[float] = None
    currency: Optional[str] = "USD"
    travelers: int
    vibe: Optional[str] = None


class Trip(BaseModel):
    """Complete trip data - the board output"""
    trip: TripSummary
    stops: List[Stop] = []
    stays: List[Stay] = []
    activities: List[Activity] = []
