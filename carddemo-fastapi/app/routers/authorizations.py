from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    AuthorizationRequest,
    AuthorizationResponse,
    PendingAuthSummaryResponse,
    PendingAuthDetailResponse,
    FraudToggleRequest,
    FraudToggleResponse,
)
from app.services.authorization_service import (
    process_authorization,
    get_pending_auth_summary,
    get_auth_detail,
    toggle_fraud_flag,
)

router = APIRouter(prefix="/api/authorizations", tags=["Authorizations (COPAUA0C, COPAUS0C, COPAUS1C)"])


@router.post("/process", response_model=AuthorizationResponse)
def process_auth(request: AuthorizationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = request.model_dump()
    return process_authorization(db, data)


@router.get("/accounts/{acct_id}", response_model=PendingAuthSummaryResponse)
def get_auth_summary(
    acct_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_pending_auth_summary(db, acct_id, page=page, page_size=page_size)
    auths = []
    for a in result["authorizations"]:
        auth_dict = {
            "id": a.id,
            "acct_id": a.acct_id,
            "card_num": a.card_num,
            "auth_date": a.auth_date,
            "auth_time": a.auth_time,
            "auth_type": a.auth_type,
            "auth_id_code": a.auth_id_code,
            "auth_resp_code": a.auth_resp_code,
            "auth_resp_reason": a.auth_resp_reason,
            "transaction_amt": a.transaction_amt,
            "approved_amt": a.approved_amt,
            "merchant_category_code": a.merchant_category_code,
            "merchant_id": a.merchant_id,
            "merchant_name": a.merchant_name,
            "merchant_city": a.merchant_city,
            "merchant_state": a.merchant_state,
            "merchant_zip": a.merchant_zip,
            "transaction_id": a.transaction_id,
            "message_type": a.message_type,
            "message_source": a.message_source,
            "processing_code": a.processing_code,
            "card_expiry_date": a.card_expiry_date,
            "pos_entry_mode": a.pos_entry_mode,
            "acqr_country_code": a.acqr_country_code,
            "fraud_confirmed": a.fraud_confirmed,
            "fraud_rpt_date": a.fraud_rpt_date,
            "match_status": a.match_status,
            "created_at": str(a.created_at) if a.created_at else None,
        }
        auths.append(auth_dict)

    return PendingAuthSummaryResponse(
        acct_id=result["acct_id"],
        cust_id=result["cust_id"],
        customer_name=result["customer_name"],
        credit_limit=result["credit_limit"],
        cash_limit=result["cash_limit"],
        credit_balance=result["credit_balance"],
        cash_balance=result["cash_balance"],
        approved_count=result["approved_count"],
        approved_amount=result["approved_amount"],
        declined_count=result["declined_count"],
        declined_amount=result["declined_amount"],
        authorizations=auths,
        page=result["page"],
        has_more=result["has_more"],
    )


@router.get("/{auth_detail_id}", response_model=PendingAuthDetailResponse)
def get_auth_detail_endpoint(auth_detail_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    detail = get_auth_detail(db, auth_detail_id)
    return PendingAuthDetailResponse.model_validate(detail)


@router.put("/{auth_detail_id}/fraud", response_model=FraudToggleResponse)
def toggle_fraud(auth_detail_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return toggle_fraud_flag(db, auth_detail_id)
