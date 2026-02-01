# CBTRN02C Test Results Report

**Generated:** 2026-02-01T13:20:16.042659
**Database:** carddemo_test

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 20 |
| Passed | 13 |
| Failed | 7 |
| Pass Rate | 65.0% |

## Results by Category

| Category | Passed | Failed | Pass Rate |
|----------|--------|--------|-----------|
| Validation Rules | 4 | 1 | 80.0% |
| Sequential Processing | 1 | 2 | 33.3% |
| Edge Cases | 3 | 2 | 60.0% |
| Batch Processing | 1 | 1 | 50.0% |
| Data Integrity | 2 | 0 | 100.0% |
| Special Scenarios | 2 | 1 | 66.7% |

## Detailed Results

| Test ID | Description | Status | Read | Posted | Rejected | Time (ms) |
|---------|-------------|--------|------|--------|----------|-----------|
| TC_100_INVALID_CARD | Transaction with card number not in XREF... | PASS | OK | OK | OK | 11190 |
| TC_101_ACCOUNT_NOT_FOUND | Transaction with valid card but account ... | PASS | OK | OK | OK | 8048 |
| TC_102_OVERLIMIT | Transaction that exceeds credit limit sh... | FAIL | OK | 0/1 | 1/0 | 11669 |
| TC_103_EXPIRED | Transaction on expired account should be... | PASS | OK | OK | OK | 7485 |
| TC_VALID_TRANSACTION | Valid transaction should be posted succe... | PASS | OK | OK | OK | 11763 |
| TC_SEQ_MULTI_TRANS_SAME_ACCOUNT | Multiple transactions on same account - ... | FAIL | OK | 2/3 | 1/0 | 11491 |
| TC_SEQ_PAYMENT_THEN_PURCHASE | Payment followed by purchase - payment i... | PASS | OK | OK | OK | 13825 |
| TC_SEQ_CASCADING_OVERLIMIT | First overlimit causes all subsequent to... | FAIL | OK | 0/3 | 3/0 | 12477 |
| TC_EDGE_EXACT_LIMIT | Transaction that brings balance exactly ... | PASS | OK | OK | OK | 12012 |
| TC_EDGE_ONE_CENT_OVER | Transaction that exceeds limit by $0.01 ... | FAIL | OK | 0/1 | 1/0 | 13970 |
| TC_EDGE_ZERO_AMOUNT | Transaction with zero amount should be p... | PASS | OK | OK | OK | 12753 |
| TC_EDGE_EXPIRATION_SAME_DAY | Transaction on expiration date should PA... | PASS | OK | OK | OK | 13268 |
| TC_EDGE_LARGE_PAYMENT | Large payment (positive amount) should b... | FAIL | OK | 1/0 | 0/1 | 7836 |
| TC_BATCH_MULTI_ACCOUNT | Multiple transactions across multiple ac... | PASS | OK | OK | OK | 13303 |
| TC_BATCH_MIXED_RESULTS | Batch with mix of valid and invalid tran... | FAIL | OK | 2/3 | 3/2 | 15347 |
| TC_INTEGRITY_BALANCE_UPDATE | Verify account balance fields are update... | PASS | OK | OK | OK | 12666 |
| TC_INTEGRITY_CATEGORY_BALANCE | Verify transaction category balances are... | PASS | OK | OK | OK | 13478 |
| TC_SPECIAL_EMPTY_BATCH | Empty batch (no transactions) should com... | PASS | OK | OK | OK | 3917 |
| TC_SPECIAL_ALL_REJECTED | All transactions rejected - no updates s... | FAIL | OK | 0/3 | 3/0 | 12248 |
| TC_SPECIAL_VALIDATION_PRIORITY | Verify validation order: 100 -> 101 -> 1... | PASS | OK | OK | OK | 5007 |

## Failed Tests Details

### TC_102_OVERLIMIT

**Description:** Transaction that exceeds credit limit should be rejected with code 102

| Metric | Expected | Actual |
|--------|----------|--------|
| Transactions Read | 1 | 1 |
| Transactions Posted | 0 | 1 |
| Transactions Rejected | 1 | 0 |
| Reject Codes | [102] | [] |

### TC_SEQ_MULTI_TRANS_SAME_ACCOUNT

**Description:** Multiple transactions on same account - sequential processing affects overlimit

| Metric | Expected | Actual |
|--------|----------|--------|
| Transactions Read | 3 | 3 |
| Transactions Posted | 2 | 3 |
| Transactions Rejected | 1 | 0 |
| Reject Codes | [102] | [] |

### TC_SEQ_CASCADING_OVERLIMIT

**Description:** First overlimit causes all subsequent to fail (cascading rejection)

| Metric | Expected | Actual |
|--------|----------|--------|
| Transactions Read | 3 | 3 |
| Transactions Posted | 0 | 3 |
| Transactions Rejected | 3 | 0 |
| Reject Codes | [102, 102, 102] | [] |

### TC_EDGE_ONE_CENT_OVER

**Description:** Transaction that exceeds limit by $0.01 should be rejected

| Metric | Expected | Actual |
|--------|----------|--------|
| Transactions Read | 1 | 1 |
| Transactions Posted | 0 | 1 |
| Transactions Rejected | 1 | 0 |
| Reject Codes | [102] | [] |

### TC_EDGE_LARGE_PAYMENT

**Description:** Large payment (positive amount) should be posted and increase credit

| Metric | Expected | Actual |
|--------|----------|--------|
| Transactions Read | 1 | 1 |
| Transactions Posted | 1 | 0 |
| Transactions Rejected | 0 | 1 |
| Reject Codes | [] | [102] |

### TC_BATCH_MIXED_RESULTS

**Description:** Batch with mix of valid and invalid transactions

| Metric | Expected | Actual |
|--------|----------|--------|
| Transactions Read | 5 | 5 |
| Transactions Posted | 2 | 3 |
| Transactions Rejected | 3 | 2 |
| Reject Codes | [100, 102, 103] | [100, 103] |

### TC_SPECIAL_ALL_REJECTED

**Description:** All transactions rejected - no updates should occur

| Metric | Expected | Actual |
|--------|----------|--------|
| Transactions Read | 3 | 3 |
| Transactions Posted | 0 | 3 |
| Transactions Rejected | 3 | 0 |
| Reject Codes | [102, 102, 102] | [] |
