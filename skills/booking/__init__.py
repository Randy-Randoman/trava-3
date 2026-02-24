"""Booking.com hotel search + CJ affiliate links."""
from .tools import booking_search, deeplink_generate

TOOLS = [booking_search, deeplink_generate]
PROMPT = """You have access to Booking.com hotel search. Use booking_search to find
accommodations when the user asks about hotels or places to stay. Results include
real prices, ratings, and affiliate booking links. Use deeplink_generate if you
need to create an affiliate link for a specific hotel URL."""
