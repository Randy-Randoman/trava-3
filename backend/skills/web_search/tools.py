"""Web search and image search tools using Tavily API."""

import json
import os

from langchain_core.tools import tool
from tavily import AsyncTavilyClient


@tool
async def web_search(query: str) -> str:
    """Search the web for information about destinations, activities, restaurants, and travel tips. Returns summarized results with sources."""
    api_key = os.getenv("TAVILY_API_KEY")
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


@tool
async def image_search(query: str) -> str:
    """Search for images of destinations, hotels, or activities. Returns image URLs."""
    api_key = os.getenv("TAVILY_API_KEY")
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
