# CBTRN02C PySpark Migration

PySpark migration of the COBOL batch program **CBTRN02C** (Post Daily Transactions) targeting **Databricks Delta Lake** as the data layer.

| Attribute | Value |
|---|---|
| Original COBOL | `app/cbl/CBTRN02C.cbl` |
| Original JCL | `app/jcl/POSTTRAN.jcl` |
| Migrated PySpark | `cbtrn02c_post_daily_transactions.py` |
| Schema | `carddemo` |

---

## Business Logic

CBTRN02C reads daily credit card transactions and processes them through a validation pipeline. Valid transactions are posted to the transaction master, account balances are updated, and transaction category balances are maintained. Invalid transactions are written to a rejects file with a reason code.

### Validation Rules

Each daily transaction is validated in this order (first failure wins):

| Code | Rule | COBOL Paragraph |
|---|---|---|
| 100 | Card number not found in cross-reference file | `1500-A-LOOKUP-XREF` |
| 101 | Account record not found for the cross-referenced account ID | `1500-B-LOOKUP-ACCT` |
| 102 | Transaction would exceed account credit limit (overlimit) | `1500-VALIDATE-TRAN` |
| 103 | Transaction dated after account expiration date | `1500-VALIDATE-TRAN` |

### Processing Steps

| Step | Description | COBOL Paragraph |
|---|---|---|
| Validate | Apply the 4 validation rules above, split into valid and rejected sets | `1500-VALIDATE-TRAN` |
| Post | Map daily transaction fields to transaction master layout, append to `transaction` table | `2000-POST-TRANSACTION` |
| Update account | Add transaction amount to `acct_curr_bal`; positive amounts add to `acct_curr_cyc_credit`, negative to `acct_curr_cyc_debit` | `2800-UPDATE-ACCOUNT-REC` |
| Update category balance | MERGE into `tran_cat_balance` keyed by (acct_id, type_cd, cat_cd); update existing or insert new | `2700-UPDATE-TCATBAL` |
| Write rejects | Append rejected transactions with reason code and description to `daily_rejects` table | `2500-WRITE-REJECT-REC` |

---

## Data Model

### COBOL Copybook to Delta Table Mapping

| Delta Table | Copybook | VSAM File | Role |
|---|---|---|---|
| `carddemo.daily_transaction` | CVTRA06Y | DALYTRAN | Input: daily transactions to process |
| `carddemo.card_xref` | CVACT03Y | CCXREF | Input: card-to-account cross-reference |
| `carddemo.account` | CVACT01Y | ACCTDAT | Input/Output: account master (balances updated) |
| `carddemo.transaction` | CVTRA05Y | TRANSACT | Output: posted transaction master |
| `carddemo.tran_cat_balance` | CVTRA01Y | TCATBALF | Input/Output: category balance aggregation |
| `carddemo.daily_rejects` | (working storage) | DALYREJS | Output: rejected transactions |

### COBOL to Spark SQL Type Mapping

| COBOL PIC Clause | Spark SQL Type | Example Field |
|---|---|---|
| `PIC X(16)` | `STRING` | `dalytran_card_num` |
| `PIC 9(11)` | `BIGINT` | `acct_id` |
| `PIC S9(09)V99` | `DECIMAL(11,2)` | `dalytran_amt` |
| `PIC 9(04)` | `INT` | `dalytran_cat_cd` |
| `PIC X(01)` | `STRING` | `acct_active_status` |

---

## File Structure

```
migration/cbtrn02c/
├── 01_ddl_setup.sql                          # Delta table DDL
├── 02_sample_data.sql                        # Sample data with test scenarios
├── cbtrn02c_post_daily_transactions.py       # PySpark pipeline
├── README.md                                 # This file
└── test/
    ├── __init__.py
    ├── conftest.py                           # Fixtures, helpers, schemas
    ├── test_validation.py                    # Reject codes 100-103
    ├── test_post_transaction.py              # Transaction posting
    ├── test_account_update.py                # Account balance MERGE
    ├── test_tran_cat_balance.py              # Category balance MERGE
    ├── test_write_rejects.py                 # Reject output
    ├── test_end_to_end.py                    # Full pipeline integration
    └── test_edge_cases.py                    # Boundary/corner cases
```

---

## Running the Pipeline

### Prerequisites

- Databricks workspace with Unity Catalog (for PRIMARY KEY constraints) or remove constraints from DDL
- PySpark 3.3+ with Delta Lake 2.0+
- Python 3.9+

### Step 1: Create Delta Tables

Run the DDL script in a Databricks SQL notebook or via `spark.sql()`:

```sql
-- In Databricks SQL editor or notebook
-- Execute the contents of 01_ddl_setup.sql

CREATE SCHEMA IF NOT EXISTS carddemo;

CREATE TABLE IF NOT EXISTS carddemo.daily_transaction ( ... ) USING DELTA;
-- (see 01_ddl_setup.sql for full DDL)
```

If you are **not** using Unity Catalog, remove the `CONSTRAINT pk_...` lines from the DDL before running.

### Step 2: Load Input Data

Load your daily transaction data into `carddemo.daily_transaction`. For initial testing, use the sample data script:

```sql
-- Execute the contents of 02_sample_data.sql
-- This loads 5 accounts, 5 card cross-references, 5 category balances,
-- and 10 daily transactions (7 valid, 3 rejected)
```

In production, replace this step with your ETL pipeline that loads daily transaction data from the source system.

### Step 3: Execute the Pipeline

#### Option A: Databricks Notebook

```python
# In a Databricks notebook cell
%run ./cbtrn02c_post_daily_transactions
```

Or import and call `main()`:

```python
from cbtrn02c_post_daily_transactions import main
main()
```

#### Option B: Databricks Job

Configure a Databricks Job with:
- **Type**: Python script
- **Path**: `/path/to/cbtrn02c_post_daily_transactions.py`
- **Cluster**: Any cluster with Delta Lake support

#### Option C: spark-submit (local/cluster)

```bash
spark-submit \
  --packages io.delta:delta-spark_2.12:3.1.0 \
  cbtrn02c_post_daily_transactions.py
```

### Step 4: Verify Results

```sql
-- Check posted transactions
SELECT COUNT(*) FROM carddemo.transaction;

-- Check rejected transactions
SELECT reject_reason_code, reject_reason_desc, COUNT(*)
FROM carddemo.daily_rejects
GROUP BY reject_reason_code, reject_reason_desc;

-- Check updated account balances
SELECT acct_id, acct_curr_bal, acct_curr_cyc_credit, acct_curr_cyc_debit
FROM carddemo.account;

-- Check category balances
SELECT * FROM carddemo.tran_cat_balance ORDER BY trancat_acct_id, trancat_type_cd, trancat_cd;
```

### Expected Results with Sample Data

After running the pipeline with the sample data from `02_sample_data.sql`:

| Metric | Count |
|---|---|
| Total input transactions | 10 |
| Transactions posted | 7 |
| Transactions rejected | 3 |

Rejected transactions:

| Transaction ID | Reject Code | Reason |
|---|---|---|
| TXN0000000000004 | 100 | Card number `9999999999999999` not in cross-reference |
| TXN0000000000005 | 102 | Account `80000000003` would exceed credit limit of 9,000 |
| TXN0000000000006 | 103 | Account `80000000004` expired on 2025-06-30 |

---

## Running the Test Framework

### Prerequisites

Install test dependencies:

```bash
pip install pytest pyspark delta-spark
```

### Run All Tests

```bash
cd migration/cbtrn02c
pytest test/ -v
```

### Run Specific Test Modules

```bash
# Validation logic only
pytest test/test_validation.py -v

# Account balance updates only
pytest test/test_account_update.py -v

# End-to-end integration tests
pytest test/test_end_to_end.py -v

# Edge cases and boundary conditions
pytest test/test_edge_cases.py -v
```

### Run by Test Class

```bash
# All overlimit rejection tests
pytest test/test_validation.py::TestReject102Overlimit -v

# All boundary amount tests
pytest test/test_edge_cases.py::TestBoundaryAmounts -v
```

### Test Coverage Summary

| Module | Tests | Coverage Area |
|---|---|---|
| `test_validation.py` | 11 | All 4 reject codes, validation priority, empty XREF, partial card match |
| `test_post_transaction.py` | 5 | Field mapping, refunds, zero amounts, multiple postings |
| `test_account_update.py` | 9 | Balance/credit/debit splits, multi-account, zero-amount, decimal precision |
| `test_tran_cat_balance.py` | 10 | MERGE insert/update, multi-category, refund reduction, cross-account independence |
| `test_write_rejects.py` | 8 | All reject codes with reasons, field preservation, timestamps, no-reject case |
| `test_end_to_end.py` | 6 | Full pipeline, sample-data regression, pre-existing data, empty input |
| `test_edge_cases.py` | 14 | Boundary amounts, date boundaries, multi-card accounts, null fields, duplicate IDs, volume |
| **Total** | **63** | |

### Test Architecture

- **Isolation**: Each test function gets clean Delta tables via the `clean_tables` fixture
- **Schema**: Tests use a separate `carddemo_test` schema, not production `carddemo`
- **SparkSession**: A single session-scoped SparkSession is shared across all tests
- **Helpers**: `conftest.py` provides builder functions (`make_daily_tran`, `make_xref`, `make_account`, `make_tran_cat_bal`) for concise test data construction
- **Schema patching**: Tests temporarily override the `SCHEMA` module variable to route writes to the test schema

---

## Design Decisions

### Sequential Processing in a Distributed Engine

The original COBOL program processes transactions one at a time. When transaction N is posted, the account balance is updated before transaction N+1 is validated. This matters for overlimit checks where cumulative spending across a day may exceed the credit limit.

The PySpark migration uses **window functions** with `PARTITION BY acct_id ORDER BY dalytran_orig_ts, dalytran_id` to compute a running sum of transaction amounts. This running sum is added to the existing cycle credit/debit to determine whether each transaction would push the account over its credit limit.

### Delta MERGE for Upserts

Account balance updates and transaction category balance updates use Delta Lake's `MERGE` operation:
- **Account**: `WHEN MATCHED UPDATE` adds the aggregated deltas to existing balances
- **Category balance**: `WHEN MATCHED UPDATE` adds the delta; `WHEN NOT MATCHED INSERT` creates a new row

### Idempotency

The `post_transactions` function uses `.mode("append")`, which means re-running the pipeline on the same daily data will create duplicate transaction records. For production use, consider:
- Adding deduplication logic using `MERGE` on `tran_id`
- Clearing `daily_transaction` after successful processing
- Using a processed-flag or watermark column

---

## Traceability to Original COBOL

| PySpark Function | COBOL Paragraph(s) |
|---|---|
| `validate_and_split()` | `1500-VALIDATE-TRAN`, `1500-A-LOOKUP-XREF`, `1500-B-LOOKUP-ACCT` |
| `post_transactions()` | `2000-POST-TRANSACTION`, `2900-WRITE-TRANSACTION-FILE` |
| `update_account_balances()` | `2800-UPDATE-ACCOUNT-REC` |
| `update_tran_cat_balance()` | `2700-UPDATE-TCATBAL`, `2700-A-CREATE-TCATBAL-REC`, `2700-B-UPDATE-TCATBAL-REC` |
| `write_rejects()` | `2500-WRITE-REJECT-REC` |
| `main()` | `0000-MAIN`, `1000-DALYTRAN-GET-NEXT` |
