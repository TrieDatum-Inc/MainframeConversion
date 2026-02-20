from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.utils.input_validations import validate_path_variable_acct_id, validate_path_variable_card_num, validate_optional_acct_id, validate_optional_card_num
from app.database import get_db
from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    CardResponse,
    CardDetailResponse,
    CardUpdateRequest,
    AccountResponse,
    CustomerResponse,
    PaginatedResponse,
)
from app.services.card_service import list_cards, get_card_detail, update_card

router = APIRouter(prefix="/api/cards", tags=["Cards (COCRDLIC, COCRDSLC, COCRDUPC)"])


@router.get("", response_model=PaginatedResponse)
def list_cards_endpoint(
    acct_id: str | None = Depends(validate_optional_acct_id),
    card_num: str | None = Depends(validate_optional_card_num),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = list_cards(db, acct_id=acct_id, card_num=card_num, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[CardResponse.model_validate(c) for c in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
        has_more=result["has_more"],
    )


@router.get("/{card_num}/{acct_id}", response_model=CardDetailResponse)
def view_card_detail(
    card_num: str = Depends(validate_path_variable_card_num),
    acct_id: str = Depends(validate_path_variable_acct_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_card_detail(db, acct_id, card_num)
    return CardDetailResponse(
        card=CardResponse.model_validate(result["card"]),
        account=AccountResponse.model_validate(result["account"]) if result["account"] else None,
        customer=CustomerResponse.model_validate(result["customer"]) if result["customer"] else None,
    )


@router.put("/{card_num}/{acct_id}", response_model=CardDetailResponse)
def update_card_endpoint(
    request: CardUpdateRequest,
    card_num: str = Depends(validate_path_variable_card_num),
    acct_id: str = Depends(validate_path_variable_acct_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_data = request.model_dump(exclude_unset=True)
    result = update_card(db, acct_id, card_num, update_data)
    return CardDetailResponse(
        card=CardResponse.model_validate(result["card"]),
        account=AccountResponse.model_validate(result["account"]) if result["account"] else None,
        customer=CustomerResponse.model_validate(result["customer"]) if result["customer"] else None,
    )
