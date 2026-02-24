"""Playwright-based Booking.com hotel search scraping."""

import logging
from .models import SearchParams, Hotel
from .deeplink import build_affiliate_url

logger = logging.getLogger(__name__)


async def search_booking(
    params: SearchParams, cj_pid: str = "", cj_aid: str = ""
) -> list[Hotel]:
    """Search Booking.com and return hotel results."""
    # Lazy import: app.services is only on sys.path when the backend is running
    from app.services.playwright import get_page

    url = (
        f"https://www.booking.com/searchresults.html"
        f"?ss={params.destination}"
        f"&checkin={params.checkin}"
        f"&checkout={params.checkout}"
        f"&group_adults={params.adults}"
        f"&no_rooms={params.rooms}"
        f"&selected_currency=EUR"
    )

    hotels = []
    async with get_page() as page:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Wait for results to load
        try:
            await page.wait_for_selector(
                '[data-testid="property-card"]', timeout=15000
            )
        except Exception:
            logger.warning("Timed out waiting for property cards — page may have changed layout")
            return hotels

        # Extract hotel cards
        cards = await page.query_selector_all('[data-testid="property-card"]')

        for card in cards[:10]:  # Limit to top 10
            try:
                name = await _safe_text(card, '[data-testid="title"]')
                price = await _safe_text(
                    card, '[data-testid="price-and-discounted-price"]'
                )
                rating = await _safe_text(
                    card, '[data-testid="review-score"] > div:first-child'
                )
                review_count = await _safe_text(
                    card,
                    '[data-testid="review-score"] > div:nth-child(2) > div:nth-child(2)',
                )
                distance = await _safe_text(card, '[data-testid="distance"]')

                # Get URL
                link_el = await card.query_selector(
                    'a[data-testid="title-link"]'
                )
                raw_url = (
                    await link_el.get_attribute("href") if link_el else None
                )
                hotel_url = (
                    f"https://www.booking.com{raw_url}"
                    if raw_url and raw_url.startswith("/")
                    else raw_url
                )

                # Get image
                img_el = await card.query_selector('img[data-testid="image"]')
                image_url = (
                    await img_el.get_attribute("src") if img_el else None
                )

                # Build affiliate link
                affiliate_url = (
                    build_affiliate_url(hotel_url, cj_pid, cj_aid)
                    if hotel_url
                    else None
                )

                hotels.append(
                    Hotel(
                        name=name or "Unknown Hotel",
                        price=price,
                        rating=rating,
                        review_count=review_count,
                        distance=distance,
                        url=hotel_url,
                        image_url=image_url,
                        affiliate_url=affiliate_url,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse hotel card: {e}")
                continue

    return hotels


async def _safe_text(parent, selector: str) -> str | None:
    """Safely extract text from a selector, returning None on failure."""
    el = await parent.query_selector(selector)
    if el:
        text = await el.text_content()
        return text.strip() if text else None
    return None
