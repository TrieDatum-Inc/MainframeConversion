# CBTRN02C Testing Framework

Comprehensive testing framework for validating the CBTRN02C PySpark migration against the original COBOL program behavior.

## Overview

This testing framework provides:
- **20 test cases** covering all validation rules and edge cases
- **Test data generators** for creating isolated test environments
- **Automated test runner** with detailed reporting
- **Expected results documentation** for manual verification

## Test Categories

### 1. Validation Rules (5 tests)

Tests for each rejection code matching COBOL behavior:

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| TC_100_INVALID_CARD | Card number not in XREFFILE | Reject code 100 |
| TC_101_ACCOUNT_NOT_FOUND | Valid card but account missing | Reject code 101 |
| TC_102_OVERLIMIT | Transaction exceeds credit limit | Reject code 102 |
| TC_103_EXPIRED | Transaction on expired account | Reject code 103 |
| TC_VALID_TRANSACTION | All validations pass | Posted successfully |

### 2. Sequential Processing (3 tests)

Critical tests for COBOL's sequential processing behavior:

| Test ID | Description | Why It Matters |
|---------|-------------|----------------|
| TC_SEQ_MULTI_TRANS_SAME_ACCOUNT | Multiple transactions on same account | Tests running balance calculation |
| TC_SEQ_PAYMENT_THEN_PURCHASE | Payment followed by purchase | Tests credit increase affects subsequent |
| TC_SEQ_CASCADING_OVERLIMIT | First overlimit causes cascade | Tests sequential rejection behavior |

### 3. Edge Cases (5 tests)

Boundary condition tests:

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| TC_EDGE_EXACT_LIMIT | Balance exactly equals limit | PASS (>= not >) |
| TC_EDGE_ONE_CENT_OVER | Balance exceeds limit by $0.01 | FAIL (code 102) |
| TC_EDGE_ZERO_AMOUNT | Zero amount transaction | PASS |
| TC_EDGE_EXPIRATION_SAME_DAY | Transaction on expiration date | PASS (>= not >) |
| TC_EDGE_LARGE_PAYMENT | Large payment (positive amount) | PASS |

### 4. Batch Processing (2 tests)

Multi-account batch tests:

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| TC_BATCH_MULTI_ACCOUNT | 5 transactions across 3 accounts | All posted, balances correct |
| TC_BATCH_MIXED_RESULTS | Mix of valid and invalid | 2 posted, 3 rejected |

### 5. Data Integrity (2 tests)

Balance update verification:

| Test ID | Description | Verifies |
|---------|-------------|----------|
| TC_INTEGRITY_BALANCE_UPDATE | Purchase and payment | curr_bal, curr_cyc_credit, curr_cyc_debit |
| TC_INTEGRITY_CATEGORY_BALANCE | Multiple categories | tran_cat_balance table |

### 6. Special Scenarios (3 tests)

Edge case scenarios:

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| TC_SPECIAL_EMPTY_BATCH | No transactions | Success, no updates |
| TC_SPECIAL_ALL_REJECTED | All transactions invalid | No balance updates |
| TC_SPECIAL_VALIDATION_PRIORITY | Check validation order | 100 before 101 before 102 before 103 |

## Files

| File | Description |
|------|-------------|
| `test_cases.py` | All 20 test case definitions with expected results |
| `test_data_generator.py` | Generates SQL and DataFrames for test data |
| `run_tests.py` | Automated test runner with reporting |
| `README.md` | This documentation |

## Running Tests

### Option 1: In Databricks Notebook

```python
# Upload all test files to your Databricks workspace
# Then run in a notebook:

%run /Workspace/Users/your-email/tests/run_tests

# Or import and run programmatically:
from run_tests import CBTRN02CTestRunner
from test_cases import ALL_TEST_CASES

runner = CBTRN02CTestRunner(spark=spark, database="carddemo_test")
results = runner.run_all_tests()
print(runner.generate_report())
```

### Option 2: Via spark-submit (Local)

```bash
# Run all tests
spark-submit --packages io.delta:delta-spark_2.12:3.1.0 run_tests.py

# Run specific test
spark-submit --packages io.delta:delta-spark_2.12:3.1.0 run_tests.py --test-id TC_100_INVALID_CARD

# Run tests by category
spark-submit --packages io.delta:delta-spark_2.12:3.1.0 run_tests.py --category "Validation Rules"

# List all tests
python run_tests.py --list
```

### Option 3: Generate SQL for Manual Testing

```python
from test_data_generator import TestDataGenerator
from test_cases import ALL_TEST_CASES

generator = TestDataGenerator("carddemo_test")

# Generate SQL for all tests
generator.generate_all_test_sql("all_test_data.sql")

# Generate SQL for specific test
from test_cases import TC_100_INVALID_CARD
print(generator.generate_sql_for_test_case(TC_100_INVALID_CARD))

# Generate verification queries
print(generator.generate_verification_sql(TC_100_INVALID_CARD))
```

## Expected Results Summary

### Validation Rule Tests

```
TC_100_INVALID_CARD:     Read=1, Posted=0, Rejected=1 (code 100)
TC_101_ACCOUNT_NOT_FOUND: Read=1, Posted=0, Rejected=1 (code 101)
TC_102_OVERLIMIT:        Read=1, Posted=0, Rejected=1 (code 102)
TC_103_EXPIRED:          Read=1, Posted=0, Rejected=1 (code 103)
TC_VALID_TRANSACTION:    Read=1, Posted=1, Rejected=0
```

### Sequential Processing Tests

```
TC_SEQ_MULTI_TRANS_SAME_ACCOUNT:
  Input: 3 transactions on same account ($600, $300, $200)
  Account: credit_limit=$1000, starting_balance=$0
  Expected: 
    - TRN_SEQ_001 ($600): PASS, running_bal=$600
    - TRN_SEQ_002 ($300): PASS, running_bal=$900
    - TRN_SEQ_003 ($200): FAIL (code 102), running_bal would be $1100 > $1000
  Result: Read=3, Posted=2, Rejected=1

TC_SEQ_PAYMENT_THEN_PURCHASE:
  Input: Payment +$500, then Purchase -$400
  Account: credit_limit=$1000, curr_cyc_debit=$950 (only $50 available)
  Expected:
    - Payment: PASS, increases available credit
    - Purchase: PASS, now has room
  Result: Read=2, Posted=2, Rejected=0

TC_SEQ_CASCADING_OVERLIMIT:
  Input: 3 small transactions ($200, $50, $25)
  Account: credit_limit=$500, curr_cyc_debit=$400 (only $100 available)
  Expected: All rejected (running balance exceeds limit for each)
  Result: Read=3, Posted=0, Rejected=3 (all code 102)
```

### Edge Case Tests

```
TC_EDGE_EXACT_LIMIT:
  Account: credit_limit=$1000, curr_cyc_debit=$900
  Transaction: -$100 (would make balance exactly $1000)
  Expected: PASS (COBOL uses >= not >)
  Result: Read=1, Posted=1, Rejected=0

TC_EDGE_ONE_CENT_OVER:
  Account: credit_limit=$1000, curr_cyc_debit=$900
  Transaction: -$100.01 (would make balance $1000.01)
  Expected: FAIL (code 102)
  Result: Read=1, Posted=0, Rejected=1
```

## Validation Logic Reference

### COBOL Overlimit Formula

```cobol
* From CBTRN02C.cbl paragraph 1500-B-LOOKUP-ACCT
COMPUTE WS-TEMP-BAL = 
    ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT

IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL
    CONTINUE  (PASS)
ELSE
    MOVE 102 TO WS-REJECT-REASON  (FAIL - OVERLIMIT)
```

### PySpark Implementation

```python
# Window function for sequential processing
window_spec = Window.partitionBy("acct_id").orderBy("tran_id").rowsBetween(
    Window.unboundedPreceding, Window.currentRow
)

# Running balance calculation
running_tran_sum = F.sum("tran_amt").over(window_spec)
projected_balance = curr_cyc_credit - curr_cyc_debit + running_tran_sum

# Overlimit check (>= means equal is OK)
within_limit = credit_limit >= projected_balance
```

### Validation Order

The validations are checked in this order (first failure wins):

1. **Code 100**: Card number lookup in XREFFILE
2. **Code 101**: Account lookup in ACCTFILE
3. **Code 102**: Overlimit check
4. **Code 103**: Expiration date check

## Test Report Format

The test runner generates a markdown report with:

1. **Summary**: Total tests, passed, failed, pass rate
2. **Results by Category**: Breakdown by test category
3. **Detailed Results**: Table with all test results
4. **Failed Tests Details**: Detailed analysis of failures

Example output:

```
# CBTRN02C Test Results Report

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 20 |
| Passed | 18 |
| Failed | 2 |
| Pass Rate | 90.0% |

## Results by Category

| Category | Passed | Failed | Pass Rate |
|----------|--------|--------|-----------|
| Validation Rules | 5 | 0 | 100.0% |
| Sequential Processing | 2 | 1 | 66.7% |
| Edge Cases | 5 | 0 | 100.0% |
...
```

## Troubleshooting

### "Table not found" errors

Make sure the test runner has created the test tables:
```python
runner = CBTRN02CTestRunner(database="carddemo_test")
runner.setup_spark()
runner.setup_test_tables()
```

### Sequential processing tests failing

The key to matching COBOL behavior is the window function:
```python
Window.partitionBy("acct_id").orderBy("tran_id").rowsBetween(
    Window.unboundedPreceding, Window.currentRow
)
```

This ensures each transaction sees the cumulative effect of all previous transactions on the same account.

### Import errors

Make sure the parent directory is in the Python path:
```python
import sys
sys.path.insert(0, '/path/to/cbtrn02c-ce')
```

## Adding New Test Cases

To add a new test case:

1. Define the test in `test_cases.py`:

```python
TC_NEW_TEST = TestCase(
    test_id="TC_NEW_TEST",
    description="Description of what this tests",
    category="Category Name",
    accounts=[
        Account(acct_id="ACCT00001", credit_limit=Decimal("5000.00"))
    ],
    card_xrefs=[
        CardXref(card_num="4111111111111111", acct_id="ACCT00001")
    ],
    transactions=[
        DailyTransaction(
            tran_id="TRN_NEW_001",
            card_num="4111111111111111",
            tran_amt=Decimal("-100.00")
        )
    ],
    expected=ExpectedResult(
        transactions_read=1,
        transactions_posted=1,
        transactions_rejected=0,
        posted_tran_ids=["TRN_NEW_001"]
    ),
    notes="Explanation of the test"
)
```

2. Add to `ALL_TEST_CASES` list:

```python
ALL_TEST_CASES = [
    # ... existing tests ...
    TC_NEW_TEST,
]
```

3. Run the test:

```bash
python run_tests.py --test-id TC_NEW_TEST
```

## COBOL to PySpark Mapping

| COBOL Concept | PySpark Implementation |
|---------------|------------------------|
| Sequential file read | `spark.table().orderBy("tran_id")` |
| VSAM KSDS lookup | `DataFrame.join()` |
| Working storage balance | Window function running total |
| WRITE to file | `df.write.format("delta").mode("append")` |
| REWRITE record | Delta Lake MERGE |
| Condition codes | Return codes (0, 4, 1) |
