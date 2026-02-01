# CBTRN02C - Databricks Community Edition Migration

This folder contains the migrated CBTRN02C (Post Daily Transactions) PySpark job optimized for **Databricks Community Edition**.

## Overview

CBTRN02C is a batch program that:
1. Reads daily transactions from the DALYTRAN table
2. Validates each transaction against 4 business rules
3. Posts valid transactions to the TRANSACTIONS table
4. Updates account balances in the ACCOUNTS table
5. Updates transaction category balances
6. Writes rejected transactions with reason codes

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CBTRN02C - Post Daily Transactions                       │
│                         (PySpark / Databricks Migration)                        │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │  Shell Script   │
                              │ run_cbtrn02c.sh │
                              │                 │
                              │ --batch-id      │
                              │ --database      │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  spark-submit   │
                              │       or        │
                              │ Notebook %run   │
                              └────────┬────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            cbtrn02c_job.py (PySpark)                             │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                         1. READ DAILY TRANSACTIONS                         │  │
│  │                                                                            │  │
│  │   SELECT * FROM dalytran WHERE batch_id = :batch_id                        │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                          │
│                                       ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                         2. VALIDATION PIPELINE                             │  │
│  │                                                                            │  │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │  │
│  │   │  CARD_XREF   │    │   ACCOUNTS   │    │   Window     │                 │  │
│  │   │    Lookup    │───▶│    Lookup    │───▶│  Functions   │                 │  │
│  │   │              │    │              │    │  (Running    │                 │  │
│  │   │ Code 100:    │    │ Code 101:    │    │   Balance)   │                 │  │
│  │   │ Invalid Card │    │ Acct Not     │    │              │                 │  │
│  │   └──────────────┘    │ Found        │    │ Code 102:    │                 │  │
│  │                       │              │    │ Overlimit    │                 │  │
│  │                       │ Code 103:    │    │              │                 │  │
│  │                       │ Expired      │    └──────────────┘                 │  │
│  │                       └──────────────┘                                     │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                          │
│                    ┌──────────────────┴──────────────────┐                       │
│                    │                                     │                       │
│                    ▼                                     ▼                       │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────────┐   │
│  │      VALID TRANSACTIONS         │   │      REJECTED TRANSACTIONS          │   │
│  │                                 │   │                                     │   │
│  │  3a. MERGE INTO transactions    │   │  3b. INSERT INTO transaction_rejects│   │
│  │  3c. MERGE INTO accounts        │   │      - tran_id                      │   │
│  │      (update balances)          │   │      - reject_reason_code           │   │
│  │  3d. MERGE INTO tran_cat_balance│   │      - reject_reason_desc           │   │
│  └─────────────────────────────────┘   └─────────────────────────────────────┘   │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                         4. RETURN STATISTICS                               │  │
│  │                                                                            │  │
│  │   { "transactions_read": N, "transactions_written": M,                     │  │
│  │     "transactions_rejected": R, "return_code": 0|4|1 }                     │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘

                              DATA FLOW DIAGRAM
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   INPUT TABLES                    REFERENCE TABLES              OUTPUT TABLES   │
│   ────────────                    ────────────────              ─────────────   │
│                                                                                 │
│   ┌───────────┐                   ┌───────────────┐            ┌─────────────┐  │
│   │  DALYTRAN │                   │   CARD_XREF   │            │TRANSACTIONS │  │
│   │  (Bronze) │                   │               │            │   (Gold)    │  │
│   │           │                   │ card_num (PK) │            │             │  │
│   │ Daily     │──────┬───────────▶│ acct_id (FK)  │            │ Posted      │  │
│   │ Batch     │      │            └───────────────┘            │ Records     │  │
│   │ Input     │      │                    │                    └─────────────┘  │
│   └───────────┘      │                    │                           ▲         │
│                      │                    ▼                           │         │
│                      │            ┌───────────────┐                   │         │
│                      │            │   ACCOUNTS    │───────────────────┤         │
│                      │            │               │   (balance        │         │
│                      │            │ acct_id (PK)  │    updates)       │         │
│                      │            │ credit_limit  │                   │         │
│                      │            │ curr_bal      │            ┌─────────────┐  │
│                      │            │ expiration_dt │            │TRAN_CAT_BAL │  │
│                      │            └───────────────┘            │   (Gold)    │  │
│                      │                                         │             │  │
│                      │                                         │ Category    │  │
│                      │                                         │ Balances    │  │
│                      │                                         └─────────────┘  │
│                      │                                                          │
│                      │                                         ┌─────────────┐  │
│                      └────────────────────────────────────────▶│  REJECTS    │  │
│                           (invalid transactions)               │   (Gold)    │  │
│                                                                │             │  │
│                                                                │ Code 100-103│  │
│                                                                └─────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                         SEQUENTIAL PROCESSING LOGIC
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  Window Function for Running Balance (matches COBOL sequential behavior):      │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  window_spec = Window.partitionBy("acct_id")                            │    │
│  │                      .orderBy("tran_id")                                │    │
│  │                      .rowsBetween(unboundedPreceding, currentRow)       │    │
│  │                                                                         │    │
│  │  running_balance = curr_cyc_credit - curr_cyc_debit + SUM(tran_amt)     │    │
│  │                                                                         │    │
│  │  IF running_balance > credit_limit THEN reject (code 102)               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
│  Example: Account A001 with credit_limit = $1000, curr_bal = $800               │
│                                                                                 │
│  Transaction 1: -$100  → running_bal = $900  → PASS (under limit)               │
│  Transaction 2: -$150  → running_bal = $1050 → REJECT (overlimit)               │
│  Transaction 3: -$50   → running_bal = $1100 → REJECT (overlimit)               │
│                                                                                 │
│  Note: Each transaction's result affects subsequent validations                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `cbtrn02c_job.py` | Main PySpark job - can be run via spark-submit or notebook |
| `run_cbtrn02c.sh` | Shell script wrapper for command-line execution |
| `setup_tables.sql` | One-time SQL to create Delta tables |
| `load_sample_data.sql` | Sample data for testing |

## Deployment Steps

### Step 1: Sign Up for Databricks Community Edition

1. Go to https://community.cloud.databricks.com/login.html
2. Click "Sign Up" and select **Community Edition** (not the trial)
3. Complete registration and verify your email

### Step 2: Create a Cluster

1. In the left sidebar, click **Compute**
2. Click **Create Cluster**
3. Configure:
   - Name: `cbtrn02c-cluster`
   - Runtime: Latest LTS (e.g., 13.3 LTS or 14.3 LTS)
4. Click **Create Cluster** and wait for it to start (green circle)

### Step 3: Create Tables (One-Time Setup)

1. In the left sidebar, click **Workspace**
2. Navigate to your user folder
3. Create a new **Notebook** named `Setup_Tables`
4. Set language to **SQL**
5. Copy the contents of `setup_tables.sql` into the notebook
6. Run each cell to create the tables

### Step 4: Load Sample Data (Optional)

1. Create another notebook named `Load_Sample_Data`
2. Copy the contents of `load_sample_data.sql`
3. Run each cell to load test data

### Step 5: Upload the Job Script

1. In the left sidebar, click **Workspace**
2. Navigate to your user folder
3. Right-click and select **Import**
4. Upload `cbtrn02c_job.py`

### Step 6: Run the Job

**Option A: Run from Notebook**

Create a new Python notebook and run:

```python
# Set the batch ID (must match data in dalytran table)
batch_id = "20260115120000"
database = "carddemo"

# Run the job
%run /Workspace/Users/your-email/cbtrn02c_job $batch_id $database
```

Or copy the entire `cbtrn02c_job.py` content into a notebook and run:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
spark.sql("USE carddemo")

job = CBTRN02CJob(
    spark=spark,
    database="carddemo",
    batch_id="20260115120000"
)

stats = job.run()
print(stats)
```

**Option B: Run via Shell (if spark-submit available)**

```bash
./run_cbtrn02c.sh --batch-id 20260115120000 --database carddemo
```

### Step 7: Verify Results

Run these SQL queries in a notebook to verify:

```sql
-- Check posted transactions
SELECT * FROM carddemo.transactions;

-- Check rejected transactions
SELECT tran_id, reject_reason_code, reject_reason_desc 
FROM carddemo.transaction_rejects;

-- Check updated account balances
SELECT acct_id, curr_bal, curr_cyc_credit, curr_cyc_debit 
FROM carddemo.accounts;

-- Reconciliation summary
SELECT 'Transactions Read' as metric, COUNT(*) as count 
FROM carddemo.dalytran WHERE batch_id = '20260115120000'
UNION ALL
SELECT 'Transactions Posted', COUNT(*) FROM carddemo.transactions
UNION ALL
SELECT 'Transactions Rejected', COUNT(*) FROM carddemo.transaction_rejects;
```

## Expected Results (with sample data)

| Metric | Count |
|--------|-------|
| Transactions Read | 5 |
| Transactions Posted | 3 |
| Transactions Rejected | 2 |

**Posted Transactions:**
- TRN0000000000001: Grocery purchase (-$45.67)
- TRN0000000000002: Amazon purchase (-$129.99)
- TRN0000000000003: Payment received (+$500.00)

**Rejected Transactions:**
- TRN0000000000004: Code 100 - Invalid card number
- TRN0000000000005: Code 103 - Expired account

## Validation Rules

| Code | Description | COBOL Paragraph |
|------|-------------|-----------------|
| 100 | INVALID CARD NUMBER FOUND | 1500-A-LOOKUP-XREF |
| 101 | ACCOUNT RECORD NOT FOUND | 1500-B-LOOKUP-ACCT |
| 102 | OVERLIMIT TRANSACTION | 1500-B-LOOKUP-ACCT |
| 103 | TRANSACTION RECEIVED AFTER ACCT EXPIRATION | 1500-B-LOOKUP-ACCT |

## Overlimit Formula

The overlimit check uses the exact COBOL formula:

```
WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL → PASS
```

This implementation uses window functions to process transactions sequentially within each account, matching COBOL's behavior where balance updates affect subsequent validations.

## Return Codes

| Code | Meaning |
|------|---------|
| 0 | Success - all transactions processed |
| 4 | Warning - some transactions rejected |
| 1 | Error - job failed |

## Limitations (Databricks Community Edition)

1. **No Unity Catalog** - Uses `database.table` naming instead of `catalog.schema.table`
2. **No Job Scheduling** - Must run manually from notebooks
3. **Auto-termination** - Clusters stop after 2 hours of inactivity
4. **Single Cluster** - Only one cluster can run at a time
5. **Limited Storage** - Small DBFS quota

## Loading Real Data

To load actual mainframe data:

1. **Export from mainframe** - Use IDCAMS REPRO to create sequential files
2. **Convert EBCDIC to ASCII** - Use the `ebcdic_converter.py` in the parent folder
3. **Upload to DBFS** - Use Databricks UI or CLI
4. **Load into Delta** - Use COPY INTO or INSERT statements

Example:
```sql
COPY INTO carddemo.dalytran
FROM '/FileStore/uploads/dalytran.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');
```

## Troubleshooting

**"Table not found" error**
- Make sure you ran `setup_tables.sql` first
- Check you're using the correct database name

**"Cluster not responding"**
- Go to Compute and check if cluster is running
- Restart if terminated

**"No transactions to process"**
- Check the batch_id matches data in dalytran table
- Verify data was loaded with `SELECT * FROM carddemo.dalytran`

**Delta MERGE errors**
- Ensure Delta Lake is enabled (built into Databricks Runtime)
- Check table exists and has correct schema
