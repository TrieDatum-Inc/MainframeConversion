from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.utils.input_validations import validate_path_variable_acct_id
from app.database import get_db
from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    AccountDetailResponse,
    AccountUpdateRequest,
    AccountResponse,
    CustomerResponse,
)
from app.services.account_service import get_account_view, update_account

router = APIRouter(prefix="/api/accounts", tags=["Accounts (COACTVWC, COACTUPC)"])


@router.get("/{acct_id}", response_model=AccountDetailResponse)
def view_account(
        acct_id: str = Depends(validate_path_variable_acct_id),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    result = get_account_view(db, acct_id)
    return AccountDetailResponse(
        account=AccountResponse.model_validate(result["account"]),
        customer=CustomerResponse.model_validate(result["customer"]) if result["customer"] else None,
    )


@router.put("/{acct_id}", response_model=AccountDetailResponse)
def update_account_endpoint(
    request: AccountUpdateRequest,
    acct_id: str = Depends(validate_path_variable_acct_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_data = request.model_dump(exclude_unset=True)
    result = update_account(db, acct_id, update_data)
    return AccountDetailResponse(
        account=AccountResponse.model_validate(result["account"]),
        customer=CustomerResponse.model_validate(result["customer"]) if result["customer"] else None,
    )
