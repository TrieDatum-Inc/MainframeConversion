"""
Delta Lake Schema Definitions for CBTRN02C Migration
Based on COBOL copybooks from CardDemo mainframe application

This module defines the schemas for all Delta Lake tables that replace
the VSAM files used by the mainframe CBTRN02C program.
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType, 
    IntegerType, TimestampType, DateType, LongType
)

# =============================================================================
# DALYTRAN - Daily Transaction Input (Bronze Layer)
# Source: CVTRA06Y.cpy - DALYTRAN-RECORD (350 bytes)
# =============================================================================
DALYTRAN_SCHEMA = StructType([
    StructField("tran_id", StringType(), False),              # PIC X(16) - Primary Key
    StructField("tran_type_cd", StringType(), False),         # PIC X(02)
    StructField("tran_cat_cd", IntegerType(), False),         # PIC 9(04)
    StructField("tran_source", StringType(), True),           # PIC X(10)
    StructField("tran_desc", StringType(), True),             # PIC X(100)
    StructField("tran_amt", DecimalType(11, 2), False),       # PIC S9(09)V99
    StructField("merchant_id", LongType(), True),             # PIC 9(09)
    StructField("merchant_name", StringType(), True),         # PIC X(50)
    StructField("merchant_city", StringType(), True),         # PIC X(50)
    StructField("merchant_zip", StringType(), True),          # PIC X(10)
    StructField("card_num", StringType(), False),             # PIC X(16)
    StructField("orig_ts", StringType(), True),               # PIC X(26)
    StructField("proc_ts", StringType(), True),               # PIC X(26)
    # Metadata columns for Databricks
    StructField("batch_id", StringType(), False),             # Batch identifier for idempotency
    StructField("ingestion_ts", TimestampType(), False),      # When record was ingested
])

# =============================================================================
# TRANSACT - Transaction Master (Silver/Gold Layer)
# Source: CVTRA05Y.cpy - TRAN-RECORD (350 bytes)
# Target: AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS
# =============================================================================
TRANSACT_SCHEMA = StructType([
    StructField("tran_id", StringType(), False),              # PIC X(16) - Primary Key
    StructField("tran_type_cd", StringType(), False),         # PIC X(02)
    StructField("tran_cat_cd", IntegerType(), False),         # PIC 9(04)
    StructField("tran_source", StringType(), True),           # PIC X(10)
    StructField("tran_desc", StringType(), True),             # PIC X(100)
    StructField("tran_amt", DecimalType(11, 2), False),       # PIC S9(09)V99
    StructField("merchant_id", LongType(), True),             # PIC 9(09)
    StructField("merchant_name", StringType(), True),         # PIC X(50)
    StructField("merchant_city", StringType(), True),         # PIC X(50)
    StructField("merchant_zip", StringType(), True),          # PIC X(10)
    StructField("card_num", StringType(), False),             # PIC X(16)
    StructField("orig_ts", StringType(), True),               # PIC X(26) - Original timestamp
    StructField("proc_ts", StringType(), False),              # PIC X(26) - Processed timestamp
    # Metadata columns
    StructField("batch_id", StringType(), False),
    StructField("created_ts", TimestampType(), False),
])

# =============================================================================
# ACCTFILE - Account Master (Stateful Table)
# Source: CVACT01Y.cpy - ACCOUNT-RECORD (300 bytes)
# Target: AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS
# =============================================================================
ACCOUNT_SCHEMA = StructType([
    StructField("acct_id", StringType(), False),              # PIC 9(11) - Primary Key
    StructField("active_status", StringType(), True),         # PIC X(01)
    StructField("curr_bal", DecimalType(12, 2), False),       # PIC S9(10)V99
    StructField("credit_limit", DecimalType(12, 2), False),   # PIC S9(10)V99
    StructField("cash_credit_limit", DecimalType(12, 2), True), # PIC S9(10)V99
    StructField("open_date", StringType(), True),             # PIC X(10)
    StructField("expiration_date", StringType(), True),       # PIC X(10)
    StructField("reissue_date", StringType(), True),          # PIC X(10)
    StructField("curr_cyc_credit", DecimalType(12, 2), False), # PIC S9(10)V99
    StructField("curr_cyc_debit", DecimalType(12, 2), False),  # PIC S9(10)V99
    StructField("addr_zip", StringType(), True),              # PIC X(10)
    StructField("group_id", StringType(), True),              # PIC X(10)
    # Metadata columns
    StructField("last_updated_ts", TimestampType(), False),
    StructField("last_updated_batch_id", StringType(), True),
])

# =============================================================================
# CARDXREF - Card Cross-Reference (Lookup Table)
# Source: CVACT03Y.cpy - CARD-XREF-RECORD (50 bytes)
# Target: AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS
# =============================================================================
CARDXREF_SCHEMA = StructType([
    StructField("card_num", StringType(), False),             # PIC X(16) - Primary Key
    StructField("cust_id", StringType(), False),              # PIC 9(09)
    StructField("acct_id", StringType(), False),              # PIC 9(11)
])

# =============================================================================
# TCATBALF - Transaction Category Balance (Stateful Table)
# Source: CVTRA01Y.cpy - TRAN-CAT-BAL-RECORD (50 bytes)
# Target: AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS
# =============================================================================
TCATBAL_SCHEMA = StructType([
    StructField("acct_id", StringType(), False),              # PIC 9(11) - Part of composite key
    StructField("tran_type_cd", StringType(), False),         # PIC X(02) - Part of composite key
    StructField("tran_cat_cd", IntegerType(), False),         # PIC 9(04) - Part of composite key
    StructField("tran_cat_bal", DecimalType(11, 2), False),   # PIC S9(09)V99
    # Metadata columns
    StructField("last_updated_ts", TimestampType(), False),
    StructField("last_updated_batch_id", StringType(), True),
])

# =============================================================================
# DALYREJS - Daily Rejects (Audit/Error Table)
# Equivalent to AWS.M2.CARDDEMO.DALYREJS GDG
# =============================================================================
REJECTS_SCHEMA = StructType([
    StructField("tran_id", StringType(), False),              # Original transaction ID
    StructField("card_num", StringType(), True),              # Card number from transaction
    StructField("tran_amt", DecimalType(11, 2), True),        # Transaction amount
    StructField("orig_ts", StringType(), True),               # Original timestamp
    StructField("reject_reason_code", IntegerType(), False),  # Validation failure code
    StructField("reject_reason_desc", StringType(), False),   # Validation failure description
    StructField("raw_record", StringType(), True),            # Original raw record for audit
    # Metadata columns
    StructField("batch_id", StringType(), False),
    StructField("rejected_ts", TimestampType(), False),
])

# =============================================================================
# Validation Reason Codes (matching COBOL CBTRN02C exactly)
# =============================================================================
VALIDATION_CODES = {
    100: "INVALID CARD NUMBER FOUND",
    101: "ACCOUNT RECORD NOT FOUND",
    102: "OVERLIMIT TRANSACTION",
    103: "TRANSACTION RECEIVED AFTER ACCT EXPIRATION",
    109: "ACCOUNT RECORD NOT FOUND DURING UPDATE",
}

# =============================================================================
# EBCDIC Field Definitions for parsing mainframe files
# Format: (field_name, start_pos, length, field_type, decimals)
# Positions are 0-indexed
# =============================================================================
DALYTRAN_EBCDIC_LAYOUT = [
    ("tran_id", 0, 16, "char", 0),
    ("tran_type_cd", 16, 2, "char", 0),
    ("tran_cat_cd", 18, 4, "zoned", 0),
    ("tran_source", 22, 10, "char", 0),
    ("tran_desc", 32, 100, "char", 0),
    ("tran_amt", 132, 11, "signed_zoned", 2),  # S9(09)V99 = 11 digits with implied 2 decimals
    ("merchant_id", 143, 9, "zoned", 0),
    ("merchant_name", 152, 50, "char", 0),
    ("merchant_city", 202, 50, "char", 0),
    ("merchant_zip", 252, 10, "char", 0),
    ("card_num", 262, 16, "char", 0),
    ("orig_ts", 278, 26, "char", 0),
    ("proc_ts", 304, 26, "char", 0),
    ("filler", 330, 20, "char", 0),
]

# Total record length
DALYTRAN_RECORD_LENGTH = 350
