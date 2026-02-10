from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Account, Card, CardXref, Customer, User
from app.schemas import (
    AccountCreate,
    AccountDetailResponse,
    AccountResponse,
    AccountUpdate,
    CardResponse,
    CustomerResponse,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    active_status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Account)
    if active_status:
        query = query.filter(Account.active_status == active_status)
    query = query.order_by(Account.id)
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size).all()


@router.get("/{acct_id}", response_model=AccountDetailResponse)
def get_account(
    acct_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(Account.id == acct_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    xref = db.query(CardXref).filter(CardXref.acct_id == acct_id).first()
    customer = None
    if xref:
        customer = db.query(Customer).filter(Customer.id == xref.cust_id).first()
    cards = db.query(Card).filter(Card.acct_id == acct_id).all()
    result = AccountDetailResponse.model_validate(account)
    if customer:
        result.customer = CustomerResponse.model_validate(customer)
    result.cards = [CardResponse.model_validate(c) for c in cards]
    return result


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_in: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Account).filter(Account.id == account_in.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    account = Account(**account_in.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.put("/{acct_id}", response_model=AccountResponse)
def update_account(
    acct_id: int,
    account_in: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(Account.id == acct_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    update_data = account_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account
