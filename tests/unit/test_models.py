"""Tests for Booking.com Pydantic models."""

import pytest
from pydantic import ValidationError
from skills.booking.models import SearchParams, Hotel


class TestSearchParams:
    """Tests for SearchParams model."""

    def test_minimal_params(self):
        p = SearchParams(destination="Lisbon", checkin="2026-04-01", checkout="2026-04-05")
        assert p.destination == "Lisbon"
        assert p.adults == 2  # default
        assert p.rooms == 1   # default
        assert p.property_type is None
        assert p.min_review_score is None
        assert p.star_rating is None
        assert p.sort_by is None

    def test_all_fields(self):
        p = SearchParams(
            destination="Paris",
            checkin="2026-06-10",
            checkout="2026-06-15",
            adults=4,
            rooms=2,
            property_type="boutique",
            min_review_score=8,
            star_rating=5,
            sort_by="price",
        )
        assert p.adults == 4
        assert p.rooms == 2
        assert p.property_type == "boutique"
        assert p.min_review_score == 8
        assert p.star_rating == 5
        assert p.sort_by == "price"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            SearchParams(checkin="2026-04-01", checkout="2026-04-05")  # no destination

    def test_destination_with_spaces(self):
        p = SearchParams(destination="New York City", checkin="2026-04-01", checkout="2026-04-05")
        assert p.destination == "New York City"

    def test_destination_with_special_chars(self):
        p = SearchParams(destination="São Paulo", checkin="2026-04-01", checkout="2026-04-05")
        assert p.destination == "São Paulo"


class TestHotel:
    """Tests for Hotel model."""

    def test_minimal_hotel(self):
        h = Hotel(name="Test Hotel")
        assert h.name == "Test Hotel"
        assert h.price is None
        assert h.url is None

    def test_full_hotel(self):
        h = Hotel(
            name="Grand Lisboa",
            price="€150",
            currency="EUR",
            rating="8.7",
            review_count="1,234",
            distance="1.2 km from center",
            url="https://www.booking.com/hotel/pt/grand-lisboa.html",
            image_url="https://cf.bstatic.com/images/hotel/max1024x768/123.jpg",
        )
        assert h.rating == "8.7"
        assert h.review_count == "1,234"
        assert "grand-lisboa" in h.url
