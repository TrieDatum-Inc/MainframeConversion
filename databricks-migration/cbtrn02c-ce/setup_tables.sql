-- ============================================================
-- CBTRN02C - Delta Lake Table Setup for Databricks Community Edition
-- ============================================================
-- 
-- Run this script ONCE to create the required tables.
-- 
-- For Databricks Community Edition:
--   1. Create a new notebook
--   2. Copy each CREATE TABLE statement into a cell
--   3. Run each cell to create the tables
--
-- Note: Databricks CE uses Hive metastore (database.table format)
--       NOT Unity Catalog (catalog.schema.table format)
-- ============================================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS carddemo;
USE carddemo;

-- ============================================================
-- DALYTRAN - Daily Transaction Input Table (Bronze Layer)
-- Source: VSAM DALYTRAN file (CVTRA06Y.cpy - 350 bytes)
-- ============================================================
CREATE TABLE IF NOT EXISTS carddemo.dalytran (
    tran_id STRING COMMENT 'Transaction ID - PIC X(16)',
    tran_type_cd STRING COMMENT 'Transaction type code - PIC X(02)',
    tran_cat_cd INT COMMENT 'Transaction category code - PIC 9(04)',
    tran_source STRING COMMENT 'Source system - PIC X(10)',
    tran_desc STRING COMMENT 'Transaction description - PIC X(100)',
    tran_amt DECIMAL(11,2) COMMENT 'Transaction amount - PIC S9(09)V99',
    merchant_id BIGINT COMMENT 'Merchant ID - PIC 9(09)',
    merchant_name STRING COMMENT 'Merchant name - PIC X(50)',
    merchant_city STRING COMMENT 'Merchant city - PIC X(50)',
    merchant_zip STRING COMMENT 'Merchant ZIP - PIC X(10)',
    card_num STRING COMMENT 'Card number - PIC X(16)',
    orig_ts STRING COMMENT 'Original timestamp - PIC X(26)',
    proc_ts STRING COMMENT 'Processed timestamp - PIC X(26)',
    batch_id STRING COMMENT 'Batch ID for this load',
    ingestion_ts TIMESTAMP COMMENT 'When record was ingested'
)
USING DELTA
COMMENT 'Daily transactions to be posted (Bronze layer - raw input)';

-- ============================================================
-- TRANSACTIONS - Posted Transaction Table (Silver Layer)
-- Target: VSAM TRANSACT file (CVTRA05Y.cpy - 350 bytes)
-- ============================================================
CREATE TABLE IF NOT EXISTS carddemo.transactions (
    tran_id STRING COMMENT 'Transaction ID - PIC X(16)',
    tran_type_cd STRING COMMENT 'Transaction type code - PIC X(02)',
    tran_cat_cd INT COMMENT 'Transaction category code - PIC 9(04)',
    tran_source STRING COMMENT 'Source system - PIC X(10)',
    tran_desc STRING COMMENT 'Transaction description - PIC X(100)',
    tran_amt DECIMAL(11,2) COMMENT 'Transaction amount - PIC S9(09)V99',
    merchant_id BIGINT COMMENT 'Merchant ID - PIC 9(09)',
    merchant_name STRING COMMENT 'Merchant name - PIC X(50)',
    merchant_city STRING COMMENT 'Merchant city - PIC X(50)',
    merchant_zip STRING COMMENT 'Merchant ZIP - PIC X(10)',
    card_num STRING COMMENT 'Card number - PIC X(16)',
    orig_ts STRING COMMENT 'Original timestamp - PIC X(26)',
    proc_ts STRING COMMENT 'Processed timestamp - PIC X(26)',
    batch_id STRING COMMENT 'Batch ID that posted this transaction',
    created_ts TIMESTAMP COMMENT 'When record was created'
)
USING DELTA
COMMENT 'Posted transactions (Silver layer - validated and processed)';

-- ============================================================
-- ACCOUNTS - Account Master Table
-- Source/Target: VSAM ACCTFILE (CVACT01Y.cpy - 300 bytes)
-- ============================================================
CREATE TABLE IF NOT EXISTS carddemo.accounts (
    acct_id STRING COMMENT 'Account ID - PIC 9(11)',
    active_status STRING COMMENT 'Active status Y/N - PIC X(01)',
    curr_bal DECIMAL(12,2) COMMENT 'Current balance - PIC S9(10)V99',
    credit_limit DECIMAL(12,2) COMMENT 'Credit limit - PIC S9(10)V99',
    cash_credit_limit DECIMAL(12,2) COMMENT 'Cash credit limit - PIC S9(10)V99',
    open_date STRING COMMENT 'Account open date - PIC X(10)',
    expiration_date STRING COMMENT 'Expiration date - PIC X(10)',
    reissue_date STRING COMMENT 'Reissue date - PIC X(10)',
    curr_cyc_credit DECIMAL(12,2) COMMENT 'Current cycle credits - PIC S9(10)V99',
    curr_cyc_debit DECIMAL(12,2) COMMENT 'Current cycle debits - PIC S9(10)V99',
    addr_zip STRING COMMENT 'ZIP code - PIC X(10)',
    group_id STRING COMMENT 'Account group ID - PIC X(10)',
    last_updated_ts TIMESTAMP COMMENT 'Last update timestamp',
    last_updated_batch_id STRING COMMENT 'Batch ID of last update'
)
USING DELTA
COMMENT 'Account master records';

-- ============================================================
-- CARD_XREF - Card Cross-Reference Table
-- Source: VSAM XREFFILE (CVACT03Y.cpy - 50 bytes)
-- ============================================================
CREATE TABLE IF NOT EXISTS carddemo.card_xref (
    card_num STRING COMMENT 'Card number - PIC X(16)',
    cust_id STRING COMMENT 'Customer ID - PIC 9(09)',
    acct_id STRING COMMENT 'Account ID - PIC 9(11)'
)
USING DELTA
COMMENT 'Card to account cross-reference';

-- ============================================================
-- TRAN_CAT_BALANCE - Transaction Category Balance Table
-- Source/Target: VSAM TCATBALF (CVTRA01Y.cpy - 50 bytes)
-- ============================================================
CREATE TABLE IF NOT EXISTS carddemo.tran_cat_balance (
    acct_id STRING COMMENT 'Account ID - PIC 9(11)',
    tran_type_cd STRING COMMENT 'Transaction type - PIC X(02)',
    tran_cat_cd INT COMMENT 'Category code - PIC 9(04)',
    tran_cat_bal DECIMAL(11,2) COMMENT 'Category balance - PIC S9(09)V99',
    last_updated_ts TIMESTAMP COMMENT 'Last update timestamp',
    last_updated_batch_id STRING COMMENT 'Batch ID of last update'
)
USING DELTA
COMMENT 'Transaction category balances by account';

-- ============================================================
-- TRANSACTION_REJECTS - Rejected Transaction Table
-- Target: Sequential DALYREJS file
-- ============================================================
CREATE TABLE IF NOT EXISTS carddemo.transaction_rejects (
    tran_id STRING COMMENT 'Transaction ID',
    card_num STRING COMMENT 'Card number',
    tran_amt DECIMAL(11,2) COMMENT 'Transaction amount',
    orig_ts STRING COMMENT 'Original timestamp',
    reject_reason_code INT COMMENT 'Reject code (100-103)',
    reject_reason_desc STRING COMMENT 'Reject description',
    batch_id STRING COMMENT 'Batch ID',
    rejected_ts TIMESTAMP COMMENT 'When rejected'
)
USING DELTA
COMMENT 'Rejected transactions with reason codes';

-- ============================================================
-- Verify tables were created
-- ============================================================
SHOW TABLES IN carddemo;
