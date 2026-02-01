# CBTRN02C Testing Framework - Execution Results

**Execution Date:** February 01, 2026  
**Test Mode:** Spark-only (comparing against expected values)  
**GnuCOBOL:** Available but not used (would require mainframe file format setup)  
**PySpark:** Available and used for testing

---

## Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | 11 |
| Passed | 8 |
| Failed | 3 |
| Pass Rate | 72.7% |

---

## Detailed Test Results

| Test Case | Description | Expected Output | Spark Output | Status |
|-----------|-------------|-----------------|--------------|--------|
| TC001_VALID_TRANSACTION | Single valid transaction that should post successfully | Read: 1, Written: 1, Rejected: 0 | Read: 1, Written: 1, Rejected: 0 | PASSED |
| TC002_INVALID_CARD | Transaction with card number not in XREFFILE - reject code 100 | Read: 1, Written: 0, Rejected: 1 (Code 100) | Read: 1, Written: 0, Rejected: 1 (Code 100) | PASSED |
| TC003_ACCOUNT_NOT_FOUND | Card exists in XREFFILE but account not in ACCTFILE - reject code 101 | Read: 1, Written: 0, Rejected: 1 (Code 101) | Read: 1, Written: 0, Rejected: 1 (Code 101) | PASSED |
| TC004_OVERLIMIT | Transaction exceeds credit limit - reject code 102 | Read: 1, Written: 0, Rejected: 1 (Code 102) | Read: 1, Written: 1, Rejected: 0 | FAILED |
| TC005_EXPIRED_ACCOUNT | Transaction on expired account - reject code 103 | Read: 1, Written: 0, Rejected: 1 (Code 103) | Read: 1, Written: 0, Rejected: 1 (Code 103) | PASSED |
| TC006_MULTI_TRANS_SAME_ACCOUNT | Multiple transactions for same account - tests sequential balance updates | Read: 3, Written: 2, Rejected: 1 (Code 102) | Read: 3, Written: 3, Rejected: 0 | FAILED |
| TC007_CREDIT_TRANSACTION | Payment/credit transaction with positive amount | Read: 1, Written: 1, Rejected: 0 | Read: 1, Written: 1, Rejected: 0 | PASSED |
| TC008_MIXED_TRANSACTIONS | Mix of valid and invalid transactions in single batch | Read: 4, Written: 2, Rejected: 2 | Read: 4, Written: 2, Rejected: 2 | PASSED |
| TC009_EXACT_LIMIT | Transaction that brings balance exactly to credit limit | Read: 1, Written: 1, Rejected: 0 | Read: 1, Written: 1, Rejected: 0 | PASSED |
| TC010_ZERO_AMOUNT | Transaction with zero amount | Read: 1, Written: 1, Rejected: 0 | Read: 1, Written: 1, Rejected: 0 | PASSED |
| TC_COMPREHENSIVE | All scenarios combined in single batch | Read: 15, Written: 8, Rejected: 7 | Read: 15, Written: 10, Rejected: 5 | FAILED |

---

## Validation Rules Tested

| Reject Code | Description | Test Cases | Spark Result |
|-------------|-------------|------------|--------------|
| 100 | INVALID CARD NUMBER FOUND | TC002, TC008, TC_COMPREHENSIVE | Working correctly |
| 101 | ACCOUNT RECORD NOT FOUND | TC003, TC008, TC_COMPREHENSIVE | Working correctly |
| 102 | OVERLIMIT TRANSACTION | TC004, TC006, TC_COMPREHENSIVE | Issue with sequential processing |
| 103 | TRANSACTION RECEIVED AFTER ACCT EXPIRATION | TC005, TC008, TC_COMPREHENSIVE | Working correctly |

---

## Failed Test Analysis

### TC004_OVERLIMIT

| Attribute | Expected (COBOL) | Actual (Spark) |
|-----------|------------------|----------------|
| Records Written | 0 | 1 |
| Records Rejected | 1 | 0 |
| Reject Code | 102 | N/A |

**Root Cause:** The overlimit calculation formula in Spark may differ from COBOL. The COBOL formula is:
```
WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL → PASS
```

The test case has:
- curr_cyc_credit = 9500.00
- curr_cyc_debit = 0.00
- tran_amt = -1000.00 (purchase)
- credit_limit = 10000.00

COBOL calculation: 9500 - 0 + (-1000) = 8500 (should pass, not fail)

**Note:** The expected values in the test vector may be incorrect. The Spark output appears to be correct based on the COBOL formula.

---

### TC006_MULTI_TRANS_SAME_ACCOUNT

| Attribute | Expected (COBOL) | Actual (Spark) |
|-----------|------------------|----------------|
| Records Written | 2 | 3 |
| Records Rejected | 1 | 0 |
| Transaction TRN0000000000008 | Rejected (Code 102) | Posted |

**Root Cause:** COBOL processes transactions **sequentially**, updating account balances after each transaction. Spark processes transactions in **parallel/batch** mode, using the original account balance for all validations.

**Sequential Processing (COBOL):**
1. TRN006: -500 → balance 1000+500=1500 → PASS, update balance
2. TRN007: -2000 → balance 1500+2000=3500 → PASS, update balance
3. TRN008: -2000 → balance 3500+2000=5500 > 5000 limit → FAIL

**Batch Processing (Spark):**
1. TRN006: -500 → original balance 1000+500=1500 → PASS
2. TRN007: -2000 → original balance 1000+2000=3000 → PASS
3. TRN008: -2000 → original balance 1000+2000=3000 → PASS

**Fix Required:** Implement sequential processing in Spark to match COBOL behavior.

---

### TC_COMPREHENSIVE

| Attribute | Expected (COBOL) | Actual (Spark) |
|-----------|------------------|----------------|
| Records Written | 8 | 10 |
| Records Rejected | 7 | 5 |

**Root Cause:** Same as TC004 and TC006 - combination of overlimit calculation and sequential processing issues.

---

## Recommendations

1. **Review Overlimit Formula:** Verify the expected values in TC004 match the actual COBOL formula. The Spark implementation may be correct.

2. **Implement Sequential Processing:** For TC006 and similar scenarios, the Spark job needs to process transactions sequentially within the same account to match COBOL behavior. This can be done using:
   - Window functions with running totals
   - Iterative processing per account
   - Spark's `foreach` with state management

3. **Re-run with GnuCOBOL:** To get actual COBOL outputs, compile and run CBTRN02C with GnuCOBOL using the generated test files.

---

## Test Files Generated

All test data files are in `/home/ubuntu/repos/MainframeConversion/testing-framework/golden_datasets/`:

| Test Case | Files Generated |
|-----------|-----------------|
| TC001_VALID_TRANSACTION | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC002_INVALID_CARD | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC003_ACCOUNT_NOT_FOUND | DALYTRAN.dat, XREFFILE.dat, expected/results.json |
| TC004_OVERLIMIT | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC005_EXPIRED_ACCOUNT | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC006_MULTI_TRANS_SAME_ACCOUNT | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC007_CREDIT_TRANSACTION | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC008_MIXED_TRANSACTIONS | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC009_EXACT_LIMIT | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC010_ZERO_AMOUNT | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |
| TC_COMPREHENSIVE | DALYTRAN.dat, ACCTFILE.dat, XREFFILE.dat, expected/results.json |

---

*Report generated by CBTRN02C Migration Testing Framework*
