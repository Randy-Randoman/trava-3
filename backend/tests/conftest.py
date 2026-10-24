"""Shared test fixtures for trava-3 skill tests."""

import os
import pytest

# Set dummy env vars so skills don't fail on missing keys during tests
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")


@pytest.fixture
def sample_search_params():
    """Basic SearchParams for Lisbon, 2 adults, 1 room."""
    from skills.booking.models import SearchParams

    return SearchParams(
        destination="Lisbon",
        checkin="2026-04-01",
        checkout="2026-04-05",
        adults=2,
        rooms=1,
    )


@pytest.fixture
def sample_search_params_with_filters():
    """SearchParams with all optional filters set."""
    from skills.booking.models import SearchParams

    return SearchParams(
        destination="Paris 7th arrondissement",
        checkin="2026-06-10",
        checkout="2026-06-15",
        adults=3,
        rooms=2,
        property_type="boutique",
        min_review_score=8,
        star_rating=4,
        sort_by="rating",
    )
