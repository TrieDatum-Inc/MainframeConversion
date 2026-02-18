from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.models import User
from app.schemas.schemas import (
    TransactionTypeResponse,
    TransactionTypeCreateRequest,
    TransactionTypeUpdateRequest,
    PaginatedResponse,
    MessageResponse,
)
from app.services.transaction_type_service import (
    list_transaction_types,
    get_transaction_type,
    create_transaction_type,
    update_transaction_type,
    delete_transaction_type,
)

router = APIRouter(prefix="/api/transaction-types", tags=["Transaction Types (COTRTUPC, COTRTLIC)"])


@router.get("", response_model=PaginatedResponse)
def list_types_endpoint(
    type_cd_filter: str = Query(None),
    type_desc_filter: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(7, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    result = list_transaction_types(
        db,
        type_cd_filter=type_cd_filter,
        type_desc_filter=type_desc_filter,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[TransactionTypeResponse.model_validate(t) for t in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
        has_more=result["has_more"],
    )


@router.get("/{type_cd}", response_model=TransactionTypeResponse)
def get_type_endpoint(type_cd: str, db: Session = Depends(get_db), admin_user: User = Depends(require_admin)):
    ttype = get_transaction_type(db, type_cd)
    return TransactionTypeResponse.model_validate(ttype)


@router.post("", response_model=TransactionTypeResponse, status_code=201)
def create_type_endpoint(
    request: TransactionTypeCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    data = request.model_dump()
    ttype = create_transaction_type(db, data)
    return TransactionTypeResponse.model_validate(ttype)


@router.put("/{type_cd}", response_model=TransactionTypeResponse)
def update_type_endpoint(
    type_cd: str,
    request: TransactionTypeUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    data = request.model_dump()
    ttype = update_transaction_type(db, type_cd, data)
    return TransactionTypeResponse.model_validate(ttype)


@router.delete("/{type_cd}", response_model=MessageResponse)
def delete_type_endpoint(type_cd: str, db: Session = Depends(get_db), admin_user: User = Depends(require_admin)):
    return delete_transaction_type(db, type_cd)
