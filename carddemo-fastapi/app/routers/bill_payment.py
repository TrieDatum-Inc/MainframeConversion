from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import BillPaymentRequest, BillPaymentResponse
from app.services.bill_payment_service import process_bill_payment

router = APIRouter(prefix="/api/bill-payments", tags=["Bill Payment (COBIL00C)"])


@router.post("", response_model=BillPaymentResponse)
def pay_bill(request: BillPaymentRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return process_bill_payment(db, request.acct_id)
