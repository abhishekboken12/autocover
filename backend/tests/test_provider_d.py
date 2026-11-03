
from pathlib import Path
from decimal import Decimal

from app.providers.provider_d import parse_provider_d


DATA_PATH = Path("data/provider_d.csv")
REGISTRY_PATH = Path("data/registry.json")


def get_result():
    return parse_provider_d(
        str(DATA_PATH),
        str(REGISTRY_PATH),
    )


def test_provider_d_extracts_valid_quotes():
    result = get_result()

    assert result.provider == "Provider D"
    assert len(result.quotes) == 9


def test_provider_d_excludes_invalid_registration():
    result = get_result()

    registrations = {
        q.registration_number for q in result.quotes
    }

    assert "WB02AB9999" not in registrations


def test_provider_d_normalizes_registration():
    result = get_result()

    assert all(
        q.registration_number.isalnum()
        for q in result.quotes
    )


def test_provider_d_converts_lakh_idv():
    result = get_result()

    quote = next(
        q for q in result.quotes
        if q.registration_number == "WB02AB1234"
        and q.plan_name == "Basic"
    )

    assert quote.idv == Decimal("330000")


def test_provider_d_handles_numeric_idv():
    result = get_result()

    quote = next(
        q for q in result.quotes
        if q.registration_number == "WB02AB1234"
        and q.plan_name == "Gold"
    )

    assert quote.idv == Decimal("332000")


def test_provider_d_parses_premium_with_commas():
    result = get_result()

    quote = next(
        q for q in result.quotes
        if q.registration_number == "WB02AB1234"
        and q.plan_name == "Basic"
    )

    assert quote.total_premium == Decimal("11670")


def test_provider_d_extracts_addons():
    result = get_result()

    quote = next(
        q for q in result.quotes
        if q.registration_number == "WB02AB1234"
        and q.plan_name == "Gold"
    )

    assert "Zero Dep" in quote.addons
    assert "RSA" in quote.addons
    assert "Engine Protect" in quote.addons


def test_provider_d_deduplicates_records():
    result = get_result()

    matching = [
        q for q in result.quotes
        if q.registration_number == "KL07DE3030"
        and q.plan_name == "Gold"
    ]

    assert len(matching) == 1


def test_provider_d_preserves_expired_quote():
    result = get_result()

    quote = next(
        q for q in result.quotes
        if q.registration_number == "DL3CAB0042"
        and q.plan_name == "Basic"
    )

    assert str(quote.valid_until) == "2026-10-15"
