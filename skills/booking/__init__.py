"""Booking.com hotel search."""
from .tools import booking_search

TOOLS = [booking_search]
PROMPT = """You have access to Booking.com hotel search. ALWAYS use booking_search when the user asks about hotels or places to stay.
booking_search returns a JSON array of hotel objects — you can pass this JSON directly to board_add_items to add them to the board.
Never make up hotel data. Always search first.

## Matching the user's vibe
booking_search supports filters to match user preferences:
- property_type: hotel, apartment, hostel, resort, villa, guesthouse, boutique
- min_review_score: 6, 7, 8, or 9 (out of 10)
- star_rating: 1-5
- sort_by: price, rating, distance, best_value

When the user describes a vibe or preference, translate it into filters:
- "cozy boutique" → property_type="boutique", min_review_score=8
- "cheap and central" → sort_by="price", min_review_score=7
- "luxury resort" → property_type="resort", star_rating=5, sort_by="rating"
- "budget hostel" → property_type="hostel", sort_by="price"
- "highly rated" → min_review_score=9, sort_by="rating"
Also use the destination field to target specific neighborhoods (e.g. "Lisbon Alfama" instead of just "Lisbon")."""
