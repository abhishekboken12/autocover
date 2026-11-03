
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import re

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------
# Utility functions
# --------------------------------------------------

def normalize_registration(value: str) -> str:
    """Normalize vehicle registration numbers."""
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()


def parse_date(value):
    """Parse supported date formats from provider datasets."""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    value = str(value).strip()

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value[:10], fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        raise ValueError(f"Unsupported date format: {value}")


# --------------------------------------------------
# Enums
# --------------------------------------------------

class CoverageType(str, Enum):
    COMPREHENSIVE = "COMPREHENSIVE"
    THIRD_PARTY = "THIRD_PARTY"
    OWN_DAMAGE = "OWN_DAMAGE"
    UNKNOWN = "UNKNOWN"


class PremiumBasis(str, Enum):
    PRE_TAX = "PRE_TAX"
    TAX_INCLUSIVE = "TAX_INCLUSIVE"
    UNKNOWN = "UNKNOWN"


# --------------------------------------------------
# Vehicle model
# --------------------------------------------------

class Vehicle(BaseModel):
    registration_number: str
    make: str
    model: str

    variant: Optional[str] = None
    fuel_type: Optional[str] = None
    engine_cc: Optional[int] = Field(default=None, gt=0)
    registration_date: Optional[date] = None
    rto: Optional[str] = None

    ex_showroom_price: Optional[Decimal] = Field(
        default=None, ge=0
    )

    current_policy_expiry: Optional[date] = None

    claims_last_year: Optional[int] = Field(
        default=None, ge=0
    )

    ncb_percent: Optional[Decimal] = Field(
        default=None, ge=0, le=100
    )

    @field_validator("registration_number")
    @classmethod
    def clean_registration(cls, value):
        return normalize_registration(value)

    @field_validator(
        "registration_date",
        "current_policy_expiry",
        mode="before"
    )
    @classmethod
    def clean_dates(cls, value):
        return parse_date(value)


# --------------------------------------------------
# Insurance quote model
# --------------------------------------------------

class InsuranceQuote(BaseModel):
    provider: str
    registration_number: str
    plan_name: str

    source_quote_id: Optional[str] = None

    coverage_type: CoverageType = CoverageType.UNKNOWN

    idv: Optional[Decimal] = Field(
        default=None, ge=0
    )

    base_premium: Optional[Decimal] = Field(
        default=None, ge=0
    )

    tax_amount: Optional[Decimal] = Field(
        default=None, ge=0
    )

    total_premium: Optional[Decimal] = Field(
        default=None, ge=0
    )

    premium_basis: PremiumBasis = PremiumBasis.UNKNOWN

    addons: List[str] = Field(default_factory=list)

    valid_until: Optional[date] = None

    @field_validator("registration_number")
    @classmethod
    def clean_registration(cls, value):
        return normalize_registration(value)

    @field_validator("valid_until", mode="before")
    @classmethod
    def clean_validity_date(cls, value):
        return parse_date(value)


# --------------------------------------------------
# Declined quote model
# --------------------------------------------------

class QuoteDecline(BaseModel):
    provider: str
    registration_number: str
    reason: str

    @field_validator("registration_number")
    @classmethod
    def clean_registration(cls, value):
        return normalize_registration(value)


# --------------------------------------------------
# Provider response model
# --------------------------------------------------

class ProviderQuoteBatch(BaseModel):
    provider: str

    quotes: List[InsuranceQuote] = Field(
        default_factory=list
    )

    declined: List[QuoteDecline] = Field(
        default_factory=list
    )
