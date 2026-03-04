# CardDemo Batch - PySpark Migration

Migrated from mainframe COBOL batch programs to PySpark jobs with Databricks Delta tables.

## Programs Migrated

| COBOL Program | PySpark Job | Description |
|---|---|---|
| CBTRN02C | `jobs/cbtrn02c_daily_transaction_posting.py` | Daily transaction posting with validation |
| CBACT04C | `jobs/cbact04c_interest_calculator.py` | Monthly interest calculation |
| CBTRN03C | `jobs/cbtrn03c_daily_transaction_report.py` | Daily transaction report (CSV output) |
| CBSTM03A | `jobs/cbstm03a_account_statement.py` | Account statement generator (CSV + HTML) |

## Folder Structure

```
carddemo-batch/
├── setup/
│   ├── create_delta_tables.sql   # Delta table DDL (13 tables)
│   └── seed_sample_data.sql      # Sample data for testing
├── jobs/
│   ├── cbtrn02c_daily_transaction_posting.py
│   ├── cbact04c_interest_calculator.py
│   ├── cbtrn03c_daily_transaction_report.py
│   └── cbstm03a_account_statement.py
├── utils/
│   ├── __init__.py
│   └── spark_utils.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Prerequisites

- Databricks workspace with Unity Catalog (or classic metastore)
- PySpark 3.5+ with Delta Lake 3.1+
- Python 3.9+

## Setup

### 1. Create Delta Tables

Run `setup/create_delta_tables.sql` in a Databricks SQL warehouse or notebook:

```sql
-- In Databricks notebook
%sql
-- Copy and run contents of setup/create_delta_tables.sql
```

### 2. Load Sample Data

Run `setup/seed_sample_data.sql` to populate tables with test data.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Jobs

All jobs accept optional `catalog` and `database` parameters. Default database is `carddemo`.

### CBTRN02C - Daily Transaction Posting

Reads daily_transaction, validates each record, posts valid transactions to the transaction table, writes rejects to daily_reject, and updates account balances and tran_cat_bal.

```bash
spark-submit jobs/cbtrn02c_daily_transaction_posting.py [catalog] [database]
```

**Validation rules (matching COBOL):**
- Reject 100: Card number not found in card_xref
- Reject 101: Account not found
- Reject 102: Transaction exceeds credit limit
- Reject 103: Account expired

**Return code:** 0 = all posted, 4 = some rejects

### CBACT04C - Interest Calculator

Reads tran_cat_bal, looks up interest rates from disclosure_group, computes monthly interest using `(balance * rate) / 1200`, writes interest transactions, and updates account balances.

```bash
spark-submit jobs/cbact04c_interest_calculator.py [parm_date] [catalog] [database]
```

**Parameters:**
- `parm_date`: Date stamp for interest transaction IDs (YYYY-MM-DD, default: today)

### CBTRN03C - Daily Transaction Report

Generates a transaction detail report filtered by date range with account totals and grand total.

```bash
spark-submit jobs/cbtrn03c_daily_transaction_report.py [start_date] [end_date] [output_path] [catalog] [database]
```

**Parameters:**
- `start_date`: Report start date (YYYY-MM-DD, default: today)
- `end_date`: Report end date (YYYY-MM-DD, default: start_date)
- `output_path`: Output directory (default: /tmp/carddemo_transaction_report_{dates})

**Output CSV files:**
- `detail/` - Transaction detail rows
- `account_totals/` - Per-account summary
- `grand_total/` - Overall totals

### CBSTM03A - Account Statement

Generates account statements in CSV and HTML formats for each card/account.

```bash
spark-submit jobs/cbstm03a_account_statement.py [start_date] [end_date] [output_path] [catalog] [database]
```

**Parameters:**
- `start_date` / `end_date`: Optional date range filter (YYYY-MM-DD)
- `output_path`: Output directory (default: /tmp/carddemo_statements_{date})

**Output CSV files:**
- `statement_detail/` - Flat transaction detail per account
- `statement_html/` - HTML statement content per account

## Delta Table Schemas

| Table | COBOL Equivalent | Key Columns |
|---|---|---|
| account | ACCTFILE (VSAM KSDS) | acct_id, curr_bal, credit_limit |
| customer | CUSTFILE (VSAM KSDS) | cust_id, name, address fields |
| card_xref | XREFFILE (VSAM KSDS) | card_num, acct_id, cust_id |
| daily_transaction | DALYTRAN (PS) | tran_id, card_num, tran_amt |
| transaction | TRANSACT (VSAM KSDS) | tran_id, card_num, tran_amt, proc_ts |
| tran_cat_bal | TCATBALF (VSAM KSDS) | acct_id, tran_type_cd, tran_cat_cd, tran_cat_bal |
| disclosure_group | DISCGRP (VSAM KSDS) | acct_group_id, tran_type_cd, tran_cat_cd, int_rate |
| transaction_type | TRANTYPE (DB2) | tran_type_cd, tran_type_desc |
| transaction_category | TRANCATG (DB2) | tran_type_cd, tran_cat_cd, tran_cat_desc |
| daily_reject | DALYREJS (PS) | tran_id, reject_reason_cd, reject_reason_desc |

## COBOL-to-PySpark Mapping

| COBOL Construct | PySpark Equivalent |
|---|---|
| VSAM KSDS READ | `spark.table().filter()` |
| VSAM KSDS WRITE/REWRITE | `.write.format("delta").mode("append"/"overwrite")` |
| Sequential file READ | `spark.table().orderBy()` |
| COMPUTE arithmetic | PySpark column expressions (`F.col() * F.col()`) |
| IF/EVALUATE | `F.when()` / `.filter()` |
| PERFORM UNTIL | DataFrame transformations (set-based) |
| WORKING-STORAGE counters | `.count()` / `.agg()` |
| Report WRITE | `.write.csv()` with header |
| Control breaks (card_num change) | `.groupBy()` / `.orderBy()` |
