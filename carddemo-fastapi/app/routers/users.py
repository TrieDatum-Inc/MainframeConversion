from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    PaginatedResponse,
    MessageResponse,
)
from app.services.user_service import (
    list_users,
    create_user,
    get_user,
    update_user,
    delete_user,
)

router = APIRouter(prefix="/api/users", tags=["Users (COUSR00C, COUSR01C, COUSR02C, COUSR03C)"])


@router.get("", response_model=PaginatedResponse)
def list_users_endpoint(
    user_id_filter: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = list_users(db, user_id_filter=user_id_filter, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
        has_more=result["has_more"],
    )


@router.post("", response_model=UserResponse, status_code=201)
def add_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    data = request.model_dump()
    user = create_user(db, data)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: str,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
):
    data = request.model_dump(exclude_unset=True)
    user = update_user(db, user_id, data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    return delete_user(db, user_id)
