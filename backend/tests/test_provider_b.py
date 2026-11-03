
from pathlib import Path
from decimal import Decimal

from app.providers.provider_b import parse_provider_b


DATA_PATH = Path("data/provider_b.html")


def test_provider_b_extracts_quotes():
    result = parse_provider_b(str(DATA_PATH))

    assert result.provider == "Provider B"
    assert len(result.quotes) > 0


def test_provider_b_extracts_all_available_quotes():
    result = parse_provider_b(str(DATA_PATH))

    # 26 JavaScript quote records are supplied.
    assert len(result.quotes) == 26


def test_provider_b_normalizes_registration():
    result = parse_provider_b(str(DATA_PATH))

    assert all(
        quote.registration_number.isalnum()
        for quote in result.quotes
    )


def test_provider_b_extracts_plan_name():
    result = parse_provider_b(str(DATA_PATH))

    quote = next(
        q for q in result.quotes
        if q.source_quote_id == "B-101"
    )

    assert quote.plan_name == "Smart Shield"


def test_provider_b_extracts_addons():
    result = parse_provider_b(str(DATA_PATH))

    quote = next(
        q for q in result.quotes
        if q.source_quote_id == "B-101"
    )

    assert "Bumper to Bumper" in quote.addons
    assert "24x7 Roadside Assistance" in quote.addons


def test_provider_b_extracts_premium_and_gst():
    result = parse_provider_b(str(DATA_PATH))

    quote = next(
        q for q in result.quotes
        if q.source_quote_id == "B-101"
    )

    assert quote.total_premium == Decimal("12830")
    assert quote.base_premium + quote.tax_amount == Decimal("12830.00")


def test_provider_b_extracts_idv():
    result = parse_provider_b(str(DATA_PATH))

    quote = next(
        q for q in result.quotes
        if q.source_quote_id == "B-101"
    )

    assert quote.idv == Decimal("310000")


def test_provider_b_skips_unavailable_vehicles():
    result = parse_provider_b(str(DATA_PATH))

    registrations = {
        quote.registration_number
        for quote in result.quotes
    }

    assert "WB06CD5678" not in registrations
    assert "WB04ZZ1001" not in registrations


def test_provider_b_deduplicates_plan_ids():
    result = parse_provider_b(str(DATA_PATH))

    plan_ids = [
        quote.source_quote_id
        for quote in result.quotes
    ]

    assert len(plan_ids) == len(set(plan_ids))
