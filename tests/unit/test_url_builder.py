"""Tests for Booking.com search URL construction logic."""

from urllib.parse import unquote
from skills.booking.search import build_search_url
from skills.booking.models import SearchParams


class TestBuildSearchUrl:
    """Tests for build_search_url()."""

    def test_basic_url(self, sample_search_params):
        url = build_search_url(sample_search_params)
        assert "booking.com/searchresults.html" in url
        assert "ss=Lisbon" in url
        assert "checkin=2026-04-01" in url
        assert "checkout=2026-04-05" in url
        assert "group_adults=2" in url
        assert "no_rooms=1" in url
        assert "selected_currency=EUR" in url
        assert "lang=en-us" in url

    def test_destination_with_spaces_is_encoded(self):
        params = SearchParams(
            destination="New York City",
            checkin="2026-04-01",
            checkout="2026-04-05",
        )
        url = build_search_url(params)
        # Space should be percent-encoded
        assert "New%20York%20City" in url
        assert "New York City" not in url

    def test_destination_with_unicode(self):
        params = SearchParams(
            destination="São Paulo",
            checkin="2026-04-01",
            checkout="2026-04-05",
        )
        url = build_search_url(params)
        # ã should be encoded
        assert "S%C3%A3o" in url
        # Decoded version should match
        assert "São Paulo" in unquote(url)

    def test_property_type_filter(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            property_type="hotel",
        )
        url = build_search_url(params)
        assert "nflt=" in url
        assert "ht_id%3D204" in url  # hotel = 204, URL-encoded = in nflt

    def test_boutique_property_type(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            property_type="boutique",
        )
        url = build_search_url(params)
        assert "ht_id%3D228" in url  # boutique = 228

    def test_unknown_property_type_ignored(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            property_type="treehouse",
        )
        url = build_search_url(params)
        assert "nflt=" not in url  # No filter added

    def test_min_review_score_filter(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            min_review_score=8,
        )
        url = build_search_url(params)
        # 8 → review_score=80
        assert "review_score%3D80" in url

    def test_review_score_out_of_range_ignored(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            min_review_score=5,  # Below 6, should be ignored
        )
        url = build_search_url(params)
        assert "review_score" not in url

    def test_star_rating_filter(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            star_rating=4,
        )
        url = build_search_url(params)
        assert "class%3D4" in url

    def test_star_rating_out_of_range_ignored(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            star_rating=6,  # Above 5, should be ignored
        )
        url = build_search_url(params)
        assert "class" not in url

    def test_sort_by_price(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            sort_by="price",
        )
        url = build_search_url(params)
        assert "order=price" in url

    def test_sort_by_rating(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            sort_by="rating",
        )
        url = build_search_url(params)
        assert "order=score" in url

    def test_sort_by_best_value(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            sort_by="best_value",
        )
        url = build_search_url(params)
        assert "order=bayesian_review_score" in url

    def test_unknown_sort_ignored(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            sort_by="popularity",  # Not in SORT_MAP
        )
        url = build_search_url(params)
        assert "order=" not in url

    def test_multiple_filters_combined(self, sample_search_params_with_filters):
        url = build_search_url(sample_search_params_with_filters)
        decoded = unquote(url)
        # All nflt parts should be present, semicolon-separated
        assert "ht_id=228" in decoded   # boutique
        assert "review_score=80" in decoded  # min 8
        assert "class=4" in decoded      # 4 star
        assert "order=score" in decoded  # sort by rating
        # Check adults/rooms
        assert "group_adults=3" in url
        assert "no_rooms=2" in url

    def test_case_insensitive_property_type(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            property_type="Hotel",  # Uppercase
        )
        url = build_search_url(params)
        assert "ht_id%3D204" in url

    def test_case_insensitive_sort(self):
        params = SearchParams(
            destination="Lisbon",
            checkin="2026-04-01",
            checkout="2026-04-05",
            sort_by="Price",  # Uppercase
        )
        url = build_search_url(params)
        assert "order=price" in url
