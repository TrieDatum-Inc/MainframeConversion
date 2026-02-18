from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    TransactionResponse,
    TransactionAddRequest,
    PaginatedResponse,
)
from app.services.transaction_service import (
    list_transactions,
    get_transaction_detail,
    add_transaction,
)

router = APIRouter(prefix="/api/transactions", tags=["Transactions (COTRN00C, COTRN01C, COTRN02C)"])


@router.get("", response_model=PaginatedResponse)
def list_transactions_endpoint(
    acct_id: int = Query(None),
    card_num: str = Query(None),
    tran_type_cd: str = Query(None),
    tran_cat_cd: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = list_transactions(
        db,
        acct_id=acct_id,
        card_num=card_num,
        tran_type_cd=tran_type_cd,
        tran_cat_cd=tran_cat_cd,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[TransactionResponse.model_validate(t) for t in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
        has_more=result["has_more"],
    )


@router.get("/{tran_id}", response_model=TransactionResponse)
def view_transaction_detail(tran_id: str, db: Session = Depends(get_db)):
    transaction = get_transaction_detail(db, tran_id)
    return TransactionResponse.model_validate(transaction)


@router.post("", response_model=TransactionResponse, status_code=201)
def add_transaction_endpoint(
    request: TransactionAddRequest,
    db: Session = Depends(get_db),
):
    data = request.model_dump()
    transaction = add_transaction(db, data)
    return TransactionResponse.model_validate(transaction)
