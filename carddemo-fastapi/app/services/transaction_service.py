from datetime import datetime, date
from decimal import Decimal
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import Transaction, Card, CardXref, Account


def list_transactions(
    db: Session,
    acct_id: int = None,
    card_num: str = None,
    tran_type_cd: str = None,
    tran_cat_cd: int = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    query = db.query(Transaction)

    if card_num:
        query = query.filter(Transaction.card_num == card_num)
    elif acct_id:
        cards = db.query(Card.card_num).filter(Card.acct_id == acct_id).all()
        card_nums = [c[0] for c in cards]
        if card_nums:
            query = query.filter(Transaction.card_num.in_(card_nums))
        else:
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
                "has_more": False,
            }

    if tran_type_cd:
        query = query.filter(Transaction.type_cd == tran_type_cd)
    if tran_cat_cd is not None:
        query = query.filter(Transaction.cat_cd == tran_cat_cd)

    total = query.count()
    offset = (page - 1) * page_size
    transactions = query.order_by(Transaction.tran_id).offset(offset).limit(page_size + 1).all()

    has_more = len(transactions) > page_size
    if has_more:
        transactions = transactions[:page_size]

    return {
        "items": transactions,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": has_more,
    }


def get_transaction_detail(db: Session, tran_id: str) -> Transaction:
    transaction = db.query(Transaction).filter(Transaction.tran_id == tran_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction: {tran_id} not found in Transaction file"
        )
    return transaction


def add_transaction(db: Session, data: dict) -> Transaction:
    card = db.query(Card).filter(Card.card_num == data["card_num"]).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card Number: {data['card_num']} not found in card master"
        )

    xref = db.query(CardXref).filter(CardXref.card_num == data["card_num"]).first()
    if not xref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card Number: {data['card_num']} not found in cross reference file"
        )

    if xref.acct_id != data["acct_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Card {data['card_num']} does not belong to Account {data['acct_id']}"
        )

    account = db.query(Account).filter(Account.acct_id == data["acct_id"]).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account: {data['acct_id']} not found in account master"
        )
    expiration_date_str = account.expiration_date
    expiration_date = datetime.strptime(
        expiration_date_str, "%Y-%m-%d"
    ).date()
    today = date.today()

    if expiration_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account {data['acct_id']} is expired"
        )
    trans_amt = data['amount']
    projected_balance = (
        account.curr_cyc_credit
        - account.curr_cyc_debit
        + trans_amt
    )

    if projected_balance > account.credit_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TRANSACTION AMOUNT EXCEEDS CREDIT LIMIT"
        )
    curr_bal = account.curr_bal + trans_amt
    curr_cyc_credit = account.curr_cyc_credit
    curr_cyc_debit = account.curr_cyc_debit
    if trans_amt>=0:
        curr_cyc_credit = curr_cyc_credit + trans_amt
    else:
        curr_cyc_debit = curr_cyc_debit + trans_amt

    setattr(account, 'curr_bal', curr_bal)
    setattr(account, 'curr_cyc_credit', curr_cyc_credit)
    setattr(account, 'curr_cyc_debit', curr_cyc_debit)
    
    tran_id = f"T{uuid.uuid4().hex[:15].upper()}"
    now_ts = datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")

    transaction = Transaction(
        tran_id=tran_id,
        type_cd=data["type_cd"],
        cat_cd=data["cat_cd"],
        source=data["source"],
        description=data["description"],
        amount=data["amount"],
        merchant_id=data.get("merchant_id"),
        merchant_name=data.get("merchant_name"),
        merchant_city=data.get("merchant_city"),
        merchant_zip=data.get("merchant_zip"),
        card_num=data["card_num"],
        orig_ts=now_ts,
        proc_ts="",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    db.refresh(account)
    return transaction
