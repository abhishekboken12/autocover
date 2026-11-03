
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from calendar import monthrange

from app.schemas.insurance import (
    Vehicle,
    InsuranceQuote,
    CoverageType,
    PremiumBasis,
)


# --------------------------------------------------
# Provider C rate-card configuration
# --------------------------------------------------

EFFECTIVE_FROM = date(2026, 10, 1)
RATE_VALID_UNTIL = date(2026, 12, 31)

GST_RATE = Decimal("0.18")

MODEL_GROUPS = {
    "SWIFT": 1,
    "I20": 1,
    "BALENO": 1,
    "ALTO K10": 1,
    "TIAGO": 1,
    "NEXON": 2,
    "CITY": 2,
    "SONET": 2,
    "CRETA": 3,
    "XUV700": 3,
    "INNOVA CRYSTA": 3,
}

OD_RATES = {
    1: {
        "0-3": Decimal("0.028"),
        "3-5": Decimal("0.031"),
        "5-8": Decimal("0.036"),
    },
    2: {
        "0-3": Decimal("0.030"),
        "3-5": Decimal("0.034"),
        "5-8": Decimal("0.039"),
    },
    3: {
        "0-3": Decimal("0.032"),
        "3-5": Decimal("0.036"),
        "5-8": Decimal("0.041"),
    },
}

TP_RATES = [
    (1000, Decimal("2094")),
    (1500, Decimal("3416")),
    (float("inf"), Decimal("7897")),
]


# --------------------------------------------------
# Rounding utilities
# --------------------------------------------------

def round_rupee(value: Decimal) -> Decimal:
    """Round an amount to the nearest rupee, halves up."""
    return value.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )


def round_idv(value: Decimal) -> Decimal:
    """Round IDV to the nearest 1,000, halves up."""
    thousands = (value / Decimal("1000")).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )

    return thousands * Decimal("1000")


# --------------------------------------------------
# Calendar-based age utilities
# --------------------------------------------------

def add_months(original_date: date, months: int) -> date:
    """
    Add calendar months while preserving a valid day.

    Example:
    31 January + 1 month = 28 February
    """
    month_index = original_date.month - 1 + months

    year = original_date.year + month_index // 12
    month = month_index % 12 + 1

    day = min(
        original_date.day,
        monthrange(year, month)[1],
    )

    return date(year, month, day)


def calculate_depreciation(
    registration_date: date,
    quote_date: date,
) -> Decimal:
    """
    Calculate IDV depreciation using the PDF schedule.

    Assumption:
    Exactly 6 months belongs to the first
    'not exceeding 6 months' bracket.

    Above 5 years, depreciation increases by
    5 percentage points for each completed year.
    """

    if quote_date < registration_date:
        raise ValueError("Quote date cannot precede registration date")

    if quote_date > add_months(registration_date, 96):
        raise ValueError("Vehicles older than 8 years are not covered")

    if quote_date <= add_months(registration_date, 6):
        return Decimal("0.05")

    if quote_date <= add_months(registration_date, 12):
        return Decimal("0.15")

    if quote_date <= add_months(registration_date, 24):
        return Decimal("0.20")

    if quote_date <= add_months(registration_date, 36):
        return Decimal("0.30")

    if quote_date <= add_months(registration_date, 48):
        return Decimal("0.40")

    if quote_date <= add_months(registration_date, 60):
        return Decimal("0.50")

    completed_years_above_five = 0

    for year in range(6, 9):
        if quote_date >= add_months(registration_date, year * 12):
            completed_years_above_five += 1

    return (
        Decimal("0.50")
        + Decimal("0.05") * completed_years_above_five
    )


def get_od_age_band(
    registration_date: date,
    quote_date: date,
) -> str:
    """Select the OD rate-card age band."""

    if quote_date < add_months(registration_date, 36):
        return "0-3"

    if quote_date < add_months(registration_date, 60):
        return "3-5"

    if quote_date <= add_months(registration_date, 96):
        return "5-8"

    raise ValueError("Vehicles older than 8 years are not covered")


# --------------------------------------------------
# Rate-card lookup utilities
# --------------------------------------------------

def get_model_group(model: str) -> int:
    normalized = model.upper().strip()

    for model_name, group in MODEL_GROUPS.items():
        if model_name in normalized:
            return group

    raise ValueError(
        f"Model not listed in Provider C rate card: {model}"
    )


def get_od_rate(group: int, age_band: str) -> Decimal:
    return OD_RATES[group][age_band]


def get_tp_premium(engine_cc: int) -> Decimal:
    for maximum_cc, premium in TP_RATES:
        if engine_cc <= maximum_cc:
            return premium

    raise ValueError("Unsupported engine capacity")


# --------------------------------------------------
# Main quote calculator
# --------------------------------------------------

def calculate_provider_c_quote(
    vehicle: Vehicle,
    quote_date: date,
    plan_name: str,
) -> InsuranceQuote:

    # Validate required vehicle information.
    if not vehicle.registration_date:
        raise ValueError("Registration date is required")

    if vehicle.ex_showroom_price is None:
        raise ValueError("Ex-showroom price is required")

    if vehicle.engine_cc is None:
        raise ValueError("Engine capacity is required")

    # Validate rate-card effective period.
    if not EFFECTIVE_FROM <= quote_date <= RATE_VALID_UNTIL:
        raise ValueError("Quote date is outside the rate-card validity period")

    registration_date = vehicle.registration_date

    # Validate vehicle age.
    if quote_date < registration_date:
        raise ValueError("Quote date cannot precede registration date")

    if quote_date > add_months(registration_date, 96):
        raise ValueError("Vehicle is older than 8 years")

    # Validate plan eligibility.
    if plan_name not in ("C-Standard", "C-Shield"):
        raise ValueError(f"Unsupported plan: {plan_name}")

    if (
        plan_name == "C-Shield"
        and quote_date > add_months(registration_date, 60)
    ):
        raise ValueError("C-Shield is available only up to 5 years")

    # 1. Calculate IDV.
    depreciation = calculate_depreciation(
        registration_date,
        quote_date,
    )

    idv = round_idv(
        vehicle.ex_showroom_price
        * (Decimal("1") - depreciation)
    )

    # 2. Calculate Own Damage premium.
    group = get_model_group(vehicle.model)

    age_band = get_od_age_band(
        registration_date,
        quote_date,
    )

    od_rate = get_od_rate(group, age_band)

    od_before_ncb = round_rupee(idv * od_rate)

    # 3. Apply NCB discount only to OD premium.
    ncb_percent = vehicle.ncb_percent or Decimal("0")

    ncb_discount = round_rupee(
        od_before_ncb * ncb_percent / Decimal("100")
    )

    od_after_ncb = od_before_ncb - ncb_discount

    # 4. Calculate Third Party premium.
    tp_premium = get_tp_premium(vehicle.engine_cc)

    # 5. Calculate plan add-ons.
    addons = []

    nil_depreciation = Decimal("0")
    roadside_assistance = Decimal("0")
    consumables = Decimal("0")

    if plan_name == "C-Shield":

        nil_depreciation = round_rupee(
            od_after_ncb * Decimal("0.15")
        )

        roadside_assistance = Decimal("350")
        consumables = Decimal("600")

        addons = [
            "NIL_DEPRECIATION",
            "ROAD_SIDE_ASSISTANCE",
            "CONSUMABLES",
        ]

    # 6. Calculate pre-tax premium.
    pre_tax_total = round_rupee(
        od_after_ncb
        + tp_premium
        + nil_depreciation
        + roadside_assistance
        + consumables
    )

    # 7. Calculate GST.
    gst = round_rupee(pre_tax_total * GST_RATE)

    # 8. Calculate final payable premium.
    total_premium = pre_tax_total + gst

    # 9. Return normalized quote.
    return InsuranceQuote(
        provider="Provider C",
        source_quote_id=plan_name,
        registration_number=vehicle.registration_number,
        plan_name=plan_name,
        coverage_type=CoverageType.COMPREHENSIVE,
        idv=idv,
        base_premium=pre_tax_total,
        tax_amount=gst,
        total_premium=total_premium,
        premium_basis=PremiumBasis.PRE_TAX,
        addons=addons,
        valid_until=RATE_VALID_UNTIL,
    )
