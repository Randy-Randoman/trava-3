"""Web search and image search tools using Tavily API."""

import json

from langchain_core.tools import tool
from tavily import AsyncTavilyClient

from app.core.config import settings


async def search_web(query: str) -> str:
    """Search the web via Tavily; returns a JSON list of {title, content, url} (or a message)."""
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        return "Error: TAVILY_API_KEY not set in environment."

    try:
        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(
            query, max_results=8, search_depth="basic"
        )
    except Exception as e:
        return f"Search failed: {e}"

    results = []
    for r in response.get("results", []):
        results.append({"title": r["title"], "content": r["content"], "url": r["url"]})
    return json.dumps(results) if results else "No results found."


async def search_images(query: str) -> str:
    """Search images via Tavily; returns up to 5 image URLs as a bullet list (or a message)."""
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        return "Error: TAVILY_API_KEY not set in environment."

    try:
        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(
            query, max_results=5, search_depth="basic", include_images=True
        )
    except Exception as e:
        return f"Image search failed: {e}"

    images = response.get("images", [])
    if not images:
        return "No images found."
    return "\n".join([f"- {url}" for url in images[:5]])


@tool
async def web_search(query: str) -> str:
    """Search the web for information about destinations, activities, restaurants, and travel tips. Returns summarized results with sources."""
    return await search_web(query)


@tool
async def image_search(query: str) -> str:
    """Search for images of destinations, hotels, or activities. Returns image URLs."""
    return await search_images(query)
