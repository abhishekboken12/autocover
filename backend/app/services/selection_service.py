
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.plan_selection import PlanSelection
from app.schemas.selection import PlanSelectionCreate


def create_selection(
    db: Session,
    selection_data: PlanSelectionCreate,
) -> PlanSelection:

    selection = PlanSelection(
        registration_number=selection_data.registration_number,
        provider=selection_data.provider,
        plan_name=selection_data.plan_name,
        coverage_type=selection_data.coverage_type,
        idv=selection_data.idv,
        base_premium=selection_data.base_premium,
        tax_amount=selection_data.tax_amount,
        total_premium=selection_data.total_premium,
        status="SELECTED",
    )

    db.add(selection)
    db.commit()
    db.refresh(selection)

    return selection


def get_selection(
    db: Session,
    selection_id: UUID,
):
    return db.query(PlanSelection).filter(
        PlanSelection.id == selection_id
    ).first()
