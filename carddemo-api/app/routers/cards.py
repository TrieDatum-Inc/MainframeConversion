from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Card, CardXref, User
from app.schemas import (
    CardCreate,
    CardResponse,
    CardUpdate,
    CardXrefBase,
    CardXrefResponse,
)

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=list[CardResponse])
def list_cards(
    acct_id: int | None = None,
    active_status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Card)
    if acct_id is not None:
        query = query.filter(Card.acct_id == acct_id)
    if active_status:
        query = query.filter(Card.active_status == active_status)
    query = query.order_by(Card.card_num)
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size).all()


@router.get("/search", response_model=list[CardResponse])
def search_cards(
    card_num: str | None = None,
    acct_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Card)
    if card_num:
        query = query.filter(Card.card_num.like(f"%{card_num}%"))
    if acct_id is not None:
        query = query.filter(Card.acct_id == acct_id)
    return query.order_by(Card.card_num).limit(50).all()


@router.get("/{card_num}", response_model=CardResponse)
def get_card(
    card_num: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = db.query(Card).filter(Card.card_num == card_num).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )
    return card


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    card_in: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Card).filter(Card.card_num == card_in.card_num).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Card already exists"
        )
    card = Card(**card_in.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.put("/{card_num}", response_model=CardResponse)
def update_card(
    card_num: str,
    card_in: CardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = db.query(Card).filter(Card.card_num == card_num).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )
    update_data = card_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)
    db.commit()
    db.refresh(card)
    return card


@router.get("/xrefs/list", response_model=list[CardXrefResponse])
def list_xrefs(
    acct_id: int | None = None,
    cust_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CardXref)
    if acct_id is not None:
        query = query.filter(CardXref.acct_id == acct_id)
    if cust_id is not None:
        query = query.filter(CardXref.cust_id == cust_id)
    return query.all()


@router.post(
    "/xrefs", response_model=CardXrefResponse, status_code=status.HTTP_201_CREATED
)
def create_xref(
    xref_in: CardXrefBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(CardXref).filter(CardXref.card_num == xref_in.card_num).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Xref already exists"
        )
    xref = CardXref(**xref_in.model_dump())
    db.add(xref)
    db.commit()
    db.refresh(xref)
    return xref
