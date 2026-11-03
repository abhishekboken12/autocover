
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup

from app.schemas.insurance import (
    InsuranceQuote,
    ProviderQuoteBatch,
    PremiumBasis,
    CoverageType,
    normalize_registration,
)


GST_RATE = Decimal("0.18")


def money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def parse_premium(value: str) -> Decimal:
    cleaned = re.sub(r"[₹,\s]", "", value)
    return Decimal(cleaned)


def parse_idv(value: str) -> Decimal:
    """
    Convert values such as '3.1 L' into rupees.
    """
    cleaned = value.strip().upper()

    if cleaned.endswith("L"):
        lakh_value = Decimal(cleaned[:-1].strip())
        return lakh_value * Decimal("100000")

    return Decimal(re.sub(r"[₹,\s]", "", cleaned))


def extract_quote_data(html: str) -> dict:
    match = re.search(
        r"window\.__QUOTE_DATA__\s*=\s*(\{.*?\})\s*;",
        html,
        re.DOTALL,
    )

    if not match:
        raise ValueError("Provider B quote data not found")

    return json.loads(match.group(1))


def parse_provider_b(data_path: str) -> ProviderQuoteBatch:
    path = Path(data_path)
    html = path.read_text(encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")

    javascript_quotes = extract_quote_data(html)

    quotes: List[InsuranceQuote] = []
    seen = set()

    for vehicle_section in soup.select("section.vehicle"):
        registration = normalize_registration(
            vehicle_section.get("data-reg", "")
        )

        if not registration:
            continue

        for card in vehicle_section.select(".plan-card"):
            plan_id = card.get("data-plan-id")

            if not plan_id or plan_id not in javascript_quotes:
                continue

            if plan_id in seen:
                continue

            seen.add(plan_id)

            price_data = javascript_quotes[plan_id]

            total = parse_premium(price_data["total"])

            # Provider B prices already include 18% GST.
            base = money(
                total / (Decimal("1") + GST_RATE)
            )
            tax = money(total - base)

            idv = parse_idv(price_data["cover"])

            heading = card.select_one("h3")
            plan_name = (
                heading.get_text(strip=True)
                if heading
                else "Unknown"
            )

            addon_elements = card.select(".addons li")
            addons = [
                element.get_text(strip=True)
                for element in addon_elements
            ]

            valid_until = price_data.get("valid_till")

            quote = InsuranceQuote(
                provider="Provider B",
                registration_number=registration,
                plan_name=plan_name,
                source_quote_id=plan_id,
                coverage_type=CoverageType.UNKNOWN,
                idv=idv,
                base_premium=base,
                tax_amount=tax,
                total_premium=total,
                premium_basis=PremiumBasis.TAX_INCLUSIVE,
                addons=addons,
                valid_until=valid_until,
            )

            quotes.append(quote)

    return ProviderQuoteBatch(
        provider="Provider B",
        quotes=quotes,
        declined=[],
    )
