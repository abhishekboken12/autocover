
from datetime import date
from decimal import Decimal

from app.schemas.insurance import Vehicle
from app.providers.provider_c import calculate_provider_c_quote


def test_provider_c_standard_quote():

    vehicle = Vehicle(
        registration_number="WB02AB1234",
        make="Maruti Suzuki",
        model="Swift",
        variant="VXi",
        engine_cc=1197,
        registration_date=date(2022, 8, 14),
        ex_showroom_price=Decimal("650000"),
        ncb_percent=Decimal("35"),
    )

    quote = calculate_provider_c_quote(
        vehicle=vehicle,
        quote_date=date(2026, 11, 9),
        plan_name="C-Standard",
    )

    assert quote.provider == "Provider C"
    assert quote.idv == Decimal("325000")
    assert quote.total_premium > quote.base_premium
