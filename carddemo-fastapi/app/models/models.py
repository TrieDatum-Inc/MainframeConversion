from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime, BigInteger
from sqlalchemy.sql import func
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    acct_id = Column(BigInteger, primary_key=True, index=True)
    active_status = Column(String(1), nullable=False, default="Y")
    curr_bal = Column(Numeric(12, 2), nullable=False, default=0)
    credit_limit = Column(Numeric(12, 2), nullable=False, default=0)
    cash_credit_limit = Column(Numeric(12, 2), nullable=False, default=0)
    open_date = Column(String(10), nullable=True)
    expiration_date = Column(String(10), nullable=True)
    reissue_date = Column(String(10), nullable=True)
    curr_cyc_credit = Column(Numeric(12, 2), nullable=False, default=0)
    curr_cyc_debit = Column(Numeric(12, 2), nullable=False, default=0)
    addr_zip = Column(String(10), nullable=True)
    group_id = Column(String(10), nullable=True)


class Card(Base):
    __tablename__ = "cards"

    card_num = Column(String(16), primary_key=True, index=True)
    acct_id = Column(BigInteger, ForeignKey("accounts.acct_id"), nullable=False, index=True)
    cvv_cd = Column(Integer, nullable=False, default=0)
    embossed_name = Column(String(50), nullable=True)
    expiration_date = Column(String(10), nullable=True)
    active_status = Column(String(1), nullable=False, default="Y")


class Customer(Base):
    __tablename__ = "customers"

    cust_id = Column(BigInteger, primary_key=True, index=True)
    first_name = Column(String(25), nullable=True)
    middle_name = Column(String(25), nullable=True)
    last_name = Column(String(25), nullable=True)
    addr_line_1 = Column(String(50), nullable=True)
    addr_line_2 = Column(String(50), nullable=True)
    addr_line_3 = Column(String(50), nullable=True)
    addr_state_cd = Column(String(2), nullable=True)
    addr_country_cd = Column(String(3), nullable=True)
    addr_zip = Column(String(10), nullable=True)
    phone_num_1 = Column(String(15), nullable=True)
    phone_num_2 = Column(String(15), nullable=True)
    ssn = Column(BigInteger, nullable=True)
    govt_issued_id = Column(String(20), nullable=True)
    dob_yyyymmdd = Column(String(10), nullable=True)
    eft_account_id = Column(String(10), nullable=True)
    pri_card_holder_ind = Column(String(1), nullable=True)
    fico_credit_score = Column(Integer, nullable=True, default=0)


class CardXref(Base):
    __tablename__ = "card_xref"

    card_num = Column(String(16), primary_key=True, index=True)
    cust_id = Column(BigInteger, ForeignKey("customers.cust_id"), nullable=False, index=True)
    acct_id = Column(BigInteger, ForeignKey("accounts.acct_id"), nullable=False, index=True)


class Transaction(Base):
    __tablename__ = "transactions"

    tran_id = Column(String(16), primary_key=True, index=True)
    type_cd = Column(String(2), nullable=True)
    cat_cd = Column(Integer, nullable=True, default=0)
    source = Column(String(10), nullable=True)
    description = Column(String(100), nullable=True)
    amount = Column(Numeric(11, 2), nullable=False, default=0)
    merchant_id = Column(BigInteger, nullable=True)
    merchant_name = Column(String(50), nullable=True)
    merchant_city = Column(String(50), nullable=True)
    merchant_zip = Column(String(10), nullable=True)
    card_num = Column(String(16), ForeignKey("cards.card_num"), nullable=False, index=True)
    orig_ts = Column(String(26), nullable=True)
    proc_ts = Column(String(26), nullable=True)


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(8), primary_key=True, index=True)
    first_name = Column(String(20), nullable=True)
    last_name = Column(String(20), nullable=True)
    password = Column(String(8), nullable=False)
    user_type = Column(String(1), nullable=False, default="U")


class TransactionType(Base):
    __tablename__ = "transaction_types"

    type_cd = Column(String(2), primary_key=True, index=True)
    type_description = Column(String(50), nullable=True)


class AuthorizationSummary(Base):
    __tablename__ = "authorization_summary"

    acct_id = Column(BigInteger, primary_key=True, index=True)
    cust_id = Column(BigInteger, nullable=True)
    credit_limit = Column(Numeric(12, 2), nullable=False, default=0)
    cash_limit = Column(Numeric(12, 2), nullable=False, default=0)
    credit_balance = Column(Numeric(12, 2), nullable=False, default=0)
    cash_balance = Column(Numeric(12, 2), nullable=False, default=0)
    approved_auth_cnt = Column(Integer, nullable=False, default=0)
    approved_auth_amt = Column(Numeric(12, 2), nullable=False, default=0)
    declined_auth_cnt = Column(Integer, nullable=False, default=0)
    declined_auth_amt = Column(Numeric(12, 2), nullable=False, default=0)


class AuthorizationDetail(Base):
    __tablename__ = "authorization_details"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    acct_id = Column(BigInteger, ForeignKey("authorization_summary.acct_id"), nullable=False, index=True)
    card_num = Column(String(16), nullable=False)
    auth_date = Column(String(10), nullable=True)
    auth_time = Column(String(10), nullable=True)
    auth_type = Column(String(2), nullable=True)
    auth_id_code = Column(String(26), nullable=True)
    auth_resp_code = Column(String(2), nullable=True)
    auth_resp_reason = Column(String(4), nullable=True)
    transaction_amt = Column(Numeric(11, 2), nullable=False, default=0)
    approved_amt = Column(Numeric(11, 2), nullable=False, default=0)
    merchant_category_code = Column(String(4), nullable=True)
    merchant_id = Column(String(15), nullable=True)
    merchant_name = Column(String(50), nullable=True)
    merchant_city = Column(String(50), nullable=True)
    merchant_state = Column(String(2), nullable=True)
    merchant_zip = Column(String(10), nullable=True)
    transaction_id = Column(String(16), nullable=True)
    message_type = Column(String(4), nullable=True)
    message_source = Column(String(10), nullable=True)
    processing_code = Column(String(2), nullable=True)
    card_expiry_date = Column(String(4), nullable=True)
    pos_entry_mode = Column(String(3), nullable=True)
    acqr_country_code = Column(String(3), nullable=True)
    fraud_confirmed = Column(String(1), nullable=True, default=" ")
    fraud_rpt_date = Column(String(10), nullable=True)
    match_status = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
