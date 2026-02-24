"""
Shared Playwright browser instance for web scraping (Booking.com etc.)

Singleton pattern — one headless Chromium shared across all requests.
Pages are handed out via async context manager for automatic cleanup.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class PlaywrightService:
    """Singleton browser manager. Launches headless Chromium on first use."""

    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        """Launch browser if not already running."""
        if self._browser is None or not self._browser.is_connected():
            async with self._lock:
                # Double-check after acquiring lock
                if self._browser is None or not self._browser.is_connected():
                    try:
                        self._playwright = await async_playwright().start()
                        self._browser = await self._playwright.chromium.launch(
                            headless=True
                        )
                        logger.info("Playwright browser launched")
                    except Exception as exc:
                        logger.warning(
                            "Failed to launch Playwright browser: %s. "
                            "Is Chromium installed? Run: playwright install chromium",
                            exc,
                        )
                        self._playwright = None
                        self._browser = None
                        raise

    @asynccontextmanager
    async def get_page(self) -> AsyncIterator[Page]:
        """Get a new browser page in a fresh context. Auto-cleans up."""
        await self._ensure_browser()
        context = await self._browser.new_context(user_agent=_DEFAULT_USER_AGENT)
        page = await context.new_page()
        try:
            yield page
        finally:
            await page.close()
            await context.close()

    async def shutdown(self):
        """Clean up browser and playwright."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None
        logger.info("Playwright browser shut down")


# Module-level singleton
_service = PlaywrightService()


def get_page() -> asynccontextmanager:
    """Convenience: return the singleton's page context manager."""
    return _service.get_page()


async def shutdown_playwright():
    """Call on app shutdown."""
    await _service.shutdown()
