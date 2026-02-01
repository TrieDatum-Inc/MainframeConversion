"""
CBTRN02C Test Cases - Comprehensive Test Vectors

This module defines all test cases for validating the CBTRN02C PySpark migration.
Each test case includes:
- Input data (daily transactions, accounts, card cross-references)
- Expected output (posted transactions, rejects, updated balances)
- Description of what is being tested

Test Categories:
1. Validation Rule Tests (Codes 100-103)
2. Sequential Processing Tests (Multiple transactions per account)
3. Edge Case Tests (Boundary conditions, zero amounts, exact limits)
4. Batch Processing Tests (Multiple accounts, mixed scenarios)
5. Data Integrity Tests (Balance updates, category balances)
"""

from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal
from datetime import date


@dataclass
class Account:
    """Account master record (matches CVACT01Y.cpy)"""
    acct_id: str
    active_status: str = "Y"
    curr_bal: Decimal = Decimal("0.00")
    credit_limit: Decimal = Decimal("5000.00")
    cash_credit_limit: Decimal = Decimal("1500.00")
    open_date: str = "2020-01-01"
    expiration_date: str = "2030-12-31"
    reissue_date: str = "2025-01-01"
    curr_cyc_credit: Decimal = Decimal("0.00")
    curr_cyc_debit: Decimal = Decimal("0.00")
    group_id: str = "DEFAULT"


@dataclass
class CardXref:
    """Card cross-reference record (matches CVACT03Y.cpy)"""
    card_num: str
    acct_id: str
    cust_id: str = "CUST001"


@dataclass
class DailyTransaction:
    """Daily transaction input record (matches CVTRA06Y.cpy)"""
    tran_id: str
    tran_type_cd: str = "PR"  # Purchase
    tran_cat_cd: int = 1001
    tran_source: str = "POS"
    tran_desc: str = "TEST TRANSACTION"
    tran_amt: Decimal = Decimal("-100.00")
    merchant_id: int = 123456789
    merchant_name: str = "TEST MERCHANT"
    merchant_city: str = "TEST CITY"
    merchant_zip: str = "12345"
    card_num: str = "4111111111111111"
    orig_ts: str = "2026-01-15-10.30.00.000000"
    batch_id: str = "TEST_BATCH_001"


@dataclass
class ExpectedResult:
    """Expected test result"""
    transactions_read: int
    transactions_posted: int
    transactions_rejected: int
    reject_codes: List[int] = field(default_factory=list)
    reject_tran_ids: List[str] = field(default_factory=list)
    posted_tran_ids: List[str] = field(default_factory=list)
    expected_account_balances: dict = field(default_factory=dict)  # acct_id -> new_curr_bal


@dataclass
class TestCase:
    """Complete test case definition"""
    test_id: str
    description: str
    category: str
    accounts: List[Account]
    card_xrefs: List[CardXref]
    transactions: List[DailyTransaction]
    expected: ExpectedResult
    notes: str = ""


# =============================================================================
# CATEGORY 1: VALIDATION RULE TESTS (Codes 100-103)
# =============================================================================

TC_100_INVALID_CARD = TestCase(
    test_id="TC_100_INVALID_CARD",
    description="Transaction with card number not in XREFFILE should be rejected with code 100",
    category="Validation Rules",
    accounts=[
        Account(acct_id="ACCT00001", credit_limit=Decimal("5000.00"))
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN100001",
            card_num="9999999999999999",  # Card not in xref
            tran_amt=Decimal("-100.00")
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=0,
        transactions_rejected=1,
        reject_codes=[100],
        reject_tran_ids=["TRN100001"]
    ),
    notes="COBOL paragraph 1500-A-LOOKUP-XREF rejects with 'INVALID CARD NUMBER FOUND'"
)

TC_101_ACCOUNT_NOT_FOUND = TestCase(
    test_id="TC_101_ACCOUNT_NOT_FOUND",
    description="Transaction with valid card but account not in ACCTFILE should be rejected with code 101",
    category="Validation Rules",
    accounts=[
        # Account ACCT00001 exists but ACCT00002 does not
        Account(acct_id="ACCT00001", credit_limit=Decimal("5000.00"))
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001"),
        CardXref(card_num="4222222222222222", acct_id="ACCT00002")  # Points to non-existent account
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN101001",
            card_num="4222222222222222",  # Valid card but account doesn't exist
            tran_amt=Decimal("-100.00")
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=0,
        transactions_rejected=1,
        reject_codes=[101],
        reject_tran_ids=["TRN101001"]
    ),
    notes="COBOL paragraph 1500-B-LOOKUP-ACCT rejects with 'ACCOUNT RECORD NOT FOUND'"
)

TC_102_OVERLIMIT = TestCase(
    test_id="TC_102_OVERLIMIT",
    description="Transaction that exceeds credit limit should be rejected with code 102",
    category="Validation Rules",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("1000.00"),
            curr_cyc_credit=Decimal("0.00"),
            curr_cyc_debit=Decimal("900.00")  # Already $900 used
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN102001",
            card_num="4111111111111111",
            tran_amt=Decimal("-150.00")  # Would make balance $1050, exceeds $1000 limit
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=0,
        transactions_rejected=1,
        reject_codes=[102],
        reject_tran_ids=["TRN102001"]
    ),
    notes="COBOL formula: WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT"
)

TC_103_EXPIRED = TestCase(
    test_id="TC_103_EXPIRED",
    description="Transaction on expired account should be rejected with code 103",
    category="Validation Rules",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("5000.00"),
            expiration_date="2025-12-31"  # Expired before transaction date
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN103001",
            card_num="4111111111111111",
            tran_amt=Decimal("-100.00"),
            orig_ts="2026-01-15-10.30.00.000000"  # After expiration
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=0,
        transactions_rejected=1,
        reject_codes=[103],
        reject_tran_ids=["TRN103001"]
    ),
    notes="COBOL paragraph 1500-B-LOOKUP-ACCT checks ACCT-EXPIRAION-DATE"
)

TC_VALID_TRANSACTION = TestCase(
    test_id="TC_VALID_TRANSACTION",
    description="Valid transaction should be posted successfully",
    category="Validation Rules",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("5000.00"),
            curr_bal=Decimal("500.00"),
            curr_cyc_credit=Decimal("0.00"),
            curr_cyc_debit=Decimal("500.00"),
            expiration_date="2030-12-31"
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_VALID_001",
            card_num="4111111111111111",
            tran_amt=Decimal("-100.00"),
            orig_ts="2026-01-15-10.30.00.000000"
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=1,
        transactions_rejected=0,
        posted_tran_ids=["TRN_VALID_001"],
        expected_account_balances={"ACCT00001": Decimal("400.00")}  # 500 - 100
    ),
    notes="All validations pass: card exists, account exists, within limit, not expired"
)


# =============================================================================
# CATEGORY 2: SEQUENTIAL PROCESSING TESTS
# =============================================================================

TC_SEQ_MULTI_TRANS_SAME_ACCOUNT = TestCase(
    test_id="TC_SEQ_MULTI_TRANS_SAME_ACCOUNT",
    description="Multiple transactions on same account - sequential processing affects overlimit",
    category="Sequential Processing",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("1000.00"),
            curr_cyc_credit=Decimal("0.00"),
            curr_cyc_debit=Decimal("0.00")
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_SEQ_001",
            card_num="4111111111111111",
            tran_amt=Decimal("-600.00"),  # Balance: $600
            orig_ts="2026-01-15-10.00.00.000000"
        ),
        DailyTransaction(
            tran_id="TRN_SEQ_002",
            card_num="4111111111111111",
            tran_amt=Decimal("-300.00"),  # Balance: $900
            orig_ts="2026-01-15-10.01.00.000000"
        ),
        DailyTransaction(
            tran_id="TRN_SEQ_003",
            card_num="4111111111111111",
            tran_amt=Decimal("-200.00"),  # Balance: $1100 - OVERLIMIT!
            orig_ts="2026-01-15-10.02.00.000000"
        )
    ],
    expected=ExpectedResult(
        transactions_read=3,
        transactions_posted=2,
        transactions_rejected=1,
        reject_codes=[102],
        reject_tran_ids=["TRN_SEQ_003"],
        posted_tran_ids=["TRN_SEQ_001", "TRN_SEQ_002"],
        expected_account_balances={"ACCT00001": Decimal("-900.00")}  # Only first 2 posted
    ),
    notes="CRITICAL: COBOL processes sequentially. Third transaction sees updated balance from first two."
)

TC_SEQ_PAYMENT_THEN_PURCHASE = TestCase(
    test_id="TC_SEQ_PAYMENT_THEN_PURCHASE",
    description="Payment followed by purchase - payment increases available credit",
    category="Sequential Processing",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("1000.00"),
            curr_cyc_credit=Decimal("0.00"),
            curr_cyc_debit=Decimal("950.00")  # Only $50 available
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_PAY_001",
            tran_type_cd="PM",  # Payment
            card_num="4111111111111111",
            tran_amt=Decimal("500.00"),  # Payment of $500 (positive)
            orig_ts="2026-01-15-10.00.00.000000"
        ),
        DailyTransaction(
            tran_id="TRN_PUR_001",
            tran_type_cd="PR",  # Purchase
            card_num="4111111111111111",
            tran_amt=Decimal("-400.00"),  # Purchase of $400
            orig_ts="2026-01-15-10.01.00.000000"
        )
    ],
    expected=ExpectedResult(
        transactions_read=2,
        transactions_posted=2,
        transactions_rejected=0,
        posted_tran_ids=["TRN_PAY_001", "TRN_PUR_001"],
        expected_account_balances={"ACCT00001": Decimal("-850.00")}  # -950 + 500 - 400 = -850
    ),
    notes="Payment increases available credit, allowing subsequent purchase to pass"
)

TC_SEQ_CASCADING_OVERLIMIT = TestCase(
    test_id="TC_SEQ_CASCADING_OVERLIMIT",
    description="First overlimit causes all subsequent to fail (cascading rejection)",
    category="Sequential Processing",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("500.00"),
            curr_cyc_credit=Decimal("0.00"),
            curr_cyc_debit=Decimal("400.00")  # $100 available
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_CAS_001",
            card_num="4111111111111111",
            tran_amt=Decimal("-200.00"),  # Would be $600, overlimit
            orig_ts="2026-01-15-10.00.00.000000"
        ),
        DailyTransaction(
            tran_id="TRN_CAS_002",
            card_num="4111111111111111",
            tran_amt=Decimal("-50.00"),  # Would be $650, overlimit
            orig_ts="2026-01-15-10.01.00.000000"
        ),
        DailyTransaction(
            tran_id="TRN_CAS_003",
            card_num="4111111111111111",
            tran_amt=Decimal("-25.00"),  # Would be $675, overlimit
            orig_ts="2026-01-15-10.02.00.000000"
        )
    ],
    expected=ExpectedResult(
        transactions_read=3,
        transactions_posted=0,
        transactions_rejected=3,
        reject_codes=[102, 102, 102],
        reject_tran_ids=["TRN_CAS_001", "TRN_CAS_002", "TRN_CAS_003"]
    ),
    notes="All transactions rejected because running balance exceeds limit"
)


# =============================================================================
# CATEGORY 3: EDGE CASE TESTS
# =============================================================================

TC_EDGE_EXACT_LIMIT = TestCase(
    test_id="TC_EDGE_EXACT_LIMIT",
    description="Transaction that brings balance exactly to credit limit should PASS",
    category="Edge Cases",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("1000.00"),
            curr_cyc_credit=Decimal("0.00"),
            curr_cyc_debit=Decimal("900.00")
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_EXACT_001",
            card_num="4111111111111111",
            tran_amt=Decimal("-100.00")  # Exactly $1000 = limit
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=1,
        transactions_rejected=0,
        posted_tran_ids=["TRN_EXACT_001"],
        expected_account_balances={"ACCT00001": Decimal("-1000.00")}
    ),
    notes="COBOL: IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL (>= not >)"
)

TC_EDGE_ONE_CENT_OVER = TestCase(
    test_id="TC_EDGE_ONE_CENT_OVER",
    description="Transaction that exceeds limit by $0.01 should be rejected",
    category="Edge Cases",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("1000.00"),
            curr_cyc_credit=Decimal("0.00"),
            curr_cyc_debit=Decimal("900.00")
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_OVER_001",
            card_num="4111111111111111",
            tran_amt=Decimal("-100.01")  # $1000.01 > $1000 limit
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=0,
        transactions_rejected=1,
        reject_codes=[102],
        reject_tran_ids=["TRN_OVER_001"]
    ),
    notes="Boundary test: even $0.01 over limit should reject"
)

TC_EDGE_ZERO_AMOUNT = TestCase(
    test_id="TC_EDGE_ZERO_AMOUNT",
    description="Transaction with zero amount should be posted (no balance impact)",
    category="Edge Cases",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("1000.00"),
            curr_bal=Decimal("500.00")
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_ZERO_001",
            card_num="4111111111111111",
            tran_amt=Decimal("0.00")
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=1,
        transactions_rejected=0,
        posted_tran_ids=["TRN_ZERO_001"],
        expected_account_balances={"ACCT00001": Decimal("500.00")}
    ),
    notes="Zero amount transactions (adjustments, reversals) should be allowed"
)

TC_EDGE_EXPIRATION_SAME_DAY = TestCase(
    test_id="TC_EDGE_EXPIRATION_SAME_DAY",
    description="Transaction on expiration date should PASS (not expired yet)",
    category="Edge Cases",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("5000.00"),
            expiration_date="2026-01-15"  # Same as transaction date
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_EXP_001",
            card_num="4111111111111111",
            tran_amt=Decimal("-100.00"),
            orig_ts="2026-01-15-10.30.00.000000"  # Same day as expiration
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=1,
        transactions_rejected=0,
        posted_tran_ids=["TRN_EXP_001"]
    ),
    notes="COBOL: IF ACCT-EXPIRAION-DATE >= WS-TRAN-DATE (>= means same day is OK)"
)

TC_EDGE_LARGE_PAYMENT = TestCase(
    test_id="TC_EDGE_LARGE_PAYMENT",
    description="Large payment (positive amount) should be posted and increase credit",
    category="Edge Cases",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("1000.00"),
            curr_bal=Decimal("800.00"),
            curr_cyc_credit=Decimal("0.00"),
            curr_cyc_debit=Decimal("800.00")
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_LPAY_001",
            tran_type_cd="PM",
            card_num="4111111111111111",
            tran_amt=Decimal("5000.00")  # Large payment
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=1,
        transactions_rejected=0,
        posted_tran_ids=["TRN_LPAY_001"],
        expected_account_balances={"ACCT00001": Decimal("5800.00")}  # 800 + 5000
    ),
    notes="Payments (positive amounts) should always pass overlimit check"
)


# =============================================================================
# CATEGORY 4: BATCH PROCESSING TESTS
# =============================================================================

TC_BATCH_MULTI_ACCOUNT = TestCase(
    test_id="TC_BATCH_MULTI_ACCOUNT",
    description="Multiple transactions across multiple accounts in single batch",
    category="Batch Processing",
    accounts=[
        Account(acct_id="ACCT00001", credit_limit=Decimal("5000.00")),
        Account(acct_id="ACCT00002", credit_limit=Decimal("3000.00")),
        Account(acct_id="ACCT00003", credit_limit=Decimal("1000.00"))
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001"),
        CardXref(card_num="4222222222222222", acct_id="ACCT00002"),
        CardXref(card_num="4333333333333333", acct_id="ACCT00003")
    ],
    transactions=[
        DailyTransaction(tran_id="TRN_BA_001", card_num="4111111111111111", tran_amt=Decimal("-100.00")),
        DailyTransaction(tran_id="TRN_BA_002", card_num="4222222222222222", tran_amt=Decimal("-200.00")),
        DailyTransaction(tran_id="TRN_BA_003", card_num="4333333333333333", tran_amt=Decimal("-300.00")),
        DailyTransaction(tran_id="TRN_BA_004", card_num="4111111111111111", tran_amt=Decimal("-150.00")),
        DailyTransaction(tran_id="TRN_BA_005", card_num="4222222222222222", tran_amt=Decimal("-250.00"))
    ],
    expected=ExpectedResult(
        transactions_read=5,
        transactions_posted=5,
        transactions_rejected=0,
        posted_tran_ids=["TRN_BA_001", "TRN_BA_002", "TRN_BA_003", "TRN_BA_004", "TRN_BA_005"],
        expected_account_balances={
            "ACCT00001": Decimal("-250.00"),  # -100 - 150
            "ACCT00002": Decimal("-450.00"),  # -200 - 250
            "ACCT00003": Decimal("-300.00")   # -300
        }
    ),
    notes="Tests that accounts are updated independently and correctly"
)

TC_BATCH_MIXED_RESULTS = TestCase(
    test_id="TC_BATCH_MIXED_RESULTS",
    description="Batch with mix of valid and invalid transactions",
    category="Batch Processing",
    accounts=[
        Account(acct_id="ACCT00001", credit_limit=Decimal("5000.00")),
        Account(acct_id="ACCT00002", credit_limit=Decimal("500.00"), curr_cyc_debit=Decimal("400.00")),
        Account(acct_id="ACCT00003", credit_limit=Decimal("5000.00"), expiration_date="2025-12-31")
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001"),
        CardXref(card_num="4222222222222222", acct_id="ACCT00002"),
        CardXref(card_num="4333333333333333", acct_id="ACCT00003")
    ],
    transactions=[
        DailyTransaction(tran_id="TRN_MX_001", card_num="4111111111111111", tran_amt=Decimal("-100.00")),  # Valid
        DailyTransaction(tran_id="TRN_MX_002", card_num="9999999999999999", tran_amt=Decimal("-50.00")),   # Invalid card (100)
        DailyTransaction(tran_id="TRN_MX_003", card_num="4222222222222222", tran_amt=Decimal("-200.00")),  # Overlimit (102)
        DailyTransaction(tran_id="TRN_MX_004", card_num="4333333333333333", tran_amt=Decimal("-75.00")),   # Expired (103)
        DailyTransaction(tran_id="TRN_MX_005", card_num="4111111111111111", tran_amt=Decimal("-200.00"))   # Valid
    ],
    expected=ExpectedResult(
        transactions_read=5,
        transactions_posted=2,
        transactions_rejected=3,
        reject_codes=[100, 102, 103],
        reject_tran_ids=["TRN_MX_002", "TRN_MX_003", "TRN_MX_004"],
        posted_tran_ids=["TRN_MX_001", "TRN_MX_005"],
        expected_account_balances={"ACCT00001": Decimal("-300.00")}
    ),
    notes="Tests all rejection codes in single batch"
)


# =============================================================================
# CATEGORY 5: DATA INTEGRITY TESTS
# =============================================================================

TC_INTEGRITY_BALANCE_UPDATE = TestCase(
    test_id="TC_INTEGRITY_BALANCE_UPDATE",
    description="Verify account balance fields are updated correctly",
    category="Data Integrity",
    accounts=[
        Account(
            acct_id="ACCT00001",
            credit_limit=Decimal("5000.00"),
            curr_bal=Decimal("1000.00"),
            curr_cyc_credit=Decimal("500.00"),
            curr_cyc_debit=Decimal("1500.00")
        )
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_INT_001",
            tran_type_cd="PR",
            card_num="4111111111111111",
            tran_amt=Decimal("-250.00")  # Purchase (debit)
        ),
        DailyTransaction(
            tran_id="TRN_INT_002",
            tran_type_cd="PM",
            card_num="4111111111111111",
            tran_amt=Decimal("100.00")  # Payment (credit)
        )
    ],
    expected=ExpectedResult(
        transactions_read=2,
        transactions_posted=2,
        transactions_rejected=0,
        posted_tran_ids=["TRN_INT_001", "TRN_INT_002"],
        expected_account_balances={
            "ACCT00001": Decimal("850.00")  # 1000 - 250 + 100 = 850
        }
    ),
    notes="COBOL: curr_bal += tran_amt; if tran_amt >= 0: curr_cyc_credit += tran_amt else: curr_cyc_debit += abs(tran_amt)"
)

TC_INTEGRITY_CATEGORY_BALANCE = TestCase(
    test_id="TC_INTEGRITY_CATEGORY_BALANCE",
    description="Verify transaction category balances are updated correctly",
    category="Data Integrity",
    accounts=[
        Account(acct_id="ACCT00001", credit_limit=Decimal("5000.00"))
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(tran_id="TRN_CAT_001", card_num="4111111111111111", tran_type_cd="PR", tran_cat_cd=1001, tran_amt=Decimal("-100.00")),
        DailyTransaction(tran_id="TRN_CAT_002", card_num="4111111111111111", tran_type_cd="PR", tran_cat_cd=1001, tran_amt=Decimal("-50.00")),
        DailyTransaction(tran_id="TRN_CAT_003", card_num="4111111111111111", tran_type_cd="PR", tran_cat_cd=2001, tran_amt=Decimal("-75.00"))
    ],
    expected=ExpectedResult(
        transactions_read=3,
        transactions_posted=3,
        transactions_rejected=0,
        posted_tran_ids=["TRN_CAT_001", "TRN_CAT_002", "TRN_CAT_003"]
    ),
    notes="Category 1001 should have -150.00, Category 2001 should have -75.00"
)


# =============================================================================
# CATEGORY 6: SPECIAL SCENARIOS
# =============================================================================

TC_SPECIAL_EMPTY_BATCH = TestCase(
    test_id="TC_SPECIAL_EMPTY_BATCH",
    description="Empty batch (no transactions) should complete successfully",
    category="Special Scenarios",
    accounts=[
        Account(acct_id="ACCT00001", credit_limit=Decimal("5000.00"))
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[],  # No transactions
    expected=ExpectedResult(
        transactions_read=0,
        transactions_posted=0,
        transactions_rejected=0
    ),
    notes="Job should handle empty input gracefully"
)

TC_SPECIAL_ALL_REJECTED = TestCase(
    test_id="TC_SPECIAL_ALL_REJECTED",
    description="All transactions rejected - no updates should occur",
    category="Special Scenarios",
    accounts=[
        Account(acct_id="ACCT00001", credit_limit=Decimal("100.00"), curr_cyc_debit=Decimal("100.00"))
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(tran_id="TRN_REJ_001", card_num="4111111111111111", tran_amt=Decimal("-50.00")),
        DailyTransaction(tran_id="TRN_REJ_002", card_num="4111111111111111", tran_amt=Decimal("-25.00")),
        DailyTransaction(tran_id="TRN_REJ_003", card_num="4111111111111111", tran_amt=Decimal("-10.00"))
    ],
    expected=ExpectedResult(
        transactions_read=3,
        transactions_posted=0,
        transactions_rejected=3,
        reject_codes=[102, 102, 102],
        reject_tran_ids=["TRN_REJ_001", "TRN_REJ_002", "TRN_REJ_003"]
    ),
    notes="Account balances should remain unchanged when all transactions rejected"
)

TC_SPECIAL_VALIDATION_PRIORITY = TestCase(
    test_id="TC_SPECIAL_VALIDATION_PRIORITY",
    description="Verify validation order: 100 -> 101 -> 102 -> 103",
    category="Special Scenarios",
    accounts=[
        # No accounts - will trigger 101 if card exists
    ],
    card_xrefs=[
        # No card xrefs - will trigger 100
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_PRI_001",
            card_num="9999999999999999",  # Invalid card
            tran_amt=Decimal("-100.00")
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=0,
        transactions_rejected=1,
        reject_codes=[100],  # Should be 100, not 101
        reject_tran_ids=["TRN_PRI_001"]
    ),
    notes="Invalid card (100) should be checked before account not found (101)"
)


# =============================================================================
# ALL TEST CASES COLLECTION
# =============================================================================

ALL_TEST_CASES = [
    # Validation Rules (5 tests)
    TC_100_INVALID_CARD,
    TC_101_ACCOUNT_NOT_FOUND,
    TC_102_OVERLIMIT,
    TC_103_EXPIRED,
    TC_VALID_TRANSACTION,
    
    # Sequential Processing (3 tests)
    TC_SEQ_MULTI_TRANS_SAME_ACCOUNT,
    TC_SEQ_PAYMENT_THEN_PURCHASE,
    TC_SEQ_CASCADING_OVERLIMIT,
    
    # Edge Cases (5 tests)
    TC_EDGE_EXACT_LIMIT,
    TC_EDGE_ONE_CENT_OVER,
    TC_EDGE_ZERO_AMOUNT,
    TC_EDGE_EXPIRATION_SAME_DAY,
    TC_EDGE_LARGE_PAYMENT,
    
    # Batch Processing (2 tests)
    TC_BATCH_MULTI_ACCOUNT,
    TC_BATCH_MIXED_RESULTS,
    
    # Data Integrity (2 tests)
    TC_INTEGRITY_BALANCE_UPDATE,
    TC_INTEGRITY_CATEGORY_BALANCE,
    
    # Special Scenarios (3 tests)
    TC_SPECIAL_EMPTY_BATCH,
    TC_SPECIAL_ALL_REJECTED,
    TC_SPECIAL_VALIDATION_PRIORITY,
]


def get_test_cases_by_category(category: str) -> List[TestCase]:
    """Get all test cases for a specific category."""
    return [tc for tc in ALL_TEST_CASES if tc.category == category]


def get_test_case_by_id(test_id: str) -> Optional[TestCase]:
    """Get a specific test case by ID."""
    for tc in ALL_TEST_CASES:
        if tc.test_id == test_id:
            return tc
    return None


def print_test_summary():
    """Print summary of all test cases."""
    categories = {}
    for tc in ALL_TEST_CASES:
        if tc.category not in categories:
            categories[tc.category] = []
        categories[tc.category].append(tc)
    
    print("=" * 80)
    print("CBTRN02C TEST CASE SUMMARY")
    print("=" * 80)
    print(f"Total Test Cases: {len(ALL_TEST_CASES)}")
    print()
    
    for category, tests in categories.items():
        print(f"\n{category} ({len(tests)} tests):")
        print("-" * 40)
        for tc in tests:
            print(f"  {tc.test_id}: {tc.description[:50]}...")


if __name__ == "__main__":
    print_test_summary()
