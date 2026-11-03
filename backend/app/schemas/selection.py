
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanSelectionCreate(BaseModel):
    registration_number: str
    provider: str
    plan_name: str
    coverage_type: str
    idv: Optional[Decimal] = None
    base_premium: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    total_premium: Decimal = Field(ge=0)


class PlanSelectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    registration_number: str
    provider: str
    plan_name: str
    coverage_type: str
    idv: Optional[Decimal]
    base_premium: Decimal
    tax_amount: Decimal
    total_premium: Decimal
    status: str
