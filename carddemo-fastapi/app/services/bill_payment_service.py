from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import Account, Transaction, CardXref


def process_bill_payment(db: Session, acct_id: int) -> dict:
    account = db.query(Account).filter(Account.acct_id == acct_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account: {acct_id} not found in Account file"
        )

    if account.curr_bal is None or account.curr_bal <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account balance is zero or negative. No payment needed."
        )

    xref = db.query(CardXref).filter(CardXref.acct_id == acct_id).first()
    if not xref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account: {acct_id} not found in cross reference file"
        )

    payment_amount = account.curr_bal
    tran_id = f"B{uuid.uuid4().hex[:15].upper()}"
    now_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")

    payment_tran = Transaction(
        tran_id=tran_id,
        type_cd="01",
        cat_cd=0,
        source="BILL-PAY",
        description=f"Bill payment for account {acct_id}",
        amount=-payment_amount,
        card_num=xref.card_num,
        orig_ts=now_ts,
        proc_ts=now_ts,
    )
    db.add(payment_tran)

    account.curr_bal = Decimal("0.00")
    db.commit()
    db.refresh(account)

    return {
        "message": f"Bill payment of {payment_amount} processed successfully",
        "acct_id": acct_id,
        "payment_amount": payment_amount,
        "new_balance": account.curr_bal,
        "tran_id": tran_id,
    }
