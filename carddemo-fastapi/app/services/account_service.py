from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import Account, Customer, CardXref


def get_account_view(db: Session, acct_id: int) -> dict:
    account = db.query(Account).filter(Account.acct_id == acct_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account: {acct_id} not found in Acct Master file"
        )

    xref = db.query(CardXref).filter(CardXref.acct_id == acct_id).first()
    customer = None
    if xref:
        customer = db.query(Customer).filter(Customer.cust_id == xref.cust_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CustId: {xref.cust_id} not found in customer master"
            )

    return {"account": account, "customer": customer}


def update_account(db: Session, acct_id: int, update_data: dict) -> dict:
    account = db.query(Account).filter(Account.acct_id == acct_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account: {acct_id} not found in Acct Master file"
        )

    xref = db.query(CardXref).filter(CardXref.acct_id == acct_id).first()
    customer = None
    if xref:
        customer = db.query(Customer).filter(Customer.cust_id == xref.cust_id).first()

    acct_fields = [
        "active_status", "curr_bal", "credit_limit", "cash_credit_limit",
        "open_date", "expiration_date", "reissue_date",
        "curr_cyc_credit", "curr_cyc_debit", "addr_zip", "group_id",
    ]
    modified = False
    for field in acct_fields:
        if field in update_data and update_data[field] is not None:
            old_val = getattr(account, field)
            new_val = update_data[field]
            if old_val != new_val:
                setattr(account, field, new_val)
                modified = True

    cust_field_map = {
        "cust_first_name": "first_name",
        "cust_middle_name": "middle_name",
        "cust_last_name": "last_name",
        "cust_addr_line_1": "addr_line_1",
        "cust_addr_line_2": "addr_line_2",
        "cust_addr_line_3": "addr_line_3",
        "cust_addr_state_cd": "addr_state_cd",
        "cust_addr_country_cd": "addr_country_cd",
        "cust_addr_zip": "addr_zip",
        "cust_phone_num_1": "phone_num_1",
        "cust_phone_num_2": "phone_num_2",
        "cust_ssn": "ssn",
        "cust_govt_issued_id": "govt_issued_id",
        "cust_dob_yyyymmdd": "dob_yyyymmdd",
        "cust_eft_account_id": "eft_account_id",
        "cust_pri_card_holder_ind": "pri_card_holder_ind",
        "cust_fico_credit_score": "fico_credit_score",
    }
    if customer:
        for req_field, db_field in cust_field_map.items():
            if req_field in update_data and update_data[req_field] is not None:
                old_val = getattr(customer, db_field)
                new_val = update_data[req_field]
                if old_val != new_val:
                    setattr(customer, db_field, new_val)
                    modified = True

    if not modified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please modify to update ..."
        )

    db.commit()
    db.refresh(account)
    if customer:
        db.refresh(customer)

    return {"account": account, "customer": customer}
