# CBTRN02C Test Results Report

**Generated:** 2026-02-01T14:57:40.961249
**Database:** carddemo_test

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 20 |
| Passed | 20 |
| Failed | 0 |
| Pass Rate | 100.0% |

## Results by Category

| Category | Passed | Failed | Pass Rate |
|----------|--------|--------|-----------|
| Validation Rules | 5 | 0 | 100.0% |
| Sequential Processing | 3 | 0 | 100.0% |
| Edge Cases | 5 | 0 | 100.0% |
| Batch Processing | 2 | 0 | 100.0% |
| Data Integrity | 2 | 0 | 100.0% |
| Special Scenarios | 3 | 0 | 100.0% |

## Detailed Results

| Test ID | Description | Status | Read | Posted | Rejected | Time (ms) |
|---------|-------------|--------|------|--------|----------|-----------|
| TC_100_INVALID_CARD | Transaction with card number not in XREF... | PASS | OK | OK | OK | 11315 |
| TC_101_ACCOUNT_NOT_FOUND | Transaction with valid card but account ... | PASS | OK | OK | OK | 11056 |
| TC_102_OVERLIMIT | Transaction that exceeds credit limit sh... | PASS | OK | OK | OK | 14544 |
| TC_103_EXPIRED | Transaction on expired account should be... | PASS | OK | OK | OK | 15521 |
| TC_VALID_TRANSACTION | Valid transaction should be posted succe... | PASS | OK | OK | OK | 29044 |
| TC_SEQ_MULTI_TRANS_SAME_ACCOUNT | Multiple transactions on same account - ... | PASS | OK | OK | OK | 30340 |
| TC_SEQ_PAYMENT_THEN_PURCHASE | Payment followed by purchase - payment i... | PASS | OK | OK | OK | 36738 |
| TC_SEQ_CASCADING_OVERLIMIT | First overlimit causes all subsequent to... | PASS | OK | OK | OK | 27726 |
| TC_EDGE_EXACT_LIMIT | Transaction that brings balance exactly ... | PASS | OK | OK | OK | 41077 |
| TC_EDGE_ONE_CENT_OVER | Transaction that exceeds limit by $0.01 ... | PASS | OK | OK | OK | 34908 |
| TC_EDGE_ZERO_AMOUNT | Transaction with zero amount should be p... | PASS | OK | OK | OK | 51120 |
| TC_EDGE_EXPIRATION_SAME_DAY | Transaction on expiration date should PA... | PASS | OK | OK | OK | 51590 |
| TC_EDGE_LARGE_PAYMENT | Large payment (positive amount) should b... | PASS | OK | OK | OK | 59620 |
| TC_BATCH_MULTI_ACCOUNT | Multiple transactions across multiple ac... | PASS | OK | OK | OK | 60263 |
| TC_BATCH_MIXED_RESULTS | Batch with mix of valid and invalid tran... | PASS | OK | OK | OK | 69438 |
| TC_INTEGRITY_BALANCE_UPDATE | Verify account balance fields are update... | PASS | OK | OK | OK | 70025 |
| TC_INTEGRITY_CATEGORY_BALANCE | Verify transaction category balances are... | PASS | OK | OK | OK | 77937 |
| TC_SPECIAL_EMPTY_BATCH | Empty batch (no transactions) should com... | PASS | OK | OK | OK | 41605 |
| TC_SPECIAL_ALL_REJECTED | All transactions rejected - no updates s... | PASS | OK | OK | OK | 60576 |
| TC_SPECIAL_VALIDATION_PRIORITY | Verify validation order: 100 -> 101 -> 1... | PASS | OK | OK | OK | 33235 |
