
from pathlib import Path
from decimal import Decimal

from app.providers.provider_a import parse_provider_a
from app.schemas.insurance import CoverageType, PremiumBasis


DATA_PATH = Path("data/provider_a.json")


def test_provider_a_parses_valid_quotes():
    result = parse_provider_a(str(DATA_PATH))

    assert result.provider == "Provider A"
    assert len(result.quotes) > 0


def test_provider_a_captures_declined_quotes():
    result = parse_provider_a(str(DATA_PATH))

    assert len(result.declined) == 2
    assert all(
        decline.provider == "Provider A"
        for decline in result.declined
    )


def test_provider_a_normalizes_registration():
    result = parse_provider_a(str(DATA_PATH))

    assert all(
        quote.registration_number.isalnum()
        for quote in result.quotes
    )


def test_provider_a_calculates_gst():
    result = parse_provider_a(str(DATA_PATH))

    quote = next(
        q for q in result.quotes
        if q.registration_number == "WB02AB1234"
        and q.plan_name == "Essential"
    )

    assert quote.base_premium == Decimal("9965")
    assert quote.tax_amount == Decimal("1793.70")
    assert quote.total_premium == Decimal("11758.70")
    assert quote.premium_basis == PremiumBasis.PRE_TAX


def test_provider_a_handles_gst_inclusive_premium():
    result = parse_provider_a(str(DATA_PATH))

    quote = next(
        q for q in result.quotes
        if q.registration_number == "DL3CAB0042"
        and q.plan_name == "Comprehensive Plus"
    )

    assert quote.premium_basis == PremiumBasis.TAX_INCLUSIVE
    assert round(quote.base_premium + quote.tax_amount, 2) == 34370.0
    assert quote.total_premium == 34370.0


def test_provider_a_deduplicates_quotes():
    result = parse_provider_a(str(DATA_PATH))

    matching_quotes = [
        q for q in result.quotes
        if q.registration_number == "WB02AB1234"
        and q.plan_name == "Comprehensive Plus"
    ]

    assert len(matching_quotes) == 1


def test_provider_a_preserves_missing_tax_as_zero():
    result = parse_provider_a(str(DATA_PATH))

    quote = next(
        q for q in result.quotes
        if q.registration_number == "MH12EF4321"
        and q.plan_name == "Essential"
    )

    assert quote.tax_amount == 0.0
    assert quote.total_premium == quote.base_premium


def test_provider_a_preserves_addons():
    result = parse_provider_a(str(DATA_PATH))

    quote = next(
        q for q in result.quotes
        if q.registration_number == "WB02AB1234"
        and q.plan_name == "Comprehensive Plus"
    )

    assert "ZERO_DEP" in quote.addons
    assert "RSA" in quote.addons
