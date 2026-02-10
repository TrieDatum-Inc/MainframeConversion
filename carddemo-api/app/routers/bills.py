from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Account, User
from app.schemas import BillPayRequest, BillPayResponse

router = APIRouter(prefix="/bills", tags=["bills"])


@router.post("/pay", response_model=BillPayResponse)
def pay_bill(
    request: BillPayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(Account.id == request.acct_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    if account.active_status != "Y":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Account is not active"
        )
    if request.amount > account.curr_bal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount exceeds current balance",
        )
    account.curr_bal = account.curr_bal - request.amount
    account.curr_cyc_credit = account.curr_cyc_credit + request.amount
    db.commit()
    db.refresh(account)
    return BillPayResponse(
        status="success",
        acct_id=account.id,
        amount_paid=request.amount,
        new_balance=account.curr_bal,
    )
