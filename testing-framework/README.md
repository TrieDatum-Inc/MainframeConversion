# CBTRN02C Migration Testing Framework

A comprehensive Python testing framework for validating the migration of mainframe COBOL batch program CBTRN02C (Post Daily Transactions) to Databricks/Spark.

## Overview

This framework enables you to test both the original COBOL program and the migrated Spark pipeline using the same golden datasets, ensuring exact functional equivalence.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TESTING WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Test Vectors ──► Generate Files ──┬──► COBOL (GnuCOBOL) ──┐        │
│  (Python)         (COBOL + CSV)    │                        │        │
│                                    │                        ├──► Compare
│                                    │                        │        │
│                                    └──► Spark (PySpark) ───┘        │
│                                                                      │
│                                    ──► Validation Report            │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

- **10 Test Scenarios** covering all validation paths:
  - Valid transactions
  - Invalid card number (reject code 100)
  - Account not found (reject code 101)
  - Overlimit transactions (reject code 102)
  - Expired accounts (reject code 103)
  - Multiple transactions for same account (sequential processing)
  - Credit/payment transactions
  - Edge cases (exact limit, zero amount)

- **Dual Execution Mode**: Run tests against both COBOL and Spark
- **Golden Dataset Generation**: Deterministic test data for reproducibility
- **Field-by-Field Comparison**: Validates exact matching of outputs
- **Detailed Reports**: Comprehensive validation reports

## Prerequisites

### For COBOL Testing (Optional but Recommended)
```bash
# Install GnuCOBOL on Ubuntu/Debian
sudo apt-get install gnucobol

# Verify installation
cobc --version
```

### For Spark Testing
```bash
# Install PySpark
pip install pyspark

# Optional: Install Delta Lake for full Databricks compatibility
pip install delta-spark
```

## Directory Structure

```
testing-framework/
├── run_tests.py              # Main test runner
├── README.md                 # This file
├── test_data/
│   └── test_vectors.py       # Test case definitions
├── utils/
│   ├── file_generators.py    # Generates test input files
│   └── comparator.py         # Compares COBOL vs Spark outputs
├── cobol_runner/
│   └── run_cobol.py          # Executes CBTRN02C via GnuCOBOL
├── spark_runner/
│   └── run_spark.py          # Executes Spark pipeline
└── golden_datasets/          # Generated test data (created at runtime)
    ├── TC001_VALID_TRANSACTION/
    │   ├── cobol/            # COBOL input/output files
    │   ├── spark/            # CSV files for Spark
    │   └── expected/         # Expected results
    ├── TC002_INVALID_CARD/
    └── ...
```

## Quick Start

### 1. Generate Test Data Only
```bash
python run_tests.py --generate-only
```

### 2. Run All Tests (COBOL + Spark)
```bash
python run_tests.py
```

### 3. Run Spark Tests Only (No COBOL Required)
```bash
python run_tests.py --spark-only
```

### 4. Run Specific Test
```bash
python run_tests.py --test TC001_VALID_TRANSACTION
```

### 5. Run COBOL Tests Only
```bash
python run_tests.py --cobol-only
```

## Test Cases

| Test ID | Description | Expected Outcome |
|---------|-------------|------------------|
| TC001_VALID_TRANSACTION | Single valid transaction | 1 posted, 0 rejected |
| TC002_INVALID_CARD | Card not in XREFFILE | 0 posted, 1 rejected (code 100) |
| TC003_ACCOUNT_NOT_FOUND | Account not in ACCTFILE | 0 posted, 1 rejected (code 101) |
| TC004_OVERLIMIT | Transaction exceeds credit limit | 0 posted, 1 rejected (code 102) |
| TC005_EXPIRED_ACCOUNT | Account past expiration date | 0 posted, 1 rejected (code 103) |
| TC006_MULTI_TRANS_SAME_ACCOUNT | Sequential processing test | 2 posted, 1 rejected |
| TC007_CREDIT_TRANSACTION | Payment/credit (positive amount) | 1 posted, 0 rejected |
| TC008_MIXED_TRANSACTIONS | Mix of valid and invalid | 2 posted, 2 rejected |
| TC009_EXACT_LIMIT | Balance exactly at limit | 1 posted, 0 rejected |
| TC010_ZERO_AMOUNT | Zero amount transaction | 1 posted, 0 rejected |
| TC_COMPREHENSIVE | All scenarios combined | Varies |

## Validation Logic (Matching COBOL Exactly)

The framework validates that Spark produces identical results to COBOL for:

### 1. Card Validation (Code 100)
```cobol
* COBOL: 1500-A-LOOKUP-XREF
READ XREF-FILE INTO CARD-XREF-RECORD
   INVALID KEY
     MOVE 100 TO WS-VALIDATION-FAIL-REASON
     MOVE 'INVALID CARD NUMBER FOUND' TO WS-VALIDATION-FAIL-REASON-DESC
```

### 2. Account Validation (Code 101)
```cobol
* COBOL: 1500-B-LOOKUP-ACCT
READ ACCOUNT-FILE INTO ACCOUNT-RECORD
   INVALID KEY
     MOVE 101 TO WS-VALIDATION-FAIL-REASON
     MOVE 'ACCOUNT RECORD NOT FOUND' TO WS-VALIDATION-FAIL-REASON-DESC
```

### 3. Overlimit Check (Code 102)
```cobol
* COBOL: Overlimit calculation
COMPUTE WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT
                    - ACCT-CURR-CYC-DEBIT
                    + DALYTRAN-AMT
IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL
   CONTINUE
ELSE
   MOVE 102 TO WS-VALIDATION-FAIL-REASON
   MOVE 'OVERLIMIT TRANSACTION' TO WS-VALIDATION-FAIL-REASON-DESC
```

### 4. Expiration Check (Code 103)
```cobol
* COBOL: Expiration check
IF ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS (1:10)
   CONTINUE
ELSE
   MOVE 103 TO WS-VALIDATION-FAIL-REASON
   MOVE 'TRANSACTION RECEIVED AFTER ACCT EXPIRATION' TO WS-VALIDATION-FAIL-REASON-DESC
```

## Sequential Processing

**Important**: COBOL processes transactions sequentially, updating account balances after each valid transaction. This means:

- Transaction 1 for Account A: Balance updated
- Transaction 2 for Account A: Validated against NEW balance
- Transaction 3 for Account A: Validated against NEWER balance

The Spark runner replicates this sequential behavior to ensure exact matching. Test case TC006 specifically validates this behavior.

## Output Files

### COBOL Output Files
- `TRANFILE.dat` - Posted transactions (350 bytes/record)
- `DALYREJS.dat` - Rejected transactions (430 bytes/record)
- `ACCTFILE.dat` - Updated account balances
- `TCATBALF.dat` - Updated transaction category balances

### Spark Output Files
- `posted_transactions.json` - Posted transactions
- `rejected_transactions.json` - Rejected transactions
- `summary.json` - Execution summary

### Comparison Report
- `test_report.txt` - Detailed comparison results

## Example Output

```
============================================================
CBTRN02C MIGRATION TESTING FRAMEWORK
============================================================
Timestamp: 2025-01-15T10:30:00

Prerequisites:
  GnuCOBOL: Available
  PySpark: Available

============================================================
GENERATING TEST DATA
============================================================
Generated test files for TC001_VALID_TRANSACTION in golden_datasets/TC001_VALID_TRANSACTION
...

============================================================
RUNNING COBOL TESTS
============================================================
COBOL compiled successfully

Running COBOL test: TC001_VALID_TRANSACTION
  Processed: 1
  Rejected: 0
  Success: True
...

============================================================
RUNNING SPARK TESTS
============================================================

Running Spark test: TC001_VALID_TRANSACTION
  Processed: 1
  Written: 1
  Rejected: 0
  Success: True
...

============================================================
COMPARING RESULTS
============================================================

Comparing TC001_VALID_TRANSACTION: COBOL vs Spark
  Status: PASSED
  Checks: 6/6 passed
...

============================================================
FINAL SUMMARY
============================================================
Total Tests: 11
Passed: 11
Failed: 0

All tests passed!
```

## Extending the Framework

### Adding New Test Cases

1. Edit `test_data/test_vectors.py`
2. Add a new `TestVector` in `create_golden_test_vectors()`
3. Define accounts, card_xrefs, and daily_transactions
4. Set expected outcomes

Example:
```python
tv_new = TestVector(
    name="TC011_NEW_SCENARIO",
    description="Description of new test case"
)
tv_new.accounts = [
    AccountRecord(acct_id="00000000012", ...)
]
tv_new.card_xrefs = [
    CardXrefRecord(card_num="4120000000000000", ...)
]
tv_new.daily_transactions = [
    DailyTransaction(
        tran_id="TRN0000000000016",
        ...,
        expected_valid=True  # or False with reject code
    )
]
tv_new.expected_records_read = 1
tv_new.expected_records_written = 1
tv_new.expected_records_rejected = 0
test_vectors.append(tv_new)
```

### Customizing Comparison

Edit `utils/comparator.py` to add custom comparison logic or adjust tolerance levels.

## Troubleshooting

### GnuCOBOL Compilation Errors
```bash
# Check COBOL source and copybooks are accessible
ls /home/ubuntu/repos/MainframeConversion/app/cbl/CBTRN02C.cbl
ls /home/ubuntu/repos/MainframeConversion/app/cpy/

# Try manual compilation
cobc -x -I ../app/cpy ../app/cbl/CBTRN02C.cbl -o cbtrn02c
```

### PySpark Errors
```bash
# Ensure Java is installed
java -version

# Install PySpark
pip install pyspark
```

### File Format Issues
- COBOL files use fixed-length records
- Ensure no extra newlines or encoding issues
- Check record lengths match copybook definitions

## Integration with Databricks

To run the Spark tests on Databricks instead of locally:

1. Upload test CSV files to DBFS
2. Modify `spark_runner/run_spark.py` to use Databricks paths
3. Use Databricks Connect or submit as a job

## License

This testing framework is part of the CardDemo mainframe modernization project.
