-- =============================================================================
-- CardDemo Batch Processing - Delta Table Setup
-- Databricks Delta Lake table definitions matching COBOL copybook structures
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Database
-- -----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS carddemo;
USE carddemo;

-- -----------------------------------------------------------------------------
-- ACCOUNT (Copybook: CVACT01Y, RECLN 300)
-- Source: AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS
-- Used by: CBTRN02C, CBACT04C, CBSTM03A
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS account (
    acct_id             BIGINT          NOT NULL,
    active_status       STRING          NOT NULL,
    curr_bal            DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    credit_limit        DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    cash_credit_limit   DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    open_date           STRING          NOT NULL,
    expiration_date     STRING          NOT NULL,
    reissue_date        STRING,
    curr_cyc_credit     DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    curr_cyc_debit      DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    addr_zip            STRING,
    group_id            STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- -----------------------------------------------------------------------------
-- CUSTOMER (Copybook: CUSTREC, RECLN 500)
-- Source: AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS
-- Used by: CBSTM03A
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer (
    cust_id             BIGINT          NOT NULL,
    first_name          STRING,
    middle_name         STRING,
    last_name           STRING,
    addr_line_1         STRING,
    addr_line_2         STRING,
    addr_line_3         STRING,
    addr_state_cd       STRING,
    addr_country_cd     STRING,
    addr_zip            STRING,
    phone_num_1         STRING,
    phone_num_2         STRING,
    ssn                 BIGINT,
    govt_issued_id      STRING,
    dob_yyyymmdd        STRING,
    eft_account_id      STRING,
    pri_card_holder_ind STRING,
    fico_credit_score   INT
)
USING DELTA;

-- -----------------------------------------------------------------------------
-- CARD_XREF (Copybook: CVACT03Y, RECLN 50)
-- Source: AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS
-- Used by: CBTRN02C, CBACT04C, CBTRN03C, CBSTM03A
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS card_xref (
    card_num            STRING          NOT NULL,
    cust_id             BIGINT          NOT NULL,
    acct_id             BIGINT          NOT NULL
)
USING DELTA;

-- -----------------------------------------------------------------------------
-- DAILY_TRANSACTION (Copybook: CVTRA06Y, RECLN 350)
-- Source: AWS.M2.CARDDEMO.DALYTRAN.PS
-- Used by: CBTRN02C (input)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_transaction (
    tran_id             STRING          NOT NULL,
    tran_type_cd        STRING          NOT NULL,
    tran_cat_cd         INT             NOT NULL,
    tran_source         STRING,
    tran_desc           STRING,
    tran_amt            DECIMAL(11,2)   NOT NULL,
    merchant_id         BIGINT,
    merchant_name       STRING,
    merchant_city       STRING,
    merchant_zip        STRING,
    card_num            STRING          NOT NULL,
    orig_ts             STRING,
    proc_ts             STRING
)
USING DELTA;

-- -----------------------------------------------------------------------------
-- TRANSACTION (Copybook: CVTRA05Y, RECLN 350)
-- Source: AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS
-- Used by: CBTRN02C (output), CBACT04C (output), CBTRN03C (input), CBSTM03A (input)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaction (
    tran_id             STRING          NOT NULL,
    tran_type_cd        STRING          NOT NULL,
    tran_cat_cd         INT             NOT NULL,
    tran_source         STRING,
    tran_desc           STRING,
    tran_amt            DECIMAL(11,2)   NOT NULL,
    merchant_id         BIGINT,
    merchant_name       STRING,
    merchant_city       STRING,
    merchant_zip        STRING,
    card_num            STRING          NOT NULL,
    orig_ts             STRING,
    proc_ts             STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- -----------------------------------------------------------------------------
-- TRAN_CAT_BAL (Copybook: CVTRA01Y, RECLN 50)
-- Source: AWS.M2.CARDDEMO.TCATBAL.VSAM.KSDS
-- Used by: CBTRN02C (I/O), CBACT04C (input)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tran_cat_bal (
    acct_id             BIGINT          NOT NULL,
    tran_type_cd        STRING          NOT NULL,
    tran_cat_cd         INT             NOT NULL,
    tran_cat_bal        DECIMAL(11,2)   NOT NULL DEFAULT 0.00
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- -----------------------------------------------------------------------------
-- DISCLOSURE_GROUP (Copybook: CVTRA02Y, RECLN 50)
-- Source: AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS
-- Used by: CBACT04C
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS disclosure_group (
    acct_group_id       STRING          NOT NULL,
    tran_type_cd        STRING          NOT NULL,
    tran_cat_cd         INT             NOT NULL,
    int_rate            DECIMAL(6,2)    NOT NULL DEFAULT 0.00
)
USING DELTA;

-- -----------------------------------------------------------------------------
-- TRANSACTION_TYPE (Copybook: CVTRA03Y, RECLN 60)
-- Source: DB2 TRANSACT table
-- Used by: CBTRN03C
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaction_type (
    tran_type_cd        STRING          NOT NULL,
    tran_type_desc      STRING
)
USING DELTA;

-- -----------------------------------------------------------------------------
-- TRANSACTION_CATEGORY (Copybook: CVTRA04Y, RECLN 60)
-- Source: DB2 TRANCATG table
-- Used by: CBTRN03C
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaction_category (
    tran_type_cd        STRING          NOT NULL,
    tran_cat_cd         INT             NOT NULL,
    tran_cat_desc       STRING
)
USING DELTA;

-- -----------------------------------------------------------------------------
-- DAILY_REJECT (Output of CBTRN02C)
-- Source: AWS.M2.CARDDEMO.DALYREJS.PS
-- Used by: CBTRN02C (output)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_reject (
    tran_id             STRING          NOT NULL,
    tran_type_cd        STRING,
    tran_cat_cd         INT,
    tran_source         STRING,
    tran_desc           STRING,
    tran_amt            DECIMAL(11,2),
    merchant_id         BIGINT,
    merchant_name       STRING,
    merchant_city       STRING,
    merchant_zip        STRING,
    card_num            STRING,
    orig_ts             STRING,
    proc_ts             STRING,
    reject_reason_cd    INT             NOT NULL,
    reject_reason_desc  STRING          NOT NULL
)
USING DELTA;
