
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PlanSelection(Base):
    __tablename__ = "plan_selections"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    registration_number = Column(String(20), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    plan_name = Column(String(150), nullable=False)

    coverage_type = Column(String(50), nullable=False)
    idv = Column(Numeric(12, 2), nullable=True)
    base_premium = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=False)
    total_premium = Column(Numeric(12, 2), nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="SELECTED",
    )

    selected_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
