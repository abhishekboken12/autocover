
import csv
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Optional, Set

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
    cleaned = value.strip().lower()

    if "lakh" in cleaned:
        amount = Decimal(cleaned.replace("lakh", "").strip())
        return amount * Decimal("100000")

    return Decimal(re.sub(r"[₹,\s]", "", cleaned))


def parse_validity(value: str):
    return datetime.strptime(value.strip(), "%d/%m/%Y").date()


def load_registry(registry_path: str) -> Set[str]:
    import json

    with open(registry_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    vehicles = data if isinstance(data, list) else data.get("vehicles", [])

    return {
        normalize_registration(vehicle["registration_number"])
        for vehicle in vehicles
    }


def parse_provider_d(
    data_path: str,
    registry_path: Optional[str] = None,
) -> ProviderQuoteBatch:

    path = Path(data_path)

    valid_registrations = (
        load_registry(registry_path)
        if registry_path
        else None
    )

    quotes: List[InsuranceQuote] = []
    seen = set()

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            registration = normalize_registration(row.get("reg_no", ""))

            if not registration:
                continue

            if (
                valid_registrations is not None
                and registration not in valid_registrations
            ):
                continue

            plan_name = row.get("plan", "Unknown").strip()

            total = parse_premium(row["premium_incl_gst"])

            base = money(total / (Decimal("1") + GST_RATE))
            tax = money(total - base)

            idv = parse_idv(row["idv"])

            addons = [
                addon.strip()
                for addon in row.get("addons", "").split("|")
                if addon.strip()
            ]

            valid_until = parse_validity(row["valid_till"])

            duplicate_key = (
                registration,
                plan_name.lower(),
                total,
                idv,
                tuple(sorted(addons)),
                valid_until,
            )

            if duplicate_key in seen:
                continue

            seen.add(duplicate_key)

            quote = InsuranceQuote(
                provider="Provider D",
                registration_number=registration,
                plan_name=plan_name,
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
        provider="Provider D",
        quotes=quotes,
        declined=[],
    )
