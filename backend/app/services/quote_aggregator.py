
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.insurance import (
    Vehicle,
    InsuranceQuote,
    QuoteDecline,
    normalize_registration,
)

from app.providers.provider_a import parse_provider_a
from app.providers.provider_b import parse_provider_b
from app.providers.provider_c import calculate_provider_c_quote
from app.providers.provider_d import parse_provider_d


# Resolve data paths relative to the backend directory.
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"

REGISTRY_PATH = DATA_DIR / "registry.json"
PROVIDER_A_PATH = DATA_DIR / "provider_a.json"
PROVIDER_B_PATH = DATA_DIR / "provider_b.html"
PROVIDER_D_PATH = DATA_DIR / "provider_d.csv"


class QuoteAggregationResult(BaseModel):
    vehicle: Vehicle
    quote_date: date

    all_quotes: List[InsuranceQuote] = Field(default_factory=list)
    valid_quotes: List[InsuranceQuote] = Field(default_factory=list)
    expired_quotes: List[InsuranceQuote] = Field(default_factory=list)

    declined: List[QuoteDecline] = Field(default_factory=list)
    provider_errors: List[Dict[str, str]] = Field(default_factory=list)

    cheapest_quote: Optional[InsuranceQuote] = None


def find_vehicle(registration_number: str) -> Optional[Vehicle]:
    registration = normalize_registration(registration_number)

    if not registration:
        raise ValueError("Registration number is required")

    with REGISTRY_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    for record in data.get("vehicles", []):
        if normalize_registration(
            record.get("registration_number", "")
        ) == registration:
            return Vehicle(**record)

    return None


def get_insurance_quotes(
    registration_number: str,
    quote_date: Optional[date] = None,
) -> QuoteAggregationResult:

    requested_registration = normalize_registration(
        registration_number
    )

    if not requested_registration:
        raise ValueError("Registration number is required")

    effective_date = quote_date or date.today()

    vehicle = find_vehicle(requested_registration)

    if vehicle is None:
        raise ValueError(
            "Vehicle registration not found in the supplied registry"
        )

    all_quotes: List[InsuranceQuote] = []
    declined: List[QuoteDecline] = []
    provider_errors: List[Dict[str, str]] = []

    # ---------------------------------------------
    # Providers A, B and D: Parse supplied datasets
    # ---------------------------------------------

    providers = [
        (
            "Provider A",
            lambda: parse_provider_a(str(PROVIDER_A_PATH)),
        ),
        (
            "Provider B",
            lambda: parse_provider_b(str(PROVIDER_B_PATH)),
        ),
        (
            "Provider D",
            lambda: parse_provider_d(
                str(PROVIDER_D_PATH),
                str(REGISTRY_PATH),
            ),
        ),
    ]

    for provider_name, parser in providers:
        try:
            batch = parser()

            matching_quotes = [
                quote
                for quote in batch.quotes
                if quote.registration_number == requested_registration
            ]

            matching_declines = [
                item
                for item in batch.declined
                if item.registration_number == requested_registration
            ]

            all_quotes.extend(matching_quotes)
            declined.extend(matching_declines)

        except Exception as exc:
            provider_errors.append({
                "provider": provider_name,
                "reason": str(exc),
            })

    # ---------------------------------------------
    # Provider C: Calculate quotes dynamically
    # ---------------------------------------------

    for plan_name in ("C-Standard", "C-Shield"):
        try:
            quote = calculate_provider_c_quote(
                vehicle=vehicle,
                quote_date=effective_date,
                plan_name=plan_name,
            )

            all_quotes.append(quote)

        except Exception as exc:
            provider_errors.append({
                "provider": "Provider C",
                "plan": plan_name,
                "reason": str(exc),
            })

    # ---------------------------------------------
    # Sort all collected quotes
    # ---------------------------------------------

    all_quotes.sort(
        key=lambda quote: (
            quote.total_premium
            if quote.total_premium is not None
            else Decimal("Infinity")
        )
    )

    # ---------------------------------------------
    # Separate expired and valid quotes
    # ---------------------------------------------

    valid_quotes = [
        quote
        for quote in all_quotes
        if quote.valid_until is None
        or quote.valid_until >= effective_date
    ]

    expired_quotes = [
        quote
        for quote in all_quotes
        if quote.valid_until is not None
        and quote.valid_until < effective_date
    ]

    cheapest_quote = (
        valid_quotes[0]
        if valid_quotes
        else None
    )

    return QuoteAggregationResult(
        vehicle=vehicle,
        quote_date=effective_date,
        all_quotes=all_quotes,
        valid_quotes=valid_quotes,
        expired_quotes=expired_quotes,
        declined=declined,
        provider_errors=provider_errors,
        cheapest_quote=cheapest_quote,
    )
