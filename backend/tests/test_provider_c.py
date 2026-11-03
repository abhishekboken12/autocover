
from datetime import date
from decimal import Decimal

import pytest

from app.schemas.insurance import Vehicle
from app.providers.provider_c import (
    calculate_provider_c_quote,
    calculate_depreciation,
    get_od_age_band,
)


def create_vehicle():
    return Vehicle(
        registration_number="WB02AB1234",
        make="Maruti Suzuki",
        model="Swift",
        variant="VXi",
        engine_cc=1197,
        registration_date=date(2022, 8, 14),
        ex_showroom_price=Decimal("650000"),
        ncb_percent=Decimal("35"),
    )


def test_provider_c_standard_quote():
    quote = calculate_provider_c_quote(
        vehicle=create_vehicle(),
        quote_date=date(2026, 11, 9),
        plan_name="C-Standard",
    )

    assert quote.provider == "Provider C"
    assert quote.idv == Decimal("325000")
    assert quote.base_premium == Decimal("9965")
    assert quote.tax_amount == Decimal("1794")
    assert quote.total_premium == Decimal("11759")


def test_provider_c_shield_quote():
    quote = calculate_provider_c_quote(
        vehicle=create_vehicle(),
        quote_date=date(2026, 11, 9),
        plan_name="C-Shield",
    )

    assert quote.base_premium == Decimal("11897")
    assert quote.tax_amount == Decimal("2141")
    assert quote.total_premium == Decimal("14038")
    assert "NIL_DEPRECIATION" in quote.addons


@pytest.mark.parametrize(
    "quote_date, expected",
    [
        (date(2020, 7, 1), Decimal("0.05")),
        (date(2020, 7, 2), Decimal("0.15")),
        (date(2021, 1, 1), Decimal("0.15")),
        (date(2021, 1, 2), Decimal("0.20")),
        (date(2025, 1, 1), Decimal("0.50")),
        (date(2026, 1, 1), Decimal("0.55")),
        (date(2027, 1, 1), Decimal("0.60")),
        (date(2028, 1, 1), Decimal("0.65")),
    ],
)
def test_depreciation_boundaries(quote_date, expected):
    result = calculate_depreciation(
        registration_date=date(2020, 1, 1),
        quote_date=quote_date,
    )

    assert result == expected


def test_od_age_band_boundaries():
    registration_date = date(2020, 1, 1)

    assert get_od_age_band(
        registration_date, date(2022, 12, 31)
    ) == "0-3"

    assert get_od_age_band(
        registration_date, date(2023, 1, 1)
    ) == "3-5"

    assert get_od_age_band(
        registration_date, date(2025, 1, 1)
    ) == "5-8"


def test_vehicle_older_than_eight_years_is_rejected():
    with pytest.raises(ValueError):
        calculate_depreciation(
            registration_date=date(2020, 1, 1),
            quote_date=date(2028, 1, 2),
        )


def test_c_shield_rejects_vehicles_over_five_years():
    vehicle = create_vehicle()

    vehicle.registration_date = date(2020, 1, 1)

    with pytest.raises(ValueError, match="C-Shield"):
        calculate_provider_c_quote(
            vehicle=vehicle,
            quote_date=date(2026, 11, 9),
            plan_name="C-Shield",
        )
