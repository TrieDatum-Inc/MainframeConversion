from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import TransactionType


def list_transaction_types(
    db: Session,
    type_cd_filter: str = None,
    type_desc_filter: str = None,
    page: int = 1,
    page_size: int = 7,
) -> dict:
    query = db.query(TransactionType)

    if type_cd_filter:
        query = query.filter(TransactionType.type_cd.like(f"%{type_cd_filter}%"))
    if type_desc_filter:
        query = query.filter(
            TransactionType.type_description.like(f"%{type_desc_filter}%")
        )

    total = query.count()
    offset = (page - 1) * page_size
    types = query.order_by(TransactionType.type_cd).offset(offset).limit(page_size + 1).all()

    has_more = len(types) > page_size
    if has_more:
        types = types[:page_size]

    return {
        "items": types,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": has_more,
    }


def get_transaction_type(db: Session, type_cd: str) -> TransactionType:
    ttype = db.query(TransactionType).filter(
        TransactionType.type_cd == type_cd
    ).first()
    if not ttype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No record found for this key in database"
        )
    return ttype


def create_transaction_type(db: Session, data: dict) -> TransactionType:
    existing = db.query(TransactionType).filter(
        TransactionType.type_cd == data["type_cd"]
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transaction type {data['type_cd']} already exists"
        )

    ttype = TransactionType(
        type_cd=data["type_cd"],
        type_description=data["type_description"],
    )
    db.add(ttype)
    db.commit()
    db.refresh(ttype)
    return ttype


def update_transaction_type(db: Session, type_cd: str, data: dict) -> TransactionType:
    ttype = db.query(TransactionType).filter(
        TransactionType.type_cd == type_cd
    ).first()
    if not ttype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No record found for this key in database"
        )

    if data.get("type_description") == ttype.type_description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No change detected with respect to values fetched."
        )

    ttype.type_description = data["type_description"]
    db.commit()
    db.refresh(ttype)
    return ttype


def delete_transaction_type(db: Session, type_cd: str) -> dict:
    ttype = db.query(TransactionType).filter(
        TransactionType.type_cd == type_cd
    ).first()
    if not ttype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No record found for this key in database"
        )

    db.delete(ttype)
    db.commit()
    return {"message": f"Transaction type {type_cd} deleted successfully"}
