"""
Test Vector Definitions for CBTRN02C Testing

This module defines deterministic test cases that cover all validation scenarios
in the CBTRN02C program. These test vectors are used to generate golden datasets
for testing both the COBOL program and the migrated Spark pipeline.

Test Scenarios Covered:
1. Valid transaction - posts successfully
2. Invalid card number (reject code 100)
3. Account not found (reject code 101)
4. Overlimit transaction (reject code 102)
5. Expired account (reject code 103)
6. Multiple transactions for same account (tests sequential processing)
7. Edge cases (zero amount, exact limit, etc.)
"""

from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# =============================================================================
# Data Classes for Test Vectors
# =============================================================================

@dataclass
class AccountRecord:
    """Account master record (CVACT01Y.cpy - 300 bytes)"""
    acct_id: str                    # PIC 9(11)
    active_status: str = "Y"        # PIC X(01)
    curr_bal: Decimal = Decimal("0.00")        # PIC S9(10)V99
    credit_limit: Decimal = Decimal("10000.00") # PIC S9(10)V99
    cash_credit_limit: Decimal = Decimal("2000.00")  # PIC S9(10)V99
    open_date: str = "2020-01-01"   # PIC X(10)
    expiration_date: str = "2030-12-31"  # PIC X(10)
    reissue_date: str = ""          # PIC X(10)
    curr_cyc_credit: Decimal = Decimal("0.00")  # PIC S9(10)V99
    curr_cyc_debit: Decimal = Decimal("0.00")   # PIC S9(10)V99
    addr_zip: str = "10001"         # PIC X(10)
    group_id: str = "STANDARD"      # PIC X(10)


@dataclass
class CardXrefRecord:
    """Card cross-reference record (CVACT03Y.cpy - 50 bytes)"""
    card_num: str       # PIC X(16)
    cust_id: str        # PIC 9(09)
    acct_id: str        # PIC 9(11)


@dataclass
class TranCatBalRecord:
    """Transaction category balance record (CVTRA01Y.cpy - 50 bytes)"""
    acct_id: str        # PIC 9(11)
    type_cd: str        # PIC X(02)
    cat_cd: int         # PIC 9(04)
    balance: Decimal    # PIC S9(09)V99


@dataclass
class DailyTransaction:
    """Daily transaction input record (CVTRA06Y.cpy - 350 bytes)"""
    tran_id: str                    # PIC X(16)
    type_cd: str                    # PIC X(02)
    cat_cd: int                     # PIC 9(04)
    source: str                     # PIC X(10)
    desc: str                       # PIC X(100)
    amount: Decimal                 # PIC S9(09)V99
    merchant_id: int                # PIC 9(09)
    merchant_name: str              # PIC X(50)
    merchant_city: str              # PIC X(50)
    merchant_zip: str               # PIC X(10)
    card_num: str                   # PIC X(16)
    orig_ts: str                    # PIC X(26)
    # Expected outcome for validation
    expected_valid: bool = True
    expected_reject_code: Optional[int] = None
    expected_reject_desc: Optional[str] = None


@dataclass
class ExpectedTransaction:
    """Expected output transaction record (CVTRA05Y.cpy - 350 bytes)"""
    tran_id: str
    type_cd: str
    cat_cd: int
    source: str
    desc: str
    amount: Decimal
    merchant_id: int
    merchant_name: str
    merchant_city: str
    merchant_zip: str
    card_num: str
    orig_ts: str
    proc_ts: str  # Will be set at runtime


@dataclass
class ExpectedReject:
    """Expected reject record"""
    tran_id: str
    reject_code: int
    reject_desc: str


@dataclass
class TestVector:
    """Complete test vector with inputs and expected outputs"""
    name: str
    description: str
    # Input data
    accounts: List[AccountRecord] = field(default_factory=list)
    card_xrefs: List[CardXrefRecord] = field(default_factory=list)
    initial_tran_cat_bal: List[TranCatBalRecord] = field(default_factory=list)
    daily_transactions: List[DailyTransaction] = field(default_factory=list)
    # Expected outputs (calculated)
    expected_transactions: List[ExpectedTransaction] = field(default_factory=list)
    expected_rejects: List[ExpectedReject] = field(default_factory=list)
    expected_account_updates: List[AccountRecord] = field(default_factory=list)
    expected_tran_cat_bal: List[TranCatBalRecord] = field(default_factory=list)
    # Counters
    expected_records_read: int = 0
    expected_records_written: int = 0
    expected_records_rejected: int = 0


# =============================================================================
# Golden Test Vectors
# =============================================================================

def create_golden_test_vectors() -> List[TestVector]:
    """
    Create comprehensive test vectors covering all validation scenarios.
    These are deterministic and can be used to generate golden datasets.
    """
    
    test_vectors = []
    
    # =========================================================================
    # Test Vector 1: Basic Valid Transaction
    # =========================================================================
    tv1 = TestVector(
        name="TC001_VALID_TRANSACTION",
        description="Single valid transaction that should post successfully"
    )
    tv1.accounts = [
        AccountRecord(
            acct_id="00000000001",
            active_status="Y",
            curr_bal=Decimal("1000.00"),
            credit_limit=Decimal("10000.00"),
            curr_cyc_credit=Decimal("500.00"),
            curr_cyc_debit=Decimal("-200.00"),
            expiration_date="2030-12-31"
        )
    ]
    tv1.card_xrefs = [
        CardXrefRecord(card_num="4111111111111111", cust_id="100000001", acct_id="00000000001")
    ]
    tv1.daily_transactions = [
        DailyTransaction(
            tran_id="TRN0000000000001",
            type_cd="PR",
            cat_cd=1001,
            source="POS",
            desc="GROCERY STORE PURCHASE",
            amount=Decimal("-50.00"),
            merchant_id=123456789,
            merchant_name="WHOLE FOODS",
            merchant_city="NEW YORK",
            merchant_zip="10001",
            card_num="4111111111111111",
            orig_ts="2025-01-15-10.30.00.000000",
            expected_valid=True
        )
    ]
    tv1.expected_records_read = 1
    tv1.expected_records_written = 1
    tv1.expected_records_rejected = 0
    test_vectors.append(tv1)
    
    # =========================================================================
    # Test Vector 2: Invalid Card Number (Reject Code 100)
    # =========================================================================
    tv2 = TestVector(
        name="TC002_INVALID_CARD",
        description="Transaction with card number not in XREFFILE - reject code 100"
    )
    tv2.accounts = [
        AccountRecord(acct_id="00000000001", curr_bal=Decimal("1000.00"), credit_limit=Decimal("10000.00"))
    ]
    tv2.card_xrefs = [
        CardXrefRecord(card_num="4111111111111111", cust_id="100000001", acct_id="00000000001")
    ]
    tv2.daily_transactions = [
        DailyTransaction(
            tran_id="TRN0000000000002",
            type_cd="PR",
            cat_cd=1001,
            source="POS",
            desc="INVALID CARD TEST",
            amount=Decimal("-100.00"),
            merchant_id=111111111,
            merchant_name="TEST MERCHANT",
            merchant_city="TEST CITY",
            merchant_zip="00000",
            card_num="9999999999999999",  # Card not in XREFFILE
            orig_ts="2025-01-15-11.00.00.000000",
            expected_valid=False,
            expected_reject_code=100,
            expected_reject_desc="INVALID CARD NUMBER FOUND"
        )
    ]
    tv2.expected_records_read = 1
    tv2.expected_records_written = 0
    tv2.expected_records_rejected = 1
    test_vectors.append(tv2)
    
    # =========================================================================
    # Test Vector 3: Account Not Found (Reject Code 101)
    # =========================================================================
    tv3 = TestVector(
        name="TC003_ACCOUNT_NOT_FOUND",
        description="Card exists in XREFFILE but account not in ACCTFILE - reject code 101"
    )
    tv3.accounts = []  # No accounts
    tv3.card_xrefs = [
        CardXrefRecord(card_num="4222222222222222", cust_id="100000002", acct_id="00000000099")  # Account doesn't exist
    ]
    tv3.daily_transactions = [
        DailyTransaction(
            tran_id="TRN0000000000003",
            type_cd="PR",
            cat_cd=1002,
            source="ONLINE",
            desc="ACCOUNT NOT FOUND TEST",
            amount=Decimal("-75.00"),
            merchant_id=222222222,
            merchant_name="AMAZON",
            merchant_city="SEATTLE",
            merchant_zip="98101",
            card_num="4222222222222222",
            orig_ts="2025-01-15-12.00.00.000000",
            expected_valid=False,
            expected_reject_code=101,
            expected_reject_desc="ACCOUNT RECORD NOT FOUND"
        )
    ]
    tv3.expected_records_read = 1
    tv3.expected_records_written = 0
    tv3.expected_records_rejected = 1
    test_vectors.append(tv3)
    
    # =========================================================================
    # Test Vector 4: Overlimit Transaction (Reject Code 102)
    # =========================================================================
    tv4 = TestVector(
        name="TC004_OVERLIMIT",
        description="Transaction exceeds credit limit - reject code 102"
    )
    tv4.accounts = [
        AccountRecord(
            acct_id="00000000004",
            curr_bal=Decimal("9500.00"),
            credit_limit=Decimal("10000.00"),
            curr_cyc_credit=Decimal("9500.00"),
            curr_cyc_debit=Decimal("0.00"),
            expiration_date="2030-12-31"
        )
    ]
    tv4.card_xrefs = [
        CardXrefRecord(card_num="4444444444444444", cust_id="100000004", acct_id="00000000004")
    ]
    tv4.daily_transactions = [
        DailyTransaction(
            tran_id="TRN0000000000004",
            type_cd="PR",
            cat_cd=1003,
            source="POS",
            desc="OVERLIMIT TEST - LARGE PURCHASE",
            amount=Decimal("-1000.00"),  # Would make balance 10500, exceeding 10000 limit
            merchant_id=444444444,
            merchant_name="BEST BUY",
            merchant_city="LOS ANGELES",
            merchant_zip="90001",
            card_num="4444444444444444",
            orig_ts="2025-01-15-13.00.00.000000",
            expected_valid=False,
            expected_reject_code=102,
            expected_reject_desc="OVERLIMIT TRANSACTION"
        )
    ]
    tv4.expected_records_read = 1
    tv4.expected_records_written = 0
    tv4.expected_records_rejected = 1
    test_vectors.append(tv4)
    
    # =========================================================================
    # Test Vector 5: Expired Account (Reject Code 103)
    # =========================================================================
    tv5 = TestVector(
        name="TC005_EXPIRED_ACCOUNT",
        description="Transaction on expired account - reject code 103"
    )
    tv5.accounts = [
        AccountRecord(
            acct_id="00000000005",
            curr_bal=Decimal("500.00"),
            credit_limit=Decimal("10000.00"),
            curr_cyc_credit=Decimal("500.00"),
            curr_cyc_debit=Decimal("0.00"),
            expiration_date="2024-12-31"  # Expired
        )
    ]
    tv5.card_xrefs = [
        CardXrefRecord(card_num="4555555555555555", cust_id="100000005", acct_id="00000000005")
    ]
    tv5.daily_transactions = [
        DailyTransaction(
            tran_id="TRN0000000000005",
            type_cd="PR",
            cat_cd=1001,
            source="POS",
            desc="EXPIRED ACCOUNT TEST",
            amount=Decimal("-25.00"),
            merchant_id=555555555,
            merchant_name="STARBUCKS",
            merchant_city="CHICAGO",
            merchant_zip="60601",
            card_num="4555555555555555",
            orig_ts="2025-01-15-14.00.00.000000",  # After expiration
            expected_valid=False,
            expected_reject_code=103,
            expected_reject_desc="TRANSACTION RECEIVED AFTER ACCT EXPIRATION"
        )
    ]
    tv5.expected_records_read = 1
    tv5.expected_records_written = 0
    tv5.expected_records_rejected = 1
    test_vectors.append(tv5)
    
    # =========================================================================
    # Test Vector 6: Multiple Transactions Same Account (Sequential Processing)
    # =========================================================================
    tv6 = TestVector(
        name="TC006_MULTI_TRANS_SAME_ACCOUNT",
        description="Multiple transactions for same account - tests sequential balance updates"
    )
    tv6.accounts = [
        AccountRecord(
            acct_id="00000000006",
            curr_bal=Decimal("1000.00"),
            credit_limit=Decimal("5000.00"),
            curr_cyc_credit=Decimal("1000.00"),
            curr_cyc_debit=Decimal("0.00"),
            expiration_date="2030-12-31"
        )
    ]
    tv6.card_xrefs = [
        CardXrefRecord(card_num="4666666666666666", cust_id="100000006", acct_id="00000000006")
    ]
    tv6.daily_transactions = [
        # Transaction 1: -500 (balance becomes 1500, within limit)
        DailyTransaction(
            tran_id="TRN0000000000006",
            type_cd="PR",
            cat_cd=1001,
            source="POS",
            desc="FIRST PURCHASE",
            amount=Decimal("-500.00"),
            merchant_id=666666666,
            merchant_name="TARGET",
            merchant_city="DALLAS",
            merchant_zip="75201",
            card_num="4666666666666666",
            orig_ts="2025-01-15-10.00.00.000000",
            expected_valid=True
        ),
        # Transaction 2: -2000 (balance becomes 3500, within limit)
        DailyTransaction(
            tran_id="TRN0000000000007",
            type_cd="PR",
            cat_cd=1002,
            source="ONLINE",
            desc="SECOND PURCHASE",
            amount=Decimal("-2000.00"),
            merchant_id=666666667,
            merchant_name="AMAZON",
            merchant_city="SEATTLE",
            merchant_zip="98101",
            card_num="4666666666666666",
            orig_ts="2025-01-15-11.00.00.000000",
            expected_valid=True
        ),
        # Transaction 3: -2000 (balance would become 5500, OVERLIMIT!)
        # Note: This tests that COBOL processes sequentially and updates balance
        DailyTransaction(
            tran_id="TRN0000000000008",
            type_cd="PR",
            cat_cd=1003,
            source="POS",
            desc="THIRD PURCHASE - SHOULD FAIL",
            amount=Decimal("-2000.00"),
            merchant_id=666666668,
            merchant_name="BEST BUY",
            merchant_city="HOUSTON",
            merchant_zip="77001",
            card_num="4666666666666666",
            orig_ts="2025-01-15-12.00.00.000000",
            expected_valid=False,
            expected_reject_code=102,
            expected_reject_desc="OVERLIMIT TRANSACTION"
        ),
    ]
    tv6.expected_records_read = 3
    tv6.expected_records_written = 2
    tv6.expected_records_rejected = 1
    test_vectors.append(tv6)
    
    # =========================================================================
    # Test Vector 7: Credit (Positive Amount) Transaction
    # =========================================================================
    tv7 = TestVector(
        name="TC007_CREDIT_TRANSACTION",
        description="Payment/credit transaction with positive amount"
    )
    tv7.accounts = [
        AccountRecord(
            acct_id="00000000007",
            curr_bal=Decimal("2000.00"),
            credit_limit=Decimal("10000.00"),
            curr_cyc_credit=Decimal("2000.00"),
            curr_cyc_debit=Decimal("0.00"),
            expiration_date="2030-12-31"
        )
    ]
    tv7.card_xrefs = [
        CardXrefRecord(card_num="4777777777777777", cust_id="100000007", acct_id="00000000007")
    ]
    tv7.daily_transactions = [
        DailyTransaction(
            tran_id="TRN0000000000009",
            type_cd="CR",
            cat_cd=2001,
            source="PAYMENT",
            desc="CUSTOMER PAYMENT",
            amount=Decimal("500.00"),  # Positive = credit/payment
            merchant_id=0,
            merchant_name="CUSTOMER PAYMENT",
            merchant_city="N/A",
            merchant_zip="00000",
            card_num="4777777777777777",
            orig_ts="2025-01-15-15.00.00.000000",
            expected_valid=True
        )
    ]
    tv7.expected_records_read = 1
    tv7.expected_records_written = 1
    tv7.expected_records_rejected = 0
    test_vectors.append(tv7)
    
    # =========================================================================
    # Test Vector 8: Mixed Valid and Invalid Transactions
    # =========================================================================
    tv8 = TestVector(
        name="TC008_MIXED_TRANSACTIONS",
        description="Mix of valid and invalid transactions in single batch"
    )
    tv8.accounts = [
        AccountRecord(
            acct_id="00000000008",
            curr_bal=Decimal("1000.00"),
            credit_limit=Decimal("10000.00"),
            curr_cyc_credit=Decimal("1000.00"),
            curr_cyc_debit=Decimal("0.00"),
            expiration_date="2030-12-31"
        ),
        AccountRecord(
            acct_id="00000000009",
            curr_bal=Decimal("500.00"),
            credit_limit=Decimal("5000.00"),
            curr_cyc_credit=Decimal("500.00"),
            curr_cyc_debit=Decimal("0.00"),
            expiration_date="2024-06-30"  # Expired
        )
    ]
    tv8.card_xrefs = [
        CardXrefRecord(card_num="4888888888888888", cust_id="100000008", acct_id="00000000008"),
        CardXrefRecord(card_num="4999999999999999", cust_id="100000009", acct_id="00000000009")
    ]
    tv8.daily_transactions = [
        # Valid transaction
        DailyTransaction(
            tran_id="TRN0000000000010",
            type_cd="PR",
            cat_cd=1001,
            source="POS",
            desc="VALID PURCHASE",
            amount=Decimal("-100.00"),
            merchant_id=888888888,
            merchant_name="WALMART",
            merchant_city="PHOENIX",
            merchant_zip="85001",
            card_num="4888888888888888",
            orig_ts="2025-01-15-09.00.00.000000",
            expected_valid=True
        ),
        # Invalid - card not found
        DailyTransaction(
            tran_id="TRN0000000000011",
            type_cd="PR",
            cat_cd=1001,
            source="POS",
            desc="INVALID CARD",
            amount=Decimal("-50.00"),
            merchant_id=111111111,
            merchant_name="UNKNOWN",
            merchant_city="UNKNOWN",
            merchant_zip="00000",
            card_num="1111111111111111",
            orig_ts="2025-01-15-09.30.00.000000",
            expected_valid=False,
            expected_reject_code=100,
            expected_reject_desc="INVALID CARD NUMBER FOUND"
        ),
        # Invalid - expired account
        DailyTransaction(
            tran_id="TRN0000000000012",
            type_cd="PR",
            cat_cd=1002,
            source="ONLINE",
            desc="EXPIRED ACCOUNT",
            amount=Decimal("-75.00"),
            merchant_id=999999999,
            merchant_name="EBAY",
            merchant_city="SAN JOSE",
            merchant_zip="95101",
            card_num="4999999999999999",
            orig_ts="2025-01-15-10.00.00.000000",
            expected_valid=False,
            expected_reject_code=103,
            expected_reject_desc="TRANSACTION RECEIVED AFTER ACCT EXPIRATION"
        ),
        # Another valid transaction
        DailyTransaction(
            tran_id="TRN0000000000013",
            type_cd="CR",
            cat_cd=2001,
            source="PAYMENT",
            desc="PAYMENT RECEIVED",
            amount=Decimal("200.00"),
            merchant_id=0,
            merchant_name="PAYMENT",
            merchant_city="N/A",
            merchant_zip="00000",
            card_num="4888888888888888",
            orig_ts="2025-01-15-11.00.00.000000",
            expected_valid=True
        ),
    ]
    tv8.expected_records_read = 4
    tv8.expected_records_written = 2
    tv8.expected_records_rejected = 2
    test_vectors.append(tv8)
    
    # =========================================================================
    # Test Vector 9: Edge Case - Exact Credit Limit
    # =========================================================================
    tv9 = TestVector(
        name="TC009_EXACT_LIMIT",
        description="Transaction that brings balance exactly to credit limit"
    )
    tv9.accounts = [
        AccountRecord(
            acct_id="00000000010",
            curr_bal=Decimal("9000.00"),
            credit_limit=Decimal("10000.00"),
            curr_cyc_credit=Decimal("9000.00"),
            curr_cyc_debit=Decimal("0.00"),
            expiration_date="2030-12-31"
        )
    ]
    tv9.card_xrefs = [
        CardXrefRecord(card_num="4100000000000000", cust_id="100000010", acct_id="00000000010")
    ]
    tv9.daily_transactions = [
        DailyTransaction(
            tran_id="TRN0000000000014",
            type_cd="PR",
            cat_cd=1001,
            source="POS",
            desc="EXACT LIMIT TEST",
            amount=Decimal("-1000.00"),  # Brings balance to exactly 10000
            merchant_id=100000000,
            merchant_name="EXACT LIMIT MERCHANT",
            merchant_city="TEST CITY",
            merchant_zip="00000",
            card_num="4100000000000000",
            orig_ts="2025-01-15-16.00.00.000000",
            expected_valid=True  # Should pass - exactly at limit, not over
        )
    ]
    tv9.expected_records_read = 1
    tv9.expected_records_written = 1
    tv9.expected_records_rejected = 0
    test_vectors.append(tv9)
    
    # =========================================================================
    # Test Vector 10: Edge Case - Zero Amount Transaction
    # =========================================================================
    tv10 = TestVector(
        name="TC010_ZERO_AMOUNT",
        description="Transaction with zero amount"
    )
    tv10.accounts = [
        AccountRecord(
            acct_id="00000000011",
            curr_bal=Decimal("1000.00"),
            credit_limit=Decimal("10000.00"),
            curr_cyc_credit=Decimal("1000.00"),
            curr_cyc_debit=Decimal("0.00"),
            expiration_date="2030-12-31"
        )
    ]
    tv10.card_xrefs = [
        CardXrefRecord(card_num="4110000000000000", cust_id="100000011", acct_id="00000000011")
    ]
    tv10.daily_transactions = [
        DailyTransaction(
            tran_id="TRN0000000000015",
            type_cd="AU",
            cat_cd=9999,
            source="AUTH",
            desc="AUTHORIZATION ONLY - ZERO AMOUNT",
            amount=Decimal("0.00"),
            merchant_id=110000000,
            merchant_name="AUTH MERCHANT",
            merchant_city="AUTH CITY",
            merchant_zip="00000",
            card_num="4110000000000000",
            orig_ts="2025-01-15-17.00.00.000000",
            expected_valid=True
        )
    ]
    tv10.expected_records_read = 1
    tv10.expected_records_written = 1
    tv10.expected_records_rejected = 0
    test_vectors.append(tv10)
    
    return test_vectors


# =============================================================================
# Utility Functions
# =============================================================================

def get_all_test_vectors() -> List[TestVector]:
    """Get all defined test vectors."""
    return create_golden_test_vectors()


def get_test_vector_by_name(name: str) -> Optional[TestVector]:
    """Get a specific test vector by name."""
    for tv in create_golden_test_vectors():
        if tv.name == name:
            return tv
    return None


def get_comprehensive_test_vector() -> TestVector:
    """
    Create a single comprehensive test vector that combines all scenarios.
    This is useful for running a complete end-to-end test.
    """
    all_vectors = create_golden_test_vectors()
    
    comprehensive = TestVector(
        name="TC_COMPREHENSIVE",
        description="Comprehensive test combining all scenarios"
    )
    
    for tv in all_vectors:
        comprehensive.accounts.extend(tv.accounts)
        comprehensive.card_xrefs.extend(tv.card_xrefs)
        comprehensive.initial_tran_cat_bal.extend(tv.initial_tran_cat_bal)
        comprehensive.daily_transactions.extend(tv.daily_transactions)
        comprehensive.expected_records_read += tv.expected_records_read
        comprehensive.expected_records_written += tv.expected_records_written
        comprehensive.expected_records_rejected += tv.expected_records_rejected
    
    # Deduplicate accounts and card_xrefs by key
    seen_accts = set()
    unique_accounts = []
    for acct in comprehensive.accounts:
        if acct.acct_id not in seen_accts:
            seen_accts.add(acct.acct_id)
            unique_accounts.append(acct)
    comprehensive.accounts = unique_accounts
    
    seen_cards = set()
    unique_xrefs = []
    for xref in comprehensive.card_xrefs:
        if xref.card_num not in seen_cards:
            seen_cards.add(xref.card_num)
            unique_xrefs.append(xref)
    comprehensive.card_xrefs = unique_xrefs
    
    return comprehensive


if __name__ == "__main__":
    # Print summary of test vectors
    vectors = get_all_test_vectors()
    print(f"Total test vectors: {len(vectors)}")
    print("-" * 60)
    for tv in vectors:
        print(f"{tv.name}: {tv.description}")
        print(f"  Transactions: {len(tv.daily_transactions)}")
        print(f"  Expected: {tv.expected_records_written} written, {tv.expected_records_rejected} rejected")
        print()
