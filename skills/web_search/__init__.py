"""Web search and image search via Tavily."""

from .tools import image_search, web_search

TOOLS = [web_search, image_search]
PROMPT = """Use web_search to find real, up-to-date information:
- Activities and things to do at a destination (include booking URLs from search results)
- Restaurants, tours, experiences (include URLs and prices when available)
- Flight options (search for flights on Skyscanner/Google Flights, include URLs)
- General travel tips and destination info
Use image_search to find real photos of places and hotels.
When adding web_search results to the board, always include the source URL as bookingUrl so cards are clickable."""
