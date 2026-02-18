from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    AccountDetailResponse,
    AccountUpdateRequest,
    AccountResponse,
    CustomerResponse,
)
from app.services.account_service import get_account_view, update_account

router = APIRouter(prefix="/api/accounts", tags=["Accounts (COACTVWC, COACTUPC)"])


@router.get("/{acct_id}", response_model=AccountDetailResponse)
def view_account(acct_id: int, db: Session = Depends(get_db)):
    result = get_account_view(db, acct_id)
    return AccountDetailResponse(
        account=AccountResponse.model_validate(result["account"]),
        customer=CustomerResponse.model_validate(result["customer"]) if result["customer"] else None,
    )


@router.put("/{acct_id}", response_model=AccountDetailResponse)
def update_account_endpoint(
    acct_id: int,
    request: AccountUpdateRequest,
    db: Session = Depends(get_db),
):
    update_data = request.model_dump(exclude_unset=True)
    result = update_account(db, acct_id, update_data)
    return AccountDetailResponse(
        account=AccountResponse.model_validate(result["account"]),
        customer=CustomerResponse.model_validate(result["customer"]) if result["customer"] else None,
    )
