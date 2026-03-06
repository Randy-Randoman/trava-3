"""CJ affiliate deep link generation for Booking.com URLs."""

from urllib.parse import quote


def build_affiliate_url(hotel_url: str, cj_pid: str, cj_aid: str) -> str:
    """Wrap a Booking.com URL in a CJ affiliate deep link."""
    if not cj_pid or not cj_aid:
        return hotel_url  # Return original URL if no CJ credentials
    encoded = quote(hotel_url, safe="")
    return f"https://www.anrdoezrs.net/click-{cj_pid}-{cj_aid}?url={encoded}"
