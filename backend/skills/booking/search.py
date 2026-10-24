"""Playwright-based Booking.com hotel search scraping."""

import logging
from urllib.parse import quote, urlencode, urlparse, urlunparse

from app.services.playwright import get_page
from .models import SearchParams, Hotel

logger = logging.getLogger(__name__)

# Booking.com property-type IDs (ht_id in nflt param)
PROPERTY_TYPE_MAP: dict[str, str] = {
    "hotel": "204",
    "apartment": "201",
    "hostel": "203",
    "resort": "206",
    "villa": "208",
    "guesthouse": "216",
    "boutique": "228",
}

# Booking.com sort-order values (order= URL param)
SORT_MAP: dict[str, str] = {
    "price": "price",
    "rating": "score",
    "distance": "distance_from_search",
    "best_value": "bayesian_review_score",
}


def build_search_url(params: SearchParams) -> str:
    """Build a Booking.com search URL from SearchParams. Pure function, no side effects."""
    url = (
        f"https://www.booking.com/searchresults.html"
        f"?ss={quote(params.destination)}"
        f"&checkin={params.checkin}"
        f"&checkout={params.checkout}"
        f"&group_adults={params.adults}"
        f"&no_rooms={params.rooms}"
        f"&selected_currency=EUR"
        f"&lang=en-us"
    )

    # --- Append vibe / preference filters ---
    nflt_parts: list[str] = []

    if params.property_type:
        ht_id = PROPERTY_TYPE_MAP.get(params.property_type.lower())
        if ht_id:
            nflt_parts.append(f"ht_id={ht_id}")

    if params.min_review_score and 6 <= params.min_review_score <= 9:
        nflt_parts.append(f"review_score={params.min_review_score * 10}")

    if params.star_rating and 1 <= params.star_rating <= 5:
        nflt_parts.append(f"class={params.star_rating}")

    if nflt_parts:
        url += f"&nflt={quote(';'.join(nflt_parts))}"

    if params.sort_by:
        order = SORT_MAP.get(params.sort_by.lower())
        if order:
            url += f"&order={order}"

    return url


def clean_hotel_url(raw_url: str | None) -> str | None:
    """Clean a raw Booking.com hotel URL: skip search redirects, strip session params.

    Returns the clean URL or None if the URL should be skipped.
    """
    if not raw_url:
        return None

    # Skip non-hotel URLs (Booking.com gives /searchresults.html
    # links for closed/unavailable hotels — these are dead links).
    # Note: don't match on full URL — every hotel URL has
    # &from=searchresults in its query string.
    if "/searchresults" in urlparse(raw_url).path:
        return None

    # Prepend domain for relative URLs
    if raw_url.startswith("/"):
        raw_url = f"https://www.booking.com{raw_url}"

    # Strip session params (aid, sid, label) — they're bound to
    # Playwright's session and break outside it
    parsed = urlparse(raw_url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def append_booking_params(hotel_url: str, params: SearchParams) -> str:
    """Append checkin/checkout/adults/rooms params to a clean hotel URL."""
    separator = "&" if "?" in hotel_url else "?"
    booking_params = urlencode({
        "checkin": params.checkin,
        "checkout": params.checkout,
        "group_adults": params.adults,
        "no_rooms": params.rooms,
    })
    return f"{hotel_url}{separator}{booking_params}"


async def search_booking(params: SearchParams) -> list[Hotel]:
    """Search Booking.com and return hotel results."""
    url = build_search_url(params)
    logger.info(f"Booking search URL: {url}")

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
        logger.info(f"Found {len(cards)} property-card elements")

        skipped = 0
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
                logger.debug(f"  [{name}] link_el={'found' if link_el else 'MISSING'}, raw_url={raw_url!r}")

                hotel_url = clean_hotel_url(raw_url)
                if raw_url and hotel_url is None:
                    logger.info(f"Skipping '{name}' — URL is a searchresults redirect")

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
                    parameterized_url = append_booking_params(hotel_url, params)
                else:
                    parameterized_url = None

                hotel_name = name or "Unknown Hotel"

                if hotel_url is None:
                    logger.info(f"Skipping hotel '{hotel_name}' — no valid URL")
                    skipped += 1
                    continue

                logger.info(f"Parsed hotel '{hotel_name}' — url OK")

                hotels.append(
                    Hotel(
                        name=hotel_name,
                        price=price,
                        rating=rating,
                        review_count=review_count,
                        distance=distance,
                        url=parameterized_url or hotel_url,
                        image_url=image_url,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse hotel card (name={name!r}): {e}", exc_info=True)
                continue

    logger.info(f"Returning {len(hotels)} hotels ({skipped} skipped due to missing URL)")
    return hotels


async def _safe_text(parent, selector: str) -> str | None:
    """Safely extract text from a selector, returning None on failure."""
    el = await parent.query_selector(selector)
    if el:
        text = await el.text_content()
        return text.strip() if text else None
    return None
