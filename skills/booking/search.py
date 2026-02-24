"""Playwright-based Booking.com hotel search scraping."""

import logging
from urllib.parse import urlencode, urlparse, urlunparse
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
                # Skip non-hotel URLs (Booking.com gives searchresults links
                # for closed/unavailable hotels — these are dead links)
                if raw_url and "searchresults" in raw_url:
                    hotel_url = None
                elif raw_url:
                    # Strip session params (aid, sid, label) — they're bound to
                    # Playwright's session and break outside it
                    if raw_url.startswith("/"):
                        raw_url = f"https://www.booking.com{raw_url}"
                    parsed = urlparse(raw_url)
                    hotel_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
                else:
                    hotel_url = None

                # Get image (try src first, then data-src for lazy-loaded images)
                img_el = await card.query_selector('img[data-testid="image"]')
                image_url = None
                if img_el:
                    image_url = await img_el.get_attribute("src")
                    # Booking.com often lazy-loads with a tiny placeholder in src
                    if not image_url or "data:image" in image_url:
                        image_url = await img_el.get_attribute("data-src")
                    if not image_url:
                        # Try srcset as last resort
                        srcset = await img_el.get_attribute("srcset")
                        if srcset:
                            image_url = srcset.split(",")[0].strip().split(" ")[0]

                # Add booking params so hotel page shows correct dates/availability
                if hotel_url:
                    separator = "&" if "?" in hotel_url else "?"
                    booking_params = urlencode({
                        "checkin": params.checkin,
                        "checkout": params.checkout,
                        "group_adults": params.adults,
                        "no_rooms": params.rooms,
                    })
                    parameterized_url = f"{hotel_url}{separator}{booking_params}"
                else:
                    parameterized_url = None

                # Build affiliate link
                affiliate_url = (
                    build_affiliate_url(parameterized_url, cj_pid, cj_aid)
                    if parameterized_url
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
