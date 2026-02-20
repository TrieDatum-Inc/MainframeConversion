from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import (
    CardXref, Account, Customer, AuthorizationSummary, AuthorizationDetail,
)

DECLINE_REASONS = {
    "CARD_NOT_FOUND": "3100",
    "ACCT_NOT_FOUND": "3100",
    "CUST_NOT_FOUND": "3100",
    "INSUFFICIENT_FUND": "4100",
    "CARD_NOT_ACTIVE": "4200",
    "ACCOUNT_CLOSED": "4300",
    "CARD_FRAUD": "5100",
    "MERCHANT_FRAUD": "5200",
    "UNKNOWN": "9000",
}


def process_authorization(db: Session, data: dict) -> dict:
    card_num = data["card_num"]
    transaction_amt = Decimal(str(data["transaction_amt"]))
    auth_time = data["auth_time"]

    xref = db.query(CardXref).filter(CardXref.card_num == card_num).first()
    if not xref:
        return _build_decline_response(
            card_num, data.get("transaction_id"), auth_time,
            "05", DECLINE_REASONS["CARD_NOT_FOUND"], Decimal("0")
        )

    decline_reason = None

    account = db.query(Account).filter(Account.acct_id == xref.acct_id).first()
    if not account:
        decline_reason = "ACCT_NOT_FOUND"
    elif account.active_status != "Y":
        decline_reason = "ACCOUNT_CLOSED"

    customer = db.query(Customer).filter(Customer.cust_id == xref.cust_id).first()
    if not customer and not decline_reason:
        decline_reason = "CUST_NOT_FOUND"

    if not decline_reason and account:
        auth_summary = db.query(AuthorizationSummary).filter(
            AuthorizationSummary.acct_id == xref.acct_id
        ).first()

        if auth_summary:
            available_amt = auth_summary.credit_limit - auth_summary.credit_balance
        else:
            available_amt = account.credit_limit - account.curr_bal

        if transaction_amt > available_amt:
            decline_reason = "INSUFFICIENT_FUND"
    else:
        auth_summary = db.query(AuthorizationSummary).filter(
            AuthorizationSummary.acct_id == xref.acct_id
        ).first()

    if decline_reason:
        _update_auth_db(
            db, xref, account, auth_summary, data, auth_time,
            approved=False, approved_amt=Decimal("0"),
            decline_reason=decline_reason
        )
        return _build_decline_response(
            card_num, data.get("transaction_id"), auth_time,
            "05", DECLINE_REASONS[decline_reason], Decimal("0")
        )

    _update_auth_db(
        db, xref, account, auth_summary, data, auth_time,
        approved=True, approved_amt=transaction_amt
    )

    return {
        "card_num": card_num,
        "transaction_id": data.get("transaction_id"),
        "auth_id_code": auth_time,
        "auth_resp_code": "00",
        "auth_resp_reason": "0000",
        "approved_amt": transaction_amt,
    }


def _build_decline_response(
    card_num: str, transaction_id: str, auth_time: str,
    resp_code: str, resp_reason: str, approved_amt: Decimal
) -> dict:
    return {
        "card_num": card_num,
        "transaction_id": transaction_id,
        "auth_id_code": auth_time,
        "auth_resp_code": resp_code,
        "auth_resp_reason": resp_reason,
        "approved_amt": approved_amt,
    }


def _update_auth_db(
    db: Session, xref: CardXref, account: Account | None,
    auth_summary: AuthorizationSummary | None, data: dict, auth_time: str,
    approved: bool, approved_amt: Decimal,
    decline_reason: str | None = None
) -> None:
    transaction_amt = Decimal(str(data["transaction_amt"]))

    credit_limit = account.credit_limit if account else Decimal("0")
    cash_credit_limit = account.cash_credit_limit if account else Decimal("0")

    if not auth_summary:
        auth_summary = AuthorizationSummary(
            acct_id=xref.acct_id,
            cust_id=xref.cust_id,
            credit_limit=credit_limit,
            cash_limit=cash_credit_limit,
            credit_balance=Decimal("0"),
            cash_balance=Decimal("0"),
            approved_auth_cnt=0,
            approved_auth_amt=Decimal("0"),
            declined_auth_cnt=0,
            declined_auth_amt=Decimal("0"),
        )
        db.add(auth_summary)
        db.flush()

    auth_summary.credit_limit = credit_limit
    auth_summary.cash_limit = cash_credit_limit

    if approved:
        auth_summary.approved_auth_cnt += 1
        auth_summary.approved_auth_amt += approved_amt
        auth_summary.credit_balance += approved_amt
        auth_summary.cash_balance = Decimal("0")
        match_status = "PENDING"
        resp_code = "00"
        resp_reason = "0000"
    else:
        auth_summary.declined_auth_cnt += 1
        auth_summary.declined_auth_amt += transaction_amt
        match_status = "AUTH-DECLINED"
        resp_code = "05"
        resp_reason = DECLINE_REASONS.get(decline_reason, DECLINE_REASONS["UNKNOWN"])

    detail = AuthorizationDetail(
        acct_id=xref.acct_id,
        card_num=data["card_num"],
        auth_date=data.get("auth_date"),
        auth_time=data.get("auth_time"),
        auth_type=data.get("auth_type"),
        auth_id_code=auth_time,
        auth_resp_code=resp_code,
        auth_resp_reason=resp_reason,
        transaction_amt=transaction_amt,
        approved_amt=approved_amt,
        merchant_category_code=data.get("merchant_category_code"),
        merchant_id=data.get("merchant_id"),
        merchant_name=data.get("merchant_name"),
        merchant_city=data.get("merchant_city"),
        merchant_state=data.get("merchant_state"),
        merchant_zip=data.get("merchant_zip"),
        transaction_id=data.get("transaction_id"),
        message_type=data.get("message_type"),
        message_source=data.get("message_source"),
        processing_code=data.get("processing_code"),
        card_expiry_date=data.get("card_expiry_date"),
        pos_entry_mode=data.get("pos_entry_mode"),
        acqr_country_code=data.get("acqr_country_code"),
        fraud_confirmed=" ",
        fraud_rpt_date="",
        match_status=match_status,
    )
    db.add(detail)
    db.commit()


def get_auth_summary(
    db: Session, acct_id: int, page: int = 1, page_size: int = 5
) -> dict:
    xref = db.query(CardXref).filter(CardXref.acct_id == acct_id).first()
    if not xref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account: {acct_id} not found in XREF file"
        )

    account = db.query(Account).filter(Account.acct_id == acct_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account: {acct_id} not found in ACCT file"
        )

    customer = db.query(Customer).filter(Customer.cust_id == xref.cust_id).first()
    customer_name = ""
    if customer:
        parts = []
        if customer.first_name:
            parts.append(customer.first_name.strip())
        if customer.middle_name:
            parts.append(customer.middle_name.strip()[:1])
        if customer.last_name:
            parts.append(customer.last_name.strip())
        customer_name = " ".join(parts)

    auth_summary = db.query(AuthorizationSummary).filter(
        AuthorizationSummary.acct_id == acct_id
    ).first()

    summary_data = {
        "acct_id": acct_id,
        "cust_id": xref.cust_id,
        "customer_name": customer_name,
        "credit_limit": account.credit_limit,
        "cash_limit": account.cash_credit_limit,
        "credit_balance": Decimal("0"),
        "cash_balance": Decimal("0"),
        "approved_count": 0,
        "approved_amount": Decimal("0"),
        "declined_count": 0,
        "declined_amount": Decimal("0"),
    }

    if auth_summary:
        summary_data.update({
            "credit_balance": auth_summary.credit_balance,
            "cash_balance": auth_summary.cash_balance,
            "approved_count": auth_summary.approved_auth_cnt,
            "approved_amount": auth_summary.approved_auth_amt,
            "declined_count": auth_summary.declined_auth_cnt,
            "declined_amount": auth_summary.declined_auth_amt,
        })

    offset = (page - 1) * page_size
    details = db.query(AuthorizationDetail).filter(
        AuthorizationDetail.acct_id == acct_id
    ).order_by(AuthorizationDetail.id.desc()).offset(offset).limit(page_size + 1).all()

    has_more = len(details) > page_size
    if has_more:
        details = details[:page_size]

    summary_data["authorizations"] = details
    summary_data["page"] = page
    summary_data["has_more"] = has_more

    return summary_data


def get_auth_detail(db: Session, auth_detail_id: int) -> AuthorizationDetail:
    detail = db.query(AuthorizationDetail).filter(
        AuthorizationDetail.id == auth_detail_id
    ).first()
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authorization detail {auth_detail_id} not found"
        )
    return detail


def toggle_fraud_flag(db: Session, auth_detail_id: int) -> dict:
    detail = db.query(AuthorizationDetail).filter(
        AuthorizationDetail.id == auth_detail_id
    ).first()
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authorization detail {auth_detail_id} not found"
        )

    if detail.fraud_confirmed and detail.fraud_confirmed.strip() == "F":
        detail.fraud_confirmed = " "
        detail.fraud_rpt_date = ""
        message = "Fraud flag removed"
    else:
        detail.fraud_confirmed = "F"
        detail.fraud_rpt_date = datetime.now().strftime("%Y-%m-%d")
        message = "Fraud flag set"

    db.commit()
    db.refresh(detail)

    return {
        "auth_detail_id": detail.id,
        "fraud_confirmed": detail.fraud_confirmed,
        "fraud_rpt_date": detail.fraud_rpt_date,
        "message": message,
    }