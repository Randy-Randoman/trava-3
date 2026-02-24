"""Booking.com hotel search + CJ affiliate links."""
from .tools import booking_search, deeplink_generate

TOOLS = [booking_search, deeplink_generate]
PROMPT = """You have access to Booking.com hotel search. ALWAYS use booking_search when the user asks about hotels or places to stay.
booking_search returns a JSON array of hotel objects — you can pass this JSON directly to board_add_items to add them to the board.
Never make up hotel data. Always search first."""
