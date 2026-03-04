from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.models import Card, Account, Customer, CardXref


def list_cards(
    db: Session,
    acct_id: int = None,
    card_num: str = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    query = db.query(Card)

    if acct_id:
        query = query.filter(Card.acct_id == acct_id)
    if card_num:
        query = query.filter(Card.card_num.like(f"%{card_num}%"))

    total = query.count()
    offset = (page - 1) * page_size
    cards = query.order_by(Card.card_num).offset(offset).limit(page_size + 1).all()

    has_more = len(cards) > page_size
    if has_more:
        cards = cards[:page_size]

    return {
        "items": cards,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": has_more,
    }


def get_card_detail(db: Session, acct_id: int, card_num: str) -> dict:
    card = db.query(Card).filter(
        Card.card_num == card_num,
        Card.acct_id == acct_id,
    ).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card: {card_num} Acct: {acct_id} combination not found in Card file"
        )

    account = db.query(Account).filter(Account.acct_id == acct_id).first()

    xref = db.query(CardXref).filter(CardXref.card_num == card_num).first()
    customer = None
    if xref:
        customer = db.query(Customer).filter(Customer.cust_id == xref.cust_id).first()

    return {"card": card, "account": account, "customer": customer}


def update_card(db: Session, acct_id: int, card_num: str, update_data: dict) -> dict:
    card = db.query(Card).filter(
        Card.card_num == card_num,
        Card.acct_id == acct_id,
    ).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card: {card_num} Acct: {acct_id} combination not found in Card file"
        )

    updatable_fields = ["embossed_name", "active_status", "expiration_date"]
    modified = False
    for field in updatable_fields:
        if field in update_data and update_data[field] is not None:
            old_val = getattr(card, field)
            new_val = update_data[field]
            if old_val != new_val:
                setattr(card, field, new_val)
                modified = True

    if not modified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please modify to update ..."
        )

    db.commit()
    db.refresh(card)

    account = db.query(Account).filter(Account.acct_id == acct_id).first()
    xref = db.query(CardXref).filter(CardXref.card_num == card_num).first()
    customer = None
    if xref:
        customer = db.query(Customer).filter(Customer.cust_id == xref.cust_id).first()

    return {"card": card, "account": account, "customer": customer}
