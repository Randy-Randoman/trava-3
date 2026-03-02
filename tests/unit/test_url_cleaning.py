"""Tests for Booking.com URL cleaning and booking param logic."""

from skills.booking.search import clean_hotel_url, append_booking_params
from skills.booking.models import SearchParams


class TestCleanHotelUrl:
    """Tests for clean_hotel_url()."""

    def test_valid_absolute_url(self):
        url = "https://www.booking.com/hotel/pt/amazing-lisbon.html?aid=123&sid=abc&label=xyz&from=searchresults"
        result = clean_hotel_url(url)
        # Should strip all query params (aid, sid, label, from)
        assert result == "https://www.booking.com/hotel/pt/amazing-lisbon.html"

    def test_relative_url_prepends_domain(self):
        url = "/hotel/pt/amazing-lisbon.html?aid=123&sid=abc"
        result = clean_hotel_url(url)
        assert result == "https://www.booking.com/hotel/pt/amazing-lisbon.html"

    def test_searchresults_path_returns_none(self):
        """URLs with /searchresults in the path are closed/unavailable hotels."""
        url = "https://www.booking.com/searchresults.html?closed_msg=1&dest=Lisbon"
        result = clean_hotel_url(url)
        assert result is None

    def test_searchresults_in_query_not_in_path_is_kept(self):
        """from=searchresults in query params should NOT cause rejection.

        This was the root cause of the 'only 1 hotel' bug — see learning.md #9.
        """
        url = "https://www.booking.com/hotel/pt/test.html?from=searchresults&aid=123"
        result = clean_hotel_url(url)
        assert result is not None
        assert result == "https://www.booking.com/hotel/pt/test.html"

    def test_none_input_returns_none(self):
        assert clean_hotel_url(None) is None

    def test_empty_string_returns_none(self):
        assert clean_hotel_url("") is None

    def test_strips_all_query_params(self):
        url = "https://www.booking.com/hotel/fr/paris-hotel.html?aid=1&sid=2&label=3&srepoch=4&from=searchresults"
        result = clean_hotel_url(url)
        assert "?" not in result
        assert result == "https://www.booking.com/hotel/fr/paris-hotel.html"

    def test_preserves_path_structure(self):
        url = "https://www.booking.com/hotel/es/barcelona-beachfront.en-gb.html?aid=123"
        result = clean_hotel_url(url)
        assert result == "https://www.booking.com/hotel/es/barcelona-beachfront.en-gb.html"

    def test_relative_searchresults_returns_none(self):
        url = "/searchresults.html?closed_msg=1"
        result = clean_hotel_url(url)
        assert result is None


class TestAppendBookingParams:
    """Tests for append_booking_params()."""

    def test_appends_to_clean_url(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            adults=2,
            rooms=1,
        )
        url = "https://www.booking.com/hotel/pt/test.html"
        result = append_booking_params(url, params)
        assert "checkin=2026-04-01" in result
        assert "checkout=2026-04-05" in result
        assert "group_adults=2" in result
        assert "no_rooms=1" in result
        # First param uses ?
        assert "?" in result

    def test_uses_ampersand_if_url_has_query(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
        )
        url = "https://www.booking.com/hotel/pt/test.html?existing=param"
        result = append_booking_params(url, params)
        # Should use & not ? since URL already has query params
        assert "?existing=param&" in result
        assert "checkin=2026-04-01" in result

    def test_custom_adults_and_rooms(self):
        params = SearchParams(
            destination="Paris",
            checkin="2026-06-10",
            checkout="2026-06-15",
            adults=4,
            rooms=2,
        )
        url = "https://www.booking.com/hotel/fr/test.html"
        result = append_booking_params(url, params)
        assert "group_adults=4" in result
        assert "no_rooms=2" in result
