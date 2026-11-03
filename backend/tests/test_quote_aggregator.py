
from datetime import date

import pytest

from app.services.quote_aggregator import (
    find_vehicle,
    get_insurance_quotes,
)


def test_vehicle_lookup():
    vehicle = find_vehicle("WB-02-AB-1234")

    assert vehicle is not None
    assert vehicle.registration_number == "WB02AB1234"
    assert vehicle.make == "Maruti Suzuki"
    assert vehicle.model == "Swift"


def test_unknown_vehicle_returns_none():
    vehicle = find_vehicle("XX99ZZ9999")

    assert vehicle is None


def test_aggregation_returns_all_provider_quotes():
    result = get_insurance_quotes(
        "WB02AB1234",
        date(2026, 11, 2),
    )

    assert result.vehicle.registration_number == "WB02AB1234"

    providers = {
        quote.provider
        for quote in result.all_quotes
    }

    assert providers == {
        "Provider A",
        "Provider B",
        "Provider C",
        "Provider D",
    }


def test_aggregation_returns_provider_c_plans():
    result = get_insurance_quotes(
        "WB02AB1234",
        date(2026, 11, 2),
    )

    provider_c_plans = {
        quote.plan_name
        for quote in result.all_quotes
        if quote.provider == "Provider C"
    }

    assert provider_c_plans == {
        "C-Standard",
        "C-Shield",
    }


def test_quotes_are_sorted_by_premium():
    result = get_insurance_quotes(
        "WB02AB1234",
        date(2026, 11, 2),
    )

    prices = [
        quote.total_premium
        for quote in result.valid_quotes
    ]

    assert prices == sorted(prices)


def test_cheapest_quote_is_selected():
    result = get_insurance_quotes(
        "WB02AB1234",
        date(2026, 11, 2),
    )

    assert result.cheapest_quote is not None

    assert (
        result.cheapest_quote.total_premium
        == result.valid_quotes[0].total_premium
    )


def test_expired_quotes_are_separated():
    result = get_insurance_quotes(
        "DL3CAB0042",
        date(2026, 11, 2),
    )

    assert any(
        quote.provider == "Provider D"
        and quote.plan_name == "Basic"
        for quote in result.expired_quotes
    )


def test_unknown_registration_is_rejected():
    with pytest.raises(ValueError):
        get_insurance_quotes(
            "XX99ZZ9999",
            date(2026, 11, 2),
        )


def test_empty_registration_is_rejected():
    with pytest.raises(ValueError):
        get_insurance_quotes("")
