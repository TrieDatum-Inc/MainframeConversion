from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import User


def list_users(
    db: Session,
    user_id_filter: str = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    query = db.query(User)

    if user_id_filter:
        query = query.filter(User.user_id >= user_id_filter)

    total = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(User.user_id).offset(offset).limit(page_size + 1).all()

    has_more = len(users) > page_size
    if has_more:
        users = users[:page_size]

    return {
        "items": users,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": has_more,
    }


def create_user(db: Session, data: dict) -> User:
    existing = db.query(User).filter(User.user_id == data["user_id"]).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User ID already exist..."
        )

    user = User(
        user_id=data["user_id"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        password=data["password"],
        user_type=data["user_type"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User ID NOT found..."
        )
    return user


def update_user(db: Session, user_id: str, data: dict) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User ID NOT found..."
        )

    modified = False
    if data.get("first_name") is not None and data["first_name"] != user.first_name:
        user.first_name = data["first_name"]
        modified = True
    if data.get("last_name") is not None and data["last_name"] != user.last_name:
        user.last_name = data["last_name"]
        modified = True
    if data.get("password") is not None and data["password"] != user.password:
        user.password = data["password"]
        modified = True
    if data.get("user_type") is not None and data["user_type"] != user.user_type:
        user.user_type = data["user_type"]
        modified = True

    if not modified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please modify to update ..."
        )

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: str) -> dict:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User ID NOT found..."
        )

    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} has been deleted ..."}
