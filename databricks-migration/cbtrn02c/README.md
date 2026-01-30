# CBTRN02C Migration to Databricks

This POC migrates the mainframe COBOL batch program **CBTRN02C** (Post Daily Transactions) to Databricks using PySpark and Delta Lake.

## Overview

### Mainframe Program (Original)
- **Program**: `CBTRN02C.cbl`
- **JCL Job**: `POSTTRAN.jcl`
- **Function**: Posts daily transactions from DALYTRAN file to VSAM master files
- **Schedule**: Daily batch job (typically end-of-day)

### Databricks Migration (This POC)
- **PySpark Job**: `post_daily_transactions.py`
- **Airflow DAG**: `airflow_dag.py`
- **Storage**: Delta Lake tables in Unity Catalog
- **Schedule**: Airflow-orchestrated daily job

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAINFRAME (Original)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DALYTRAN ──► CBTRN02C.cbl ──► TRANFILE (VSAM)                              │
│  (Input)         │              TCATBALF (VSAM)                              │
│                  │              ACCTFILE (VSAM)                              │
│                  └──► DALYREJS (Rejects)                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABRICKS (Migrated)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  bronze.dalytran ──► post_daily_transactions.py ──► silver.transactions     │
│  (Delta Lake)              │                        silver.tran_cat_balance  │
│                            │                        silver.accounts          │
│                            └──► silver.transaction_rejects                   │
│                                                                              │
│  Orchestration: Airflow DAG (daily at 11 PM UTC)                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `schema_definitions.py` | Delta Lake table schemas based on COBOL copybooks |
| `ebcdic_converter.py` | EBCDIC to ASCII conversion for mainframe files |
| `post_daily_transactions.py` | Main PySpark job (CBTRN02C equivalent) |
| `setup_delta_tables.py` | Creates Unity Catalog tables and loads sample data |
| `airflow_dag.py` | Airflow DAG for scheduling the job |

## Data Flow

### Input: Daily Transactions (DALYTRAN)
- **Mainframe**: EBCDIC fixed-length file (350 bytes/record)
- **Databricks**: `bronze.dalytran` Delta table

### Processing: Validation Logic (Exact Match with COBOL)
1. **Validation 1** (Code 100): Card number exists in XREFFILE
2. **Validation 2** (Code 101): Account exists in ACCTFILE
3. **Validation 3** (Code 102): Transaction doesn't exceed credit limit
4. **Validation 4** (Code 103): Account is not expired

### Output: Multiple Tables Updated
- **Valid transactions** → `silver.transactions` (append)
- **Category balances** → `silver.tran_cat_balance` (MERGE/upsert)
- **Account balances** → `silver.accounts` (MERGE/update)
- **Rejected transactions** → `silver.transaction_rejects` (append)

## Validation Reason Codes

| Code | Description | COBOL Reference |
|------|-------------|-----------------|
| 100 | INVALID CARD NUMBER FOUND | 1600-LOOKUP-XREF |
| 101 | ACCOUNT RECORD NOT FOUND | 1700-LOOKUP-ACCOUNT |
| 102 | OVERLIMIT TRANSACTION | 1800-CHECK-OVERLIMIT |
| 103 | TRANSACTION RECEIVED AFTER ACCT EXPIRATION | 1900-CHECK-EXPIRATION |
| 109 | ACCOUNT RECORD NOT FOUND DURING UPDATE | 2800-UPDATE-ACCOUNT-REC |

## Setup Instructions

### 1. Prerequisites
- Databricks workspace with Unity Catalog enabled
- Airflow with Databricks provider installed
- Python 3.8+ with PySpark

### 2. Create Delta Tables

Run in a Databricks notebook:
```python
%run ./setup_delta_tables

# Or with custom catalog name:
from setup_delta_tables import setup_all
setup_all(spark, catalog="your_catalog", load_samples=True)
```

### 3. Deploy PySpark Job

Upload `post_daily_transactions.py` to DBFS:
```bash
databricks fs cp post_daily_transactions.py dbfs:/jobs/cbtrn02c/
```

### 4. Configure Airflow

1. Set up Databricks connection in Airflow:
   ```
   Connection ID: databricks_default
   Connection Type: Databricks
   Host: https://your-workspace.cloud.databricks.com
   Token: your-databricks-token
   ```

2. Set Airflow variables:
   ```
   databricks_cluster_id: your-cluster-id
   cbtrn02c_job_id: your-job-id (if using pre-configured job)
   ```

3. Deploy the DAG:
   ```bash
   cp airflow_dag.py $AIRFLOW_HOME/dags/
   ```

### 5. Run the Job

**Manual run (Databricks notebook):**
```python
from post_daily_transactions import CBTRN02CJob

job = CBTRN02CJob(
    spark=spark,
    catalog="carddemo",
    schema="silver",
    batch_id="20240115120000"
)
stats = job.run()
print(stats)
```

**Scheduled run (Airflow):**
The DAG runs daily at 11 PM UTC. Trigger manually:
```bash
airflow dags trigger carddemo_cbtrn02c_post_daily_transactions
```

## EBCDIC File Handling

For mainframe files in EBCDIC format:

```python
from ebcdic_converter import EBCDICFileReader
from schema_definitions import DALYTRAN_EBCDIC_LAYOUT, DALYTRAN_RECORD_LENGTH

reader = EBCDICFileReader(
    file_path="/path/to/DALYTRAN.dat",
    record_length=DALYTRAN_RECORD_LENGTH,
    layout=DALYTRAN_EBCDIC_LAYOUT
)

for record in reader.read_records():
    print(record)
```

## Idempotency

The job uses `batch_id` to ensure idempotent reruns:
- Each batch run has a unique `batch_id` (timestamp-based)
- Transactions are keyed by `(tran_id, batch_id)`
- MERGE operations prevent duplicate updates
- Rerunning the same batch_id will not double-post

## Reconciliation

The job produces reconciliation statistics matching mainframe control totals:
```
============================================
RECONCILIATION REPORT
============================================
Batch ID:          20240115120000
Records Read:      1000
Records Written:   985
Records Rejected:  15
============================================
```

Compare these with mainframe job output to validate migration.

## Testing

Sample data is loaded by `setup_delta_tables.py`:
- 5 sample accounts
- 5 sample card cross-references
- 5 sample daily transactions (3 valid, 2 will be rejected)

Run the job with batch_id `20240115120000` to process sample data.

## Mapping: COBOL to PySpark

| COBOL Section | PySpark Method |
|---------------|----------------|
| 1000-OPEN-FILES | `_read_daily_transactions()` |
| 1100-READ-DALYTRAN-FILE | `spark.table().filter()` |
| 1500-VALIDATE-TRANSACTION | `_validate_transactions()` |
| 1600-LOOKUP-XREF | `join(xref_df)` |
| 1700-LOOKUP-ACCOUNT | `join(accounts_df)` |
| 1800-CHECK-OVERLIMIT | `withColumn("validation_3_pass", ...)` |
| 1900-CHECK-EXPIRATION | `withColumn("validation_4_pass", ...)` |
| 2000-POST-TRANSACTION | `_post_transactions()` |
| 2500-WRITE-REJECT-REC | `_write_rejects()` |
| 2700-UPDATE-TCATBAL | `_update_tran_cat_balance()` |
| 2800-UPDATE-ACCOUNT-REC | `_update_account_balances()` |
| 2900-WRITE-TRANSACTION-FILE | `_write_transactions()` |
| 9000-DISPLAY-COUNTERS | `_generate_reconciliation_report()` |

## Next Steps

1. **Data Migration**: Migrate existing VSAM data to Delta tables
2. **Integration Testing**: Run parallel with mainframe and compare outputs
3. **Performance Tuning**: Optimize for production data volumes
4. **Monitoring**: Set up Databricks job monitoring and alerts
5. **Related Jobs**: Migrate INTCALC (interest) and CREASTMT (statements)
