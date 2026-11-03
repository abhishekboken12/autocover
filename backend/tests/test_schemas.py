
from app.schemas.insurance import (
    InsuranceQuote,
    CoverageType,
    PremiumBasis,
)


def test_registration_normalization():
    quote = InsuranceQuote(
        provider="Provider B",
        registration_number="WB-02-AB-1234",
        plan_name="Smart Shield",
        coverage_type=CoverageType.COMPREHENSIVE,
        total_premium=12830,
        premium_basis=PremiumBasis.TAX_INCLUSIVE,
    )

    assert quote.registration_number == "WB02AB1234"
    assert quote.total_premium == 12830


def test_missing_tax_is_allowed():
    quote = InsuranceQuote(
        provider="Provider A",
        registration_number="MH12EF4321",
        plan_name="Essential",
        base_premium=19459,
        premium_basis=PremiumBasis.PRE_TAX,
    )

    assert quote.tax_amount is None
    assert quote.total_premium is None
