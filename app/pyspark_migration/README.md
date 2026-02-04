# CBTRN02C PySpark Migration

This directory contains the PySpark migration of the COBOL batch program `CBTRN02C.cbl` for execution on Databricks with Delta Lake.

## Overview

The original COBOL program `CBTRN02C.cbl` posts daily credit card transactions to the transaction master, updates account balances, and maintains transaction category balances. This migration preserves the exact sequential processing logic and validation rules.

## Files

| File | Description |
|------|-------------|
| `01_table_setup.py` | Creates all Delta tables with proper schemas |
| `02_sample_data_load.py` | Loads sample test data into the tables |
| `cbtrn02c_pyspark.py` | Main program - PySpark equivalent of CBTRN02C.cbl |
| `run_cbtrn02c.py` | Runner script to execute the complete posting cycle |

## Delta Tables

| Table | COBOL Equivalent | Description |
|-------|------------------|-------------|
| `daily_transactions` | DALYTRAN | Input transactions to be posted |
| `card_xref` | CARDXREF/XREFFILE | Card to account cross-reference |
| `accounts` | ACCTFILE | Account master with balances |
| `transaction_category_balance` | TCATBALF | Running balances by category |
| `transactions` | TRANSACT/TRANFILE | Posted transaction master |
| `daily_rejects` | DALYREJS | Rejected transactions with reasons |

## Validation Rules

The program validates each transaction with the following checks:

| Error Code | Description | COBOL Reference |
|------------|-------------|-----------------|
| 100 | Invalid card number (not in cross-reference) | 1500-A-LOOKUP-XREF |
| 101 | Account record not found | 1500-B-LOOKUP-ACCT |
| 102 | Overlimit transaction | 1500-B-LOOKUP-ACCT |
| 103 | Transaction after account expiration | 1500-B-LOOKUP-ACCT |

## Execution Instructions

### Step 1: Create Tables
Run `01_table_setup.py` in Databricks to create the database and all Delta tables.

### Step 2: Load Sample Data
Run `02_sample_data_load.py` to load test data for validation.

### Step 3: Execute Transaction Posting
Run `run_cbtrn02c.py` to execute the complete transaction posting cycle.

Alternatively, run `cbtrn02c_pyspark.py` directly for just the posting logic.

## Processing Logic

The program follows the exact same sequential processing as the COBOL original:

1. Load lookup tables (card_xref, accounts, category balances) into memory
2. Read unprocessed daily transactions in order
3. For each transaction:
   - Validate card number exists in cross-reference
   - Validate account exists and check business rules
   - If valid: Post transaction, update balances
   - If invalid: Write to rejects with failure reason
4. Persist all updates to Delta tables
5. Display processing statistics

## Return Codes

| Code | Meaning |
|------|---------|
| 0 | All transactions processed successfully |
| 4 | Completed with some rejected transactions |

## Sample Data

The sample data includes 10 transactions designed to test all validation paths:
- 7 valid transactions (will be posted)
- 1 invalid card number (Error 100)
- 1 overlimit transaction (Error 102)
- 1 expired account transaction (Error 103)

## Databricks Free Edition Compatibility

This migration is designed to work with Databricks Community Edition (free tier):
- Uses Delta Lake (included in Databricks)
- No external dependencies required
- All tables created in a single database
- Compatible with single-node clusters

## Original COBOL Program Reference

The original program is located at: `app/cbl/CBTRN02C.cbl`

JCL to run the original: `app/jcl/POSTTRAN.jcl`

Copybooks used:
- `CVTRA06Y.cpy` - Daily transaction record
- `CVTRA05Y.cpy` - Transaction master record
- `CVACT03Y.cpy` - Card cross-reference
- `CVACT01Y.cpy` - Account record
- `CVTRA01Y.cpy` - Transaction category balance
