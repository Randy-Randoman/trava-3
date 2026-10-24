"""Web search and image search via Tavily."""

from .tools import image_search, web_search

TOOLS = [web_search, image_search]
PROMPT = """Use web_search to find real, up-to-date information:
- Activities and things to do at a destination
- Restaurants, tours, experiences
- Flight options: search "Skyscanner flights [origin] to [destination] [month year]" or "Google Flights [origin] [destination]". Use the direct Skyscanner/Google Flights/Kayak URL as bookingUrl — NEVER use blog posts or articles.
- General travel tips and destination info
web_search returns JSON: each result has "title", "content", and "url" fields.
Use the "url" field as bookingUrl when adding items to the board.
Use image_search to find real photos of places and hotels.
Summarize web_search results conversationally for the user — don't dump raw JSON."""
