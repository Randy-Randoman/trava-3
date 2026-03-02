"""Tests for CJ affiliate deep link generation."""

from skills.booking.deeplink import build_affiliate_url


class TestBuildAffiliateUrl:
    """Tests for build_affiliate_url()."""

    def test_generates_cj_link_with_credentials(self):
        url = build_affiliate_url(
            "https://www.booking.com/hotel/pt/amazing-lisbon.html",
            cj_pid="12345",
            cj_aid="67890",
        )
        assert url.startswith("https://www.anrdoezrs.net/click-12345-67890?url=")
        # Original URL should be URL-encoded in the result
        assert "booking.com" in url
        assert "amazing-lisbon" in url

    def test_returns_original_url_without_pid(self):
        original = "https://www.booking.com/hotel/pt/test.html"
        result = build_affiliate_url(original, cj_pid="", cj_aid="67890")
        assert result == original

    def test_returns_original_url_without_aid(self):
        original = "https://www.booking.com/hotel/pt/test.html"
        result = build_affiliate_url(original, cj_pid="12345", cj_aid="")
        assert result == original

    def test_returns_original_url_without_both(self):
        original = "https://www.booking.com/hotel/pt/test.html"
        result = build_affiliate_url(original, cj_pid="", cj_aid="")
        assert result == original

    def test_url_encodes_hotel_url(self):
        """The hotel URL inside the CJ link should be fully URL-encoded."""
        hotel_url = "https://www.booking.com/hotel/pt/test.html?checkin=2026-04-01&checkout=2026-04-05"
        result = build_affiliate_url(hotel_url, cj_pid="111", cj_aid="222")
        # & and = and : and / should be encoded
        assert "&checkin" not in result  # Should be encoded
        assert "%26checkin" in result or "checkin%3D" in result

    def test_preserves_booking_params_in_encoded_url(self):
        """Booking params should survive encoding inside the CJ wrapper."""
        hotel_url = "https://www.booking.com/hotel/pt/test.html?checkin=2026-04-01&group_adults=2"
        result = build_affiliate_url(hotel_url, cj_pid="111", cj_aid="222")
        # The full original URL should be recoverable from the encoded version
        from urllib.parse import unquote
        encoded_part = result.split("?url=")[1]
        decoded = unquote(encoded_part)
        assert decoded == hotel_url
