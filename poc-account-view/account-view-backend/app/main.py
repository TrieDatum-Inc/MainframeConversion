from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="CardDemo Account View API",
    description="Modern web API equivalent of mainframe COACTVWC.cbl (Account View) program",
    version="1.0.0"
)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# ============================================================================
# Data Models (based on COBOL copybooks CVACT01Y, CVCUS01Y, CVACT03Y)
# ============================================================================

class Customer(BaseModel):
    """Customer record - based on CVCUS01Y.cpy"""
    cust_id: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    addr_line_1: Optional[str] = None
    addr_line_2: Optional[str] = None
    city: Optional[str] = None
    state_cd: Optional[str] = None
    country_cd: Optional[str] = None
    zip_code: Optional[str] = None
    phone_num_1: Optional[str] = None
    phone_num_2: Optional[str] = None
    ssn: Optional[str] = None
    govt_issued_id: Optional[str] = None
    dob: Optional[str] = None
    eft_account_id: Optional[str] = None
    pri_card_holder_ind: Optional[str] = None
    fico_credit_score: Optional[int] = None

class Account(BaseModel):
    """Account record - based on CVACT01Y.cpy"""
    acct_id: str
    active_status: str
    curr_bal: float
    credit_limit: float
    cash_credit_limit: float
    open_date: Optional[str] = None
    expiration_date: Optional[str] = None
    reissue_date: Optional[str] = None
    curr_cyc_credit: float
    curr_cyc_debit: float
    group_id: Optional[str] = None

class CardXref(BaseModel):
    """Card cross-reference record - based on CVACT03Y.cpy"""
    card_num: str
    cust_id: str
    acct_id: str

class AccountViewResponse(BaseModel):
    """Combined response for Account View - matches COACTVWC screen output"""
    account: Account
    customer: Customer

# ============================================================================
# In-Memory Database (simulating VSAM files)
# ============================================================================

ACCOUNTS_DB: dict[str, Account] = {
    "00000000001": Account(
        acct_id="00000000001",
        active_status="Y",
        curr_bal=1500.75,
        credit_limit=10000.00,
        cash_credit_limit=2000.00,
        open_date="2020-01-15",
        expiration_date="2025-01-15",
        reissue_date="2024-01-15",
        curr_cyc_credit=500.00,
        curr_cyc_debit=250.25,
        group_id="PREMIUM"
    ),
    "00000000002": Account(
        acct_id="00000000002",
        active_status="Y",
        curr_bal=3250.50,
        credit_limit=15000.00,
        cash_credit_limit=3000.00,
        open_date="2019-06-20",
        expiration_date="2024-06-20",
        reissue_date="2023-06-20",
        curr_cyc_credit=1200.00,
        curr_cyc_debit=800.50,
        group_id="GOLD"
    ),
    "00000000003": Account(
        acct_id="00000000003",
        active_status="N",
        curr_bal=0.00,
        credit_limit=5000.00,
        cash_credit_limit=1000.00,
        open_date="2018-03-10",
        expiration_date="2023-03-10",
        reissue_date=None,
        curr_cyc_credit=0.00,
        curr_cyc_debit=0.00,
        group_id="STANDARD"
    ),
    "00000000004": Account(
        acct_id="00000000004",
        active_status="Y",
        curr_bal=7890.25,
        credit_limit=25000.00,
        cash_credit_limit=5000.00,
        open_date="2021-09-01",
        expiration_date="2026-09-01",
        reissue_date="2025-09-01",
        curr_cyc_credit=2500.00,
        curr_cyc_debit=1500.75,
        group_id="PLATINUM"
    ),
    "00000000005": Account(
        acct_id="00000000005",
        active_status="Y",
        curr_bal=450.00,
        credit_limit=3000.00,
        cash_credit_limit=500.00,
        open_date="2022-11-15",
        expiration_date="2027-11-15",
        reissue_date=None,
        curr_cyc_credit=100.00,
        curr_cyc_debit=50.00,
        group_id="STANDARD"
    ),
}

CUSTOMERS_DB: dict[str, Customer] = {
    "000000001": Customer(
        cust_id="000000001",
        first_name="John",
        middle_name="Michael",
        last_name="Smith",
        addr_line_1="123 Main Street",
        addr_line_2="Apt 4B",
        city="New York",
        state_cd="NY",
        country_cd="USA",
        zip_code="10001",
        phone_num_1="212-555-0101",
        phone_num_2="917-555-0102",
        ssn="123-45-6789",
        govt_issued_id="DL-NY-12345678",
        dob="1985-03-15",
        eft_account_id="EFT0000001",
        pri_card_holder_ind="Y",
        fico_credit_score=750
    ),
    "000000002": Customer(
        cust_id="000000002",
        first_name="Sarah",
        middle_name="Elizabeth",
        last_name="Johnson",
        addr_line_1="456 Oak Avenue",
        addr_line_2=None,
        city="Los Angeles",
        state_cd="CA",
        country_cd="USA",
        zip_code="90001",
        phone_num_1="310-555-0201",
        phone_num_2=None,
        ssn="234-56-7890",
        govt_issued_id="DL-CA-23456789",
        dob="1990-07-22",
        eft_account_id="EFT0000002",
        pri_card_holder_ind="Y",
        fico_credit_score=720
    ),
    "000000003": Customer(
        cust_id="000000003",
        first_name="Robert",
        middle_name=None,
        last_name="Williams",
        addr_line_1="789 Pine Road",
        addr_line_2="Suite 100",
        city="Chicago",
        state_cd="IL",
        country_cd="USA",
        zip_code="60601",
        phone_num_1="312-555-0301",
        phone_num_2="312-555-0302",
        ssn="345-67-8901",
        govt_issued_id="DL-IL-34567890",
        dob="1978-11-30",
        eft_account_id="EFT0000003",
        pri_card_holder_ind="Y",
        fico_credit_score=680
    ),
    "000000004": Customer(
        cust_id="000000004",
        first_name="Emily",
        middle_name="Rose",
        last_name="Davis",
        addr_line_1="321 Elm Street",
        addr_line_2=None,
        city="Houston",
        state_cd="TX",
        country_cd="USA",
        zip_code="77001",
        phone_num_1="713-555-0401",
        phone_num_2=None,
        ssn="456-78-9012",
        govt_issued_id="DL-TX-45678901",
        dob="1995-02-14",
        eft_account_id="EFT0000004",
        pri_card_holder_ind="Y",
        fico_credit_score=800
    ),
    "000000005": Customer(
        cust_id="000000005",
        first_name="Michael",
        middle_name="James",
        last_name="Brown",
        addr_line_1="555 Maple Drive",
        addr_line_2="Unit 12",
        city="Phoenix",
        state_cd="AZ",
        country_cd="USA",
        zip_code="85001",
        phone_num_1="602-555-0501",
        phone_num_2="602-555-0502",
        ssn="567-89-0123",
        govt_issued_id="DL-AZ-56789012",
        dob="1988-08-08",
        eft_account_id="EFT0000005",
        pri_card_holder_ind="Y",
        fico_credit_score=710
    ),
}

CARD_XREF_DB: dict[str, CardXref] = {
    "00000000001": CardXref(card_num="4111111111111111", cust_id="000000001", acct_id="00000000001"),
    "00000000002": CardXref(card_num="4222222222222222", cust_id="000000002", acct_id="00000000002"),
    "00000000003": CardXref(card_num="4333333333333333", cust_id="000000003", acct_id="00000000003"),
    "00000000004": CardXref(card_num="4444444444444444", cust_id="000000004", acct_id="00000000004"),
    "00000000005": CardXref(card_num="4555555555555555", cust_id="000000005", acct_id="00000000005"),
}

# ============================================================================
# API Endpoints (equivalent to CICS transactions)
# ============================================================================

@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/api/accounts/{account_id}", response_model=AccountViewResponse)
async def get_account_view(account_id: str):
    """
    Account View endpoint - equivalent to CICS transaction CAVW (program COACTVWC)
    """
    padded_acct_id = account_id.zfill(11)
    
    if len(padded_acct_id) != 11:
        raise HTTPException(status_code=400, detail="Account number must be an 11 digit number")
    
    if not padded_acct_id.isdigit():
        raise HTTPException(status_code=400, detail="Account number must be a non-zero 11 digit number")
    
    if padded_acct_id == "00000000000":
        raise HTTPException(status_code=400, detail="Account number must be a non-zero 11 digit number")
    
    xref = CARD_XREF_DB.get(padded_acct_id)
    if not xref:
        raise HTTPException(status_code=404, detail="Did not find this account in account card xref file")
    
    account = ACCOUNTS_DB.get(padded_acct_id)
    if not account:
        raise HTTPException(status_code=404, detail="Did not find this account in account master file")
    
    customer = CUSTOMERS_DB.get(xref.cust_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Did not find associated customer in master file")
    
    return AccountViewResponse(account=account, customer=customer)

@app.get("/api/accounts", response_model=list[Account])
async def list_accounts():
    """List all accounts - helper endpoint for the UI"""
    return list(ACCOUNTS_DB.values())
