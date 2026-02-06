-- ============================================================================
-- DDL Setup for CBTRN02C PySpark Migration
-- Creates Databricks Delta tables based on COBOL copybook structures
-- Source copybooks: CVTRA06Y, CVTRA05Y, CVACT03Y, CVACT01Y, CVTRA01Y
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS carddemo;

-- ---------------------------------------------------------------------------
-- Daily Transaction Input (Copybook: CVTRA06Y - DALYTRAN-RECORD)
-- Source: DALYTRAN sequential file
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.daily_transaction (
    dalytran_id             STRING          NOT NULL,
    dalytran_type_cd        STRING          NOT NULL,
    dalytran_cat_cd         INT             NOT NULL,
    dalytran_source         STRING,
    dalytran_desc           STRING,
    dalytran_amt            DECIMAL(11,2)   NOT NULL,
    dalytran_merchant_id    BIGINT,
    dalytran_merchant_name  STRING,
    dalytran_merchant_city  STRING,
    dalytran_merchant_zip   STRING,
    dalytran_card_num       STRING          NOT NULL,
    dalytran_orig_ts        STRING,
    dalytran_proc_ts        STRING
)
USING DELTA
COMMENT 'Daily transaction staging table (from DALYTRAN sequential file / CVTRA06Y copybook)';

-- ---------------------------------------------------------------------------
-- Transaction Master (Copybook: CVTRA05Y - TRAN-RECORD)
-- Source: TRANSACT VSAM KSDS, key = TRAN-ID
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.transaction (
    tran_id                 STRING          NOT NULL,
    tran_type_cd            STRING          NOT NULL,
    tran_cat_cd             INT             NOT NULL,
    tran_source             STRING,
    tran_desc               STRING,
    tran_amt                DECIMAL(11,2)   NOT NULL,
    tran_merchant_id        BIGINT,
    tran_merchant_name      STRING,
    tran_merchant_city      STRING,
    tran_merchant_zip       STRING,
    tran_card_num           STRING          NOT NULL,
    tran_orig_ts            STRING,
    tran_proc_ts            STRING,
    CONSTRAINT pk_transaction PRIMARY KEY (tran_id)
)
USING DELTA
COMMENT 'Posted transaction master (from TRANSACT VSAM / CVTRA05Y copybook)';

-- ---------------------------------------------------------------------------
-- Card Cross-Reference (Copybook: CVACT03Y - CARD-XREF-RECORD)
-- Source: CCXREF VSAM KSDS, key = XREF-CARD-NUM
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.card_xref (
    xref_card_num           STRING          NOT NULL,
    xref_cust_id            BIGINT          NOT NULL,
    xref_acct_id            BIGINT          NOT NULL,
    CONSTRAINT pk_card_xref PRIMARY KEY (xref_card_num)
)
USING DELTA
COMMENT 'Card-to-account-to-customer cross reference (from CCXREF VSAM / CVACT03Y copybook)';

-- ---------------------------------------------------------------------------
-- Account Master (Copybook: CVACT01Y - ACCOUNT-RECORD)
-- Source: ACCTDAT VSAM KSDS, key = ACCT-ID
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.account (
    acct_id                 BIGINT          NOT NULL,
    acct_active_status      STRING,
    acct_curr_bal           DECIMAL(12,2)   NOT NULL DEFAULT 0,
    acct_credit_limit       DECIMAL(12,2)   NOT NULL DEFAULT 0,
    acct_cash_credit_limit  DECIMAL(12,2)   NOT NULL DEFAULT 0,
    acct_open_date          STRING,
    acct_expiration_date    STRING,
    acct_reissue_date       STRING,
    acct_curr_cyc_credit    DECIMAL(12,2)   NOT NULL DEFAULT 0,
    acct_curr_cyc_debit     DECIMAL(12,2)   NOT NULL DEFAULT 0,
    acct_addr_zip           STRING,
    acct_group_id           STRING,
    CONSTRAINT pk_account PRIMARY KEY (acct_id)
)
USING DELTA
COMMENT 'Account master (from ACCTDAT VSAM / CVACT01Y copybook)';

-- ---------------------------------------------------------------------------
-- Transaction Category Balance (Copybook: CVTRA01Y - TRAN-CAT-BAL-RECORD)
-- Source: TCATBALF VSAM KSDS, composite key = ACCT-ID + TYPE-CD + CAT-CD
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.tran_cat_balance (
    trancat_acct_id         BIGINT          NOT NULL,
    trancat_type_cd         STRING          NOT NULL,
    trancat_cd              INT             NOT NULL,
    tran_cat_bal            DECIMAL(11,2)   NOT NULL DEFAULT 0,
    CONSTRAINT pk_tran_cat_balance PRIMARY KEY (trancat_acct_id, trancat_type_cd, trancat_cd)
)
USING DELTA
COMMENT 'Transaction category balance aggregation (from TCATBALF VSAM / CVTRA01Y copybook)';

-- ---------------------------------------------------------------------------
-- Daily Rejects Output (no copybook; layout from CBTRN02C working storage)
-- Source: DALYREJS sequential output file
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carddemo.daily_rejects (
    dalytran_id             STRING,
    dalytran_type_cd        STRING,
    dalytran_cat_cd         INT,
    dalytran_source         STRING,
    dalytran_desc           STRING,
    dalytran_amt            DECIMAL(11,2),
    dalytran_merchant_id    BIGINT,
    dalytran_merchant_name  STRING,
    dalytran_merchant_city  STRING,
    dalytran_merchant_zip   STRING,
    dalytran_card_num       STRING,
    dalytran_orig_ts        STRING,
    dalytran_proc_ts        STRING,
    reject_reason_code      INT             NOT NULL,
    reject_reason_desc      STRING          NOT NULL,
    reject_timestamp        TIMESTAMP       DEFAULT current_timestamp()
)
USING DELTA
COMMENT 'Rejected daily transactions with validation failure reasons (from DALYREJS output)';
