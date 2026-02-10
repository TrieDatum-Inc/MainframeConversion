from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str
    user_type: str


class LoginRequest(BaseModel):
    user_id: str = Field(..., max_length=8)
    password: str = Field(..., max_length=8)


class UserBase(BaseModel):
    id: str = Field(..., max_length=8)
    first_name: str = Field("", max_length=20)
    last_name: str = Field("", max_length=20)
    user_type: str = Field("U", max_length=1, pattern="^[AU]$")


class UserCreate(UserBase):
    password: str = Field(..., max_length=8)


class UserUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=20)
    last_name: str | None = Field(None, max_length=20)
    user_type: str | None = Field(None, max_length=1, pattern="^[AU]$")
    password: str | None = Field(None, max_length=8)


class UserResponse(UserBase):
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerBase(BaseModel):
    first_name: str = Field(..., max_length=25)
    middle_name: str = Field("", max_length=25)
    last_name: str = Field(..., max_length=25)
    addr_line_1: str = Field("", max_length=50)
    addr_line_2: str = Field("", max_length=50)
    addr_line_3: str = Field("", max_length=50)
    addr_state_cd: str = Field("", max_length=2)
    addr_country_cd: str = Field("", max_length=3)
    addr_zip: str = Field("", max_length=10)
    phone_num_1: str = Field("", max_length=15)
    phone_num_2: str = Field("", max_length=15)
    ssn: int
    govt_issued_id: str = Field("", max_length=20)
    dob: str = Field("", max_length=10)
    eft_account_id: str = Field("", max_length=10)
    pri_card_holder_ind: str = Field("Y", max_length=1)
    fico_credit_score: int = Field(0, ge=0, le=999)


class CustomerCreate(CustomerBase):
    id: int


class CustomerUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=25)
    middle_name: str | None = Field(None, max_length=25)
    last_name: str | None = Field(None, max_length=25)
    addr_line_1: str | None = Field(None, max_length=50)
    addr_line_2: str | None = Field(None, max_length=50)
    addr_line_3: str | None = Field(None, max_length=50)
    addr_state_cd: str | None = Field(None, max_length=2)
    addr_country_cd: str | None = Field(None, max_length=3)
    addr_zip: str | None = Field(None, max_length=10)
    phone_num_1: str | None = Field(None, max_length=15)
    phone_num_2: str | None = Field(None, max_length=15)
    ssn: int | None = None
    govt_issued_id: str | None = Field(None, max_length=20)
    dob: str | None = Field(None, max_length=10)
    eft_account_id: str | None = Field(None, max_length=10)
    pri_card_holder_ind: str | None = Field(None, max_length=1)
    fico_credit_score: int | None = Field(None, ge=0, le=999)


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountBase(BaseModel):
    active_status: str = Field("Y", max_length=1)
    curr_bal: Decimal = Field(Decimal("0.00"))
    credit_limit: Decimal = Field(Decimal("0.00"))
    cash_credit_limit: Decimal = Field(Decimal("0.00"))
    open_date: str = Field("", max_length=10)
    expiration_date: str = Field("", max_length=10)
    reissue_date: str = Field("", max_length=10)
    curr_cyc_credit: Decimal = Field(Decimal("0.00"))
    curr_cyc_debit: Decimal = Field(Decimal("0.00"))
    addr_zip: str = Field("", max_length=10)
    group_id: str = Field("", max_length=10)


class AccountCreate(AccountBase):
    id: int


class AccountUpdate(BaseModel):
    active_status: str | None = Field(None, max_length=1)
    curr_bal: Decimal | None = None
    credit_limit: Decimal | None = None
    cash_credit_limit: Decimal | None = None
    open_date: str | None = Field(None, max_length=10)
    expiration_date: str | None = Field(None, max_length=10)
    reissue_date: str | None = Field(None, max_length=10)
    curr_cyc_credit: Decimal | None = None
    curr_cyc_debit: Decimal | None = None
    addr_zip: str | None = Field(None, max_length=10)
    group_id: str | None = Field(None, max_length=10)


class AccountResponse(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountDetailResponse(AccountResponse):
    customer: CustomerResponse | None = None
    cards: list["CardResponse"] = []


class CardBase(BaseModel):
    card_num: str = Field(..., max_length=16)
    acct_id: int
    cvv_cd: int = Field(0, ge=0, le=999)
    embossed_name: str = Field("", max_length=50)
    expiration_date: str = Field("", max_length=10)
    active_status: str = Field("Y", max_length=1)


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    cvv_cd: int | None = Field(None, ge=0, le=999)
    embossed_name: str | None = Field(None, max_length=50)
    expiration_date: str | None = Field(None, max_length=10)
    active_status: str | None = Field(None, max_length=1)


class CardResponse(CardBase):
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CardXrefBase(BaseModel):
    card_num: str = Field(..., max_length=16)
    cust_id: int
    acct_id: int


class CardXrefResponse(CardXrefBase):
    model_config = {"from_attributes": True}


class TransactionBase(BaseModel):
    id: str = Field(..., max_length=20)
    type_cd: str = Field("", max_length=2)
    cat_cd: int = Field(0)
    source: str = Field("", max_length=10)
    description: str = Field("")
    amount: Decimal = Field(Decimal("0.00"))
    merchant_id: int = Field(0)
    merchant_name: str = Field("", max_length=50)
    merchant_city: str = Field("", max_length=50)
    merchant_zip: str = Field("", max_length=10)
    card_num: str = Field("", max_length=16)
    orig_ts: str = Field("", max_length=26)
    proc_ts: str = Field("", max_length=26)


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionTypeResponse(BaseModel):
    type_cd: str
    type_desc: str

    model_config = {"from_attributes": True}


class TransactionCategoryResponse(BaseModel):
    type_cd: str
    cat_cd: int
    cat_desc: str

    model_config = {"from_attributes": True}


class TranCatBalanceResponse(BaseModel):
    acct_id: int
    type_cd: str
    cat_cd: int
    balance: Decimal

    model_config = {"from_attributes": True}


class BillPayRequest(BaseModel):
    acct_id: int
    amount: Decimal = Field(..., gt=0)


class BillPayResponse(BaseModel):
    status: str
    acct_id: int
    amount_paid: Decimal
    new_balance: Decimal


class ReportRequest(BaseModel):
    report_type: str = Field(..., pattern="^(transaction_detail|statement|account_summary)$")
    start_date: str | None = Field(None, max_length=10)
    end_date: str | None = Field(None, max_length=10)
    acct_id: int | None = None


class ReportResponse(BaseModel):
    report_id: str
    report_type: str
    status: str
    message: str


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
