
import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from app.schemas.insurance import (
    InsuranceQuote,
    QuoteDecline,
    ProviderQuoteBatch,
    CoverageType,
    PremiumBasis,
    normalize_registration,
)


GST_RATE = Decimal("0.18")


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_provider_a(data_path: str) -> ProviderQuoteBatch:
    path = Path(data_path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    quotes: List[InsuranceQuote] = []
    declined: List[QuoteDecline] = []
    seen = set()

    for item in data.get("quotes", []):
        registration = normalize_registration(
            item.get("registration", "")
        )

        if not registration:
            continue

        status = str(item.get("status", "QUOTED")).upper()

        if status == "DECLINED":
            declined.append(
                QuoteDecline(
                    provider="Provider A",
                    registration_number=registration,
                    reason=item.get("reason", "Quote declined"),
                )
            )
            continue

        if status != "QUOTED":
            continue

        if item.get("base_premium") is not None:
            base = Decimal(str(item["base_premium"]))

            taxes = item.get("taxes") or []
            tax = sum(
                (
                    base * Decimal(str(t.get("rate", 0)))
                    for t in taxes
                    if t.get("name", "").upper() == "GST"
                ),
                Decimal("0"),
            )

            tax = money(tax)
            total = money(base + tax)
            premium_basis = PremiumBasis.PRE_TAX

        elif item.get("premium") is not None:
            total = Decimal(str(item["premium"]))

            if item.get("premium_includes_gst") is True:
                base = money(total / (Decimal("1") + GST_RATE))
                tax = money(total - base)
                premium_basis = PremiumBasis.TAX_INCLUSIVE
            else:
                base = total
                tax = Decimal("0")
                premium_basis = PremiumBasis.UNKNOWN

        else:
            continue

        plan_name = str(item.get("plan", "Unknown")).strip()

        duplicate_key = (
            registration,
            plan_name.lower(),
            total,
        )

        if duplicate_key in seen:
            continue

        seen.add(duplicate_key)

        coverage_value = str(item.get("coverage", "")).upper()

        if "COMPREHENSIVE" in coverage_value:
            coverage = CoverageType.COMPREHENSIVE
        elif "THIRD" in coverage_value:
            coverage = CoverageType.THIRD_PARTY
        elif "OWN" in coverage_value:
            coverage = CoverageType.OWN_DAMAGE
        else:
            coverage = CoverageType.UNKNOWN

        quote = InsuranceQuote(
            provider="Provider A",
            registration_number=registration,
            plan_name=plan_name,
            coverage_type=coverage,
            idv=item.get("idv"),
            base_premium=float(base),
            tax_amount=float(tax),
            total_premium=float(total),
            premium_basis=premium_basis,
            addons=item.get("addons") or [],
            valid_until=item.get("valid_until"),
        )

        quotes.append(quote)

    return ProviderQuoteBatch(
        provider="Provider A",
        quotes=quotes,
        declined=declined,
    )
