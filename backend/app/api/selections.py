
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.selection import (
    PlanSelectionCreate,
    PlanSelectionResponse,
)
from app.services.selection_service import (
    create_selection,
    get_selection,
)

router = APIRouter(prefix="/api/selections", tags=["Plan Selections"])


@router.post(
    "",
    response_model=PlanSelectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_selection(
    selection_data: PlanSelectionCreate,
    db: Session = Depends(get_db),
):
    return create_selection(db, selection_data)


@router.get(
    "/{selection_id}",
    response_model=PlanSelectionResponse,
)
def retrieve_selection(
    selection_id: UUID,
    db: Session = Depends(get_db),
):
    selection = get_selection(db, selection_id)

    if not selection:
        raise HTTPException(
            status_code=404,
            detail="Selection not found",
        )

    return selection
