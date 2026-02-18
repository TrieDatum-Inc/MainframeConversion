from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal


class SignonRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=8)
    password: str = Field(..., min_length=1, max_length=8)

    @field_validator("user_id")
    @classmethod
    def user_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Please enter User ID ...")
        return v.upper().strip()

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Please enter Password ...")
        return v.upper().strip()


class SignonResponse(BaseModel):
    user_id: str
    user_type: str
    access_token: str
    token_type: str = "bearer"


class AccountViewRequest(BaseModel):
    acct_id: int = Field(..., gt=0)

    @field_validator("acct_id")
    @classmethod
    def acct_id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Acct ID can NOT be zeros...")
        return v


class AccountResponse(BaseModel):
    acct_id: int
    active_status: Optional[str] = None
    curr_bal: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    cash_credit_limit: Optional[Decimal] = None
    open_date: Optional[str] = None
    expiration_date: Optional[str] = None
    reissue_date: Optional[str] = None
    curr_cyc_credit: Optional[Decimal] = None
    curr_cyc_debit: Optional[Decimal] = None
    addr_zip: Optional[str] = None
    group_id: Optional[str] = None

    model_config = {"from_attributes": True}


class CustomerResponse(BaseModel):
    cust_id: int
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    addr_line_1: Optional[str] = None
    addr_line_2: Optional[str] = None
    addr_line_3: Optional[str] = None
    addr_state_cd: Optional[str] = None
    addr_country_cd: Optional[str] = None
    addr_zip: Optional[str] = None
    phone_num_1: Optional[str] = None
    phone_num_2: Optional[str] = None
    ssn: Optional[int] = None
    govt_issued_id: Optional[str] = None
    dob_yyyymmdd: Optional[str] = None
    eft_account_id: Optional[str] = None
    pri_card_holder_ind: Optional[str] = None
    fico_credit_score: Optional[int] = None

    model_config = {"from_attributes": True}


class AccountDetailResponse(BaseModel):
    account: AccountResponse
    customer: Optional[CustomerResponse] = None


class AccountUpdateRequest(BaseModel):
    acct_id: int = Field(..., gt=0)
    active_status: Optional[str] = Field(None, max_length=1)
    curr_bal: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    cash_credit_limit: Optional[Decimal] = None
    open_date: Optional[str] = Field(None, max_length=10)
    expiration_date: Optional[str] = Field(None, max_length=10)
    reissue_date: Optional[str] = Field(None, max_length=10)
    curr_cyc_credit: Optional[Decimal] = None
    curr_cyc_debit: Optional[Decimal] = None
    addr_zip: Optional[str] = Field(None, max_length=10)
    group_id: Optional[str] = Field(None, max_length=10)
    cust_first_name: Optional[str] = Field(None, max_length=25)
    cust_middle_name: Optional[str] = Field(None, max_length=25)
    cust_last_name: Optional[str] = Field(None, max_length=25)
    cust_addr_line_1: Optional[str] = Field(None, max_length=50)
    cust_addr_line_2: Optional[str] = Field(None, max_length=50)
    cust_addr_line_3: Optional[str] = Field(None, max_length=50)
    cust_addr_state_cd: Optional[str] = Field(None, max_length=2)
    cust_addr_country_cd: Optional[str] = Field(None, max_length=3)
    cust_addr_zip: Optional[str] = Field(None, max_length=10)
    cust_phone_num_1: Optional[str] = Field(None, max_length=15)
    cust_phone_num_2: Optional[str] = Field(None, max_length=15)
    cust_ssn: Optional[int] = None
    cust_govt_issued_id: Optional[str] = Field(None, max_length=20)
    cust_dob_yyyymmdd: Optional[str] = Field(None, max_length=10)
    cust_eft_account_id: Optional[str] = Field(None, max_length=10)
    cust_pri_card_holder_ind: Optional[str] = Field(None, max_length=1)
    cust_fico_credit_score: Optional[int] = None

    @field_validator("acct_id")
    @classmethod
    def acct_id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Acct ID can NOT be zeros...")
        return v


class CardListRequest(BaseModel):
    acct_id: Optional[int] = None
    card_num: Optional[str] = Field(None, max_length=16)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class CardResponse(BaseModel):
    card_num: str
    acct_id: int
    cvv_cd: Optional[int] = None
    embossed_name: Optional[str] = None
    expiration_date: Optional[str] = None
    active_status: Optional[str] = None

    model_config = {"from_attributes": True}


class CardDetailRequest(BaseModel):
    acct_id: int = Field(..., gt=0)
    card_num: str = Field(..., min_length=1, max_length=16)

    @field_validator("acct_id")
    @classmethod
    def acct_id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Acct ID can NOT be zeros...")
        return v

    @field_validator("card_num")
    @classmethod
    def card_num_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Card Number can NOT be blank...")
        return v.strip()


class CardDetailResponse(BaseModel):
    card: CardResponse
    account: Optional[AccountResponse] = None
    customer: Optional[CustomerResponse] = None


class CardUpdateRequest(BaseModel):
    acct_id: int = Field(..., gt=0)
    card_num: str = Field(..., min_length=1, max_length=16)
    embossed_name: Optional[str] = Field(None, max_length=50)
    active_status: Optional[str] = Field(None, max_length=1)
    expiration_date: Optional[str] = Field(None, max_length=10)

    @field_validator("acct_id")
    @classmethod
    def acct_id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Acct ID can NOT be zeros...")
        return v

    @field_validator("card_num")
    @classmethod
    def card_num_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Card Number can NOT be blank...")
        return v.strip()


class TransactionListRequest(BaseModel):
    acct_id: Optional[int] = None
    card_num: Optional[str] = Field(None, max_length=16)
    tran_type_cd: Optional[str] = Field(None, max_length=2)
    tran_cat_cd: Optional[int] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class TransactionResponse(BaseModel):
    tran_id: str
    type_cd: Optional[str] = None
    cat_cd: Optional[int] = None
    source: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    merchant_id: Optional[int] = None
    merchant_name: Optional[str] = None
    merchant_city: Optional[str] = None
    merchant_zip: Optional[str] = None
    card_num: str
    orig_ts: Optional[str] = None
    proc_ts: Optional[str] = None

    model_config = {"from_attributes": True}


class TransactionAddRequest(BaseModel):
    type_cd: str = Field(..., min_length=1, max_length=2)
    cat_cd: int = Field(..., ge=0)
    source: str = Field(..., min_length=1, max_length=10)
    description: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(...)
    merchant_id: Optional[int] = None
    merchant_name: Optional[str] = Field(None, max_length=50)
    merchant_city: Optional[str] = Field(None, max_length=50)
    merchant_zip: Optional[str] = Field(None, max_length=10)
    card_num: str = Field(..., min_length=1, max_length=16)
    acct_id: int = Field(..., gt=0)

    @field_validator("type_cd")
    @classmethod
    def type_cd_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction Type can NOT be empty...")
        return v.strip()

    @field_validator("cat_cd")
    @classmethod
    def cat_cd_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Transaction Category can NOT be negative...")
        return v

    @field_validator("source")
    @classmethod
    def source_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction Source can NOT be empty...")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction Description can NOT be empty...")
        return v.strip()

    @field_validator("card_num")
    @classmethod
    def card_num_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Card Number can NOT be blank...")
        return v.strip()

    @field_validator("acct_id")
    @classmethod
    def acct_id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Account ID can NOT be zeros...")
        return v

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Transaction Amount must be greater than zero...")
        return v


class ReportSubmitRequest(BaseModel):
    report_type: str = Field(..., pattern="^(monthly_transaction|daily_transaction)$")
    start_month: Optional[int] = Field(None, ge=1, le=12)
    start_year: Optional[int] = Field(None, ge=2000)
    end_month: Optional[int] = Field(None, ge=1, le=12)
    end_year: Optional[int] = Field(None, ge=2000)

    @field_validator("start_month")
    @classmethod
    def start_month_required(cls, v: Optional[int], info) -> Optional[int]:
        if v is None:
            raise ValueError("Start Month must be entered...")
        return v

    @field_validator("start_year")
    @classmethod
    def start_year_required(cls, v: Optional[int], info) -> Optional[int]:
        if v is None:
            raise ValueError("Start Year must be entered...")
        return v

    @field_validator("end_month")
    @classmethod
    def end_month_required(cls, v: Optional[int], info) -> Optional[int]:
        if v is None:
            raise ValueError("End Month must be entered...")
        return v

    @field_validator("end_year")
    @classmethod
    def end_year_required(cls, v: Optional[int], info) -> Optional[int]:
        if v is None:
            raise ValueError("End Year must be entered...")
        return v


class ReportSubmitResponse(BaseModel):
    message: str
    job_id: Optional[str] = None
    report_type: str
    start_date: str
    end_date: str


class BillPaymentRequest(BaseModel):
    acct_id: int = Field(..., gt=0)

    @field_validator("acct_id")
    @classmethod
    def acct_id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Acct ID can NOT be zero...")
        return v


class BillPaymentResponse(BaseModel):
    message: str
    acct_id: int
    payment_amount: Decimal
    new_balance: Decimal
    tran_id: str


class AuthorizationRequest(BaseModel):
    auth_date: str = Field(..., max_length=10)
    auth_time: str = Field(..., max_length=10)
    card_num: str = Field(..., min_length=1, max_length=16)
    auth_type: str = Field(..., max_length=2)
    card_expiry_date: str = Field(..., max_length=4)
    message_type: str = Field(..., max_length=4)
    message_source: str = Field(..., max_length=10)
    processing_code: str = Field(..., max_length=2)
    transaction_amt: Decimal = Field(..., gt=0)
    merchant_category_code: Optional[str] = Field(None, max_length=4)
    acqr_country_code: Optional[str] = Field(None, max_length=3)
    pos_entry_mode: Optional[str] = Field(None, max_length=3)
    merchant_id: Optional[str] = Field(None, max_length=15)
    merchant_name: Optional[str] = Field(None, max_length=50)
    merchant_city: Optional[str] = Field(None, max_length=50)
    merchant_state: Optional[str] = Field(None, max_length=2)
    merchant_zip: Optional[str] = Field(None, max_length=10)
    transaction_id: Optional[str] = Field(None, max_length=16)

    @field_validator("card_num")
    @classmethod
    def card_num_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Card number is required")
        return v.strip()


class AuthorizationResponse(BaseModel):
    card_num: str
    transaction_id: Optional[str] = None
    auth_id_code: str
    auth_resp_code: str
    auth_resp_reason: str
    approved_amt: Decimal


class PendingAuthSummaryRequest(BaseModel):
    acct_id: int = Field(..., gt=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(5, ge=1, le=50)

    @field_validator("acct_id")
    @classmethod
    def acct_id_must_be_numeric(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Acct Id must be Numeric ...")
        return v


class PendingAuthSummaryResponse(BaseModel):
    acct_id: int
    cust_id: Optional[int] = None
    customer_name: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    cash_limit: Optional[Decimal] = None
    credit_balance: Optional[Decimal] = None
    cash_balance: Optional[Decimal] = None
    approved_count: int = 0
    approved_amount: Optional[Decimal] = None
    declined_count: int = 0
    declined_amount: Optional[Decimal] = None
    authorizations: list = []
    page: int = 1
    has_more: bool = False


class PendingAuthDetailResponse(BaseModel):
    id: int
    acct_id: int
    card_num: str
    auth_date: Optional[str] = None
    auth_time: Optional[str] = None
    auth_type: Optional[str] = None
    auth_id_code: Optional[str] = None
    auth_resp_code: Optional[str] = None
    auth_resp_reason: Optional[str] = None
    transaction_amt: Optional[Decimal] = None
    approved_amt: Optional[Decimal] = None
    merchant_category_code: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_city: Optional[str] = None
    merchant_state: Optional[str] = None
    merchant_zip: Optional[str] = None
    transaction_id: Optional[str] = None
    message_type: Optional[str] = None
    message_source: Optional[str] = None
    processing_code: Optional[str] = None
    card_expiry_date: Optional[str] = None
    pos_entry_mode: Optional[str] = None
    acqr_country_code: Optional[str] = None
    fraud_confirmed: Optional[str] = None
    fraud_rpt_date: Optional[str] = None
    match_status: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class FraudToggleRequest(BaseModel):
    auth_detail_id: int = Field(..., gt=0)


class FraudToggleResponse(BaseModel):
    auth_detail_id: int
    fraud_confirmed: str
    fraud_rpt_date: Optional[str] = None
    message: str


class UserListRequest(BaseModel):
    user_id_filter: Optional[str] = Field(None, max_length=8)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class UserResponse(BaseModel):
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: str

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=20)
    last_name: str = Field(..., min_length=1, max_length=20)
    user_id: str = Field(..., min_length=1, max_length=8)
    password: str = Field(..., min_length=1, max_length=8)
    user_type: str = Field(..., min_length=1, max_length=1)

    @field_validator("first_name")
    @classmethod
    def first_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("First Name can NOT be empty...")
        return v.strip()

    @field_validator("last_name")
    @classmethod
    def last_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Last Name can NOT be empty...")
        return v.strip()

    @field_validator("user_id")
    @classmethod
    def user_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("User ID can NOT be empty...")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password can NOT be empty...")
        return v.strip()

    @field_validator("user_type")
    @classmethod
    def user_type_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("User Type can NOT be empty...")
        v = v.strip().upper()
        if v not in ("A", "U"):
            raise ValueError("User Type must be 'A' (Admin) or 'U' (Regular)")
        return v


class UserUpdateRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=8)
    first_name: Optional[str] = Field(None, max_length=20)
    last_name: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, max_length=8)
    user_type: Optional[str] = Field(None, max_length=1)

    @field_validator("user_id")
    @classmethod
    def user_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("User ID can NOT be empty...")
        return v.strip()

    @field_validator("first_name")
    @classmethod
    def first_name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("First Name can NOT be empty...")
        return v.strip() if v else v

    @field_validator("last_name")
    @classmethod
    def last_name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Last Name can NOT be empty...")
        return v.strip() if v else v

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Password can NOT be empty...")
        return v.strip() if v else v

    @field_validator("user_type")
    @classmethod
    def user_type_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("User Type can NOT be empty...")
            v = v.strip().upper()
            if v not in ("A", "U"):
                raise ValueError("User Type must be 'A' (Admin) or 'U' (Regular)")
        return v


class UserDeleteRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=8)

    @field_validator("user_id")
    @classmethod
    def user_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("User ID can NOT be empty...")
        return v.strip()


class TransactionTypeResponse(BaseModel):
    type_cd: str
    type_description: Optional[str] = None

    model_config = {"from_attributes": True}


class TransactionTypeListRequest(BaseModel):
    type_cd_filter: Optional[str] = Field(None, max_length=2)
    type_desc_filter: Optional[str] = Field(None, max_length=50)
    page: int = Field(1, ge=1)
    page_size: int = Field(7, ge=1, le=100)


class TransactionTypeCreateRequest(BaseModel):
    type_cd: str = Field(..., min_length=1, max_length=2)
    type_description: str = Field(..., min_length=1, max_length=50)

    @field_validator("type_cd")
    @classmethod
    def type_cd_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction Type code can NOT be empty")
        return v.strip()

    @field_validator("type_description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction Type description can NOT be empty")
        return v.strip()


class TransactionTypeUpdateRequest(BaseModel):
    type_cd: str = Field(..., min_length=1, max_length=2)
    type_description: str = Field(..., min_length=1, max_length=50)

    @field_validator("type_cd")
    @classmethod
    def type_cd_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction Type code can NOT be empty")
        return v.strip()

    @field_validator("type_description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction Type description can NOT be empty")
        return v.strip()


class TransactionTypeDeleteRequest(BaseModel):
    type_cd: str = Field(..., min_length=1, max_length=2)

    @field_validator("type_cd")
    @classmethod
    def type_cd_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction Type code can NOT be empty")
        return v.strip()


class PaginatedResponse(BaseModel):
    items: list
    page: int
    page_size: int
    total: int
    has_more: bool


class MessageResponse(BaseModel):
    message: str
