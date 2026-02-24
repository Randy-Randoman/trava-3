"""Web search and image search via Tavily."""

from .tools import image_search, web_search

TOOLS = [web_search, image_search]
PROMPT = """You can search the web for destination information, activities, restaurants, and travel tips
using web_search. Use image_search to find images of places and hotels."""
