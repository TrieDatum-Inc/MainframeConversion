from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    TranCatBalance,
    Transaction,
    TransactionCategory,
    TransactionType,
    User,
)
from app.schemas import (
    TranCatBalanceResponse,
    TransactionCategoryResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionTypeResponse,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    card_num: str | None = None,
    type_cd: str | None = None,
    cat_cd: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction)
    if card_num:
        query = query.filter(Transaction.card_num == card_num)
    if type_cd:
        query = query.filter(Transaction.type_cd == type_cd)
    if cat_cd is not None:
        query = query.filter(Transaction.cat_cd == cat_cd)
    if start_date:
        query = query.filter(Transaction.orig_ts >= start_date)
    if end_date:
        query = query.filter(Transaction.orig_ts <= end_date)
    query = query.order_by(Transaction.orig_ts.desc())
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size).all()


@router.get("/search", response_model=list[TransactionResponse])
def search_transactions(
    card_num: str | None = None,
    acct_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction)
    if card_num:
        query = query.filter(Transaction.card_num == card_num)
    if acct_id is not None:
        from app.models import CardXref

        xrefs = db.query(CardXref.card_num).filter(CardXref.acct_id == acct_id).all()
        card_nums = [x.card_num for x in xrefs]
        if card_nums:
            query = query.filter(Transaction.card_num.in_(card_nums))
        else:
            return []
    if start_date:
        query = query.filter(Transaction.orig_ts >= start_date)
    if end_date:
        query = query.filter(Transaction.orig_ts <= end_date)
    return query.order_by(Transaction.orig_ts.desc()).limit(100).all()


@router.get("/{tran_id}", response_model=TransactionResponse)
def get_transaction(
    tran_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = db.query(Transaction).filter(Transaction.id == tran_id).first()
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    return txn


@router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
def create_transaction(
    txn_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Transaction).filter(Transaction.id == txn_in.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Transaction already exists"
        )
    txn = Transaction(**txn_in.model_dump())
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.get("/types/list", response_model=list[TransactionTypeResponse])
def list_transaction_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(TransactionType).order_by(TransactionType.type_cd).all()


@router.get("/categories/list", response_model=list[TransactionCategoryResponse])
def list_transaction_categories(
    type_cd: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(TransactionCategory)
    if type_cd:
        query = query.filter(TransactionCategory.type_cd == type_cd)
    return query.order_by(
        TransactionCategory.type_cd, TransactionCategory.cat_cd
    ).all()


@router.get(
    "/balances/by-account/{acct_id}",
    response_model=list[TranCatBalanceResponse],
)
def get_category_balances(
    acct_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(TranCatBalance)
        .filter(TranCatBalance.acct_id == acct_id)
        .order_by(TranCatBalance.type_cd, TranCatBalance.cat_cd)
        .all()
    )
