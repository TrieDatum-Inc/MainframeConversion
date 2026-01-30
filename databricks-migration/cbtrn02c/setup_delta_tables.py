"""
Delta Lake Table Setup for CBTRN02C Migration

This script creates the Unity Catalog schema and Delta Lake tables
required for the CBTRN02C transaction posting job.

Tables Created:
- bronze.dalytran - Daily transaction input (landing zone)
- silver.transactions - Transaction master (replaces TRANSACT.VSAM.KSDS)
- silver.accounts - Account master (replaces ACCTDATA.VSAM.KSDS)
- silver.card_xref - Card cross-reference (replaces CARDXREF.VSAM.KSDS)
- silver.tran_cat_balance - Transaction category balance (replaces TCATBALF.VSAM.KSDS)
- silver.transaction_rejects - Rejected transactions (replaces DALYREJS GDG)

Run this script once to initialize the Databricks environment.

Usage:
    # In Databricks notebook or job:
    %run ./setup_delta_tables
    
    # Or via spark-submit:
    spark-submit setup_delta_tables.py --catalog carddemo
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType,
    IntegerType, TimestampType, LongType
)
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SetupDeltaTables")


def create_catalog_and_schemas(spark: SparkSession, catalog: str):
    """Create Unity Catalog and schemas if they don't exist."""
    
    logger.info(f"Creating catalog: {catalog}")
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    spark.sql(f"USE CATALOG {catalog}")
    
    logger.info("Creating schemas: bronze, silver, gold")
    spark.sql("CREATE SCHEMA IF NOT EXISTS bronze COMMENT 'Raw data landing zone'")
    spark.sql("CREATE SCHEMA IF NOT EXISTS silver COMMENT 'Cleansed and validated data'")
    spark.sql("CREATE SCHEMA IF NOT EXISTS gold COMMENT 'Business-level aggregates'")


def create_dalytran_table(spark: SparkSession, catalog: str):
    """
    Create bronze.dalytran table for daily transaction input.
    This is where EBCDIC-converted data lands before processing.
    """
    table_name = f"{catalog}.bronze.dalytran"
    logger.info(f"Creating table: {table_name}")
    
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            tran_id STRING NOT NULL COMMENT 'Transaction ID - PIC X(16)',
            tran_type_cd STRING NOT NULL COMMENT 'Transaction type code - PIC X(02)',
            tran_cat_cd INT NOT NULL COMMENT 'Transaction category code - PIC 9(04)',
            tran_source STRING COMMENT 'Transaction source - PIC X(10)',
            tran_desc STRING COMMENT 'Transaction description - PIC X(100)',
            tran_amt DECIMAL(11,2) NOT NULL COMMENT 'Transaction amount - PIC S9(09)V99',
            merchant_id BIGINT COMMENT 'Merchant ID - PIC 9(09)',
            merchant_name STRING COMMENT 'Merchant name - PIC X(50)',
            merchant_city STRING COMMENT 'Merchant city - PIC X(50)',
            merchant_zip STRING COMMENT 'Merchant ZIP - PIC X(10)',
            card_num STRING NOT NULL COMMENT 'Card number - PIC X(16)',
            orig_ts STRING COMMENT 'Original timestamp - PIC X(26)',
            proc_ts STRING COMMENT 'Processed timestamp - PIC X(26)',
            batch_id STRING NOT NULL COMMENT 'Batch identifier for idempotency',
            ingestion_ts TIMESTAMP NOT NULL COMMENT 'When record was ingested'
        )
        USING DELTA
        COMMENT 'Daily transaction input - migrated from DALYTRAN mainframe file'
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
    """)
    
    logger.info(f"Table {table_name} created successfully")


def create_transactions_table(spark: SparkSession, catalog: str):
    """
    Create silver.transactions table.
    Replaces AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS
    """
    table_name = f"{catalog}.silver.transactions"
    logger.info(f"Creating table: {table_name}")
    
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            tran_id STRING NOT NULL COMMENT 'Transaction ID - Primary Key - PIC X(16)',
            tran_type_cd STRING NOT NULL COMMENT 'Transaction type code - PIC X(02)',
            tran_cat_cd INT NOT NULL COMMENT 'Transaction category code - PIC 9(04)',
            tran_source STRING COMMENT 'Transaction source - PIC X(10)',
            tran_desc STRING COMMENT 'Transaction description - PIC X(100)',
            tran_amt DECIMAL(11,2) NOT NULL COMMENT 'Transaction amount - PIC S9(09)V99',
            merchant_id BIGINT COMMENT 'Merchant ID - PIC 9(09)',
            merchant_name STRING COMMENT 'Merchant name - PIC X(50)',
            merchant_city STRING COMMENT 'Merchant city - PIC X(50)',
            merchant_zip STRING COMMENT 'Merchant ZIP - PIC X(10)',
            card_num STRING NOT NULL COMMENT 'Card number - PIC X(16)',
            orig_ts STRING COMMENT 'Original timestamp - PIC X(26)',
            proc_ts STRING NOT NULL COMMENT 'Processed timestamp - PIC X(26)',
            batch_id STRING NOT NULL COMMENT 'Batch identifier',
            created_ts TIMESTAMP NOT NULL COMMENT 'Record creation timestamp'
        )
        USING DELTA
        COMMENT 'Transaction master - migrated from AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS'
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
    """)
    
    # Create constraint for primary key (tran_id + batch_id for idempotency)
    # Note: Delta Lake doesn't enforce PK but this documents the intent
    
    logger.info(f"Table {table_name} created successfully")


def create_accounts_table(spark: SparkSession, catalog: str):
    """
    Create silver.accounts table.
    Replaces AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS
    """
    table_name = f"{catalog}.silver.accounts"
    logger.info(f"Creating table: {table_name}")
    
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            acct_id STRING NOT NULL COMMENT 'Account ID - Primary Key - PIC 9(11)',
            active_status STRING COMMENT 'Active status - PIC X(01)',
            curr_bal DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT 'Current balance - PIC S9(10)V99',
            credit_limit DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT 'Credit limit - PIC S9(10)V99',
            cash_credit_limit DECIMAL(12,2) COMMENT 'Cash credit limit - PIC S9(10)V99',
            open_date STRING COMMENT 'Account open date - PIC X(10)',
            expiration_date STRING COMMENT 'Account expiration date - PIC X(10)',
            reissue_date STRING COMMENT 'Reissue date - PIC X(10)',
            curr_cyc_credit DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT 'Current cycle credits - PIC S9(10)V99',
            curr_cyc_debit DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT 'Current cycle debits - PIC S9(10)V99',
            addr_zip STRING COMMENT 'Address ZIP - PIC X(10)',
            group_id STRING COMMENT 'Account group ID - PIC X(10)',
            last_updated_ts TIMESTAMP NOT NULL COMMENT 'Last update timestamp',
            last_updated_batch_id STRING COMMENT 'Last update batch ID'
        )
        USING DELTA
        COMMENT 'Account master - migrated from AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS'
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
    """)
    
    logger.info(f"Table {table_name} created successfully")


def create_card_xref_table(spark: SparkSession, catalog: str):
    """
    Create silver.card_xref table.
    Replaces AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS
    """
    table_name = f"{catalog}.silver.card_xref"
    logger.info(f"Creating table: {table_name}")
    
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            card_num STRING NOT NULL COMMENT 'Card number - Primary Key - PIC X(16)',
            cust_id STRING NOT NULL COMMENT 'Customer ID - PIC 9(09)',
            acct_id STRING NOT NULL COMMENT 'Account ID - PIC 9(11)'
        )
        USING DELTA
        COMMENT 'Card cross-reference - migrated from AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS'
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
    """)
    
    logger.info(f"Table {table_name} created successfully")


def create_tran_cat_balance_table(spark: SparkSession, catalog: str):
    """
    Create silver.tran_cat_balance table.
    Replaces AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS
    """
    table_name = f"{catalog}.silver.tran_cat_balance"
    logger.info(f"Creating table: {table_name}")
    
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            acct_id STRING NOT NULL COMMENT 'Account ID - Part of composite key - PIC 9(11)',
            tran_type_cd STRING NOT NULL COMMENT 'Transaction type code - Part of composite key - PIC X(02)',
            tran_cat_cd INT NOT NULL COMMENT 'Transaction category code - Part of composite key - PIC 9(04)',
            tran_cat_bal DECIMAL(11,2) NOT NULL DEFAULT 0 COMMENT 'Category balance - PIC S9(09)V99',
            last_updated_ts TIMESTAMP NOT NULL COMMENT 'Last update timestamp',
            last_updated_batch_id STRING COMMENT 'Last update batch ID'
        )
        USING DELTA
        COMMENT 'Transaction category balance - migrated from AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS'
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
    """)
    
    logger.info(f"Table {table_name} created successfully")


def create_rejects_table(spark: SparkSession, catalog: str):
    """
    Create silver.transaction_rejects table.
    Replaces AWS.M2.CARDDEMO.DALYREJS GDG
    """
    table_name = f"{catalog}.silver.transaction_rejects"
    logger.info(f"Creating table: {table_name}")
    
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            tran_id STRING NOT NULL COMMENT 'Original transaction ID',
            card_num STRING COMMENT 'Card number from transaction',
            tran_amt DECIMAL(11,2) COMMENT 'Transaction amount',
            orig_ts STRING COMMENT 'Original timestamp',
            reject_reason_code INT NOT NULL COMMENT 'Validation failure code',
            reject_reason_desc STRING NOT NULL COMMENT 'Validation failure description',
            raw_record STRING COMMENT 'Original raw record for audit',
            batch_id STRING NOT NULL COMMENT 'Batch identifier',
            rejected_ts TIMESTAMP NOT NULL COMMENT 'When record was rejected'
        )
        USING DELTA
        COMMENT 'Rejected transactions - migrated from AWS.M2.CARDDEMO.DALYREJS'
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        PARTITIONED BY (batch_id)
    """)
    
    logger.info(f"Table {table_name} created successfully")


def load_sample_data(spark: SparkSession, catalog: str):
    """
    Load sample data for testing.
    This replicates the sample data from the mainframe VSAM files.
    """
    logger.info("Loading sample data for testing...")
    
    # Sample accounts (from ACCTDATA)
    sample_accounts = [
        ("00000000001", "Y", 1500.75, 10000.00, 2000.00, "2020-01-15", "2025-12-31", None, 500.00, -200.00, "10001", "PREMIUM"),
        ("00000000002", "Y", 3250.50, 15000.00, 3000.00, "2019-06-20", "2026-06-30", None, 1000.00, -500.00, "20002", "GOLD"),
        ("00000000003", "N", 0.00, 5000.00, 1000.00, "2018-03-10", "2024-03-31", None, 0.00, 0.00, "30003", "STANDARD"),
        ("00000000004", "Y", 7890.25, 25000.00, 5000.00, "2021-09-01", "2027-09-30", None, 2500.00, -1000.00, "40004", "PLATINUM"),
        ("00000000005", "Y", 450.00, 3000.00, 500.00, "2022-02-14", "2028-02-28", None, 100.00, -50.00, "50005", "STANDARD"),
    ]
    
    accounts_df = spark.createDataFrame(
        sample_accounts,
        ["acct_id", "active_status", "curr_bal", "credit_limit", "cash_credit_limit",
         "open_date", "expiration_date", "reissue_date", "curr_cyc_credit", "curr_cyc_debit",
         "addr_zip", "group_id"]
    ).withColumn("last_updated_ts", spark.sql("SELECT current_timestamp()").collect()[0][0]) \
     .withColumn("last_updated_batch_id", spark.sql("SELECT 'INITIAL_LOAD'").collect()[0][0])
    
    accounts_df.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.silver.accounts")
    logger.info(f"Loaded {accounts_df.count()} sample accounts")
    
    # Sample card cross-references (from CARDXREF)
    sample_xrefs = [
        ("4111111111111111", "100000001", "00000000001"),
        ("4222222222222222", "100000002", "00000000002"),
        ("4333333333333333", "100000003", "00000000003"),
        ("4444444444444444", "100000004", "00000000004"),
        ("4555555555555555", "100000005", "00000000005"),
    ]
    
    xref_df = spark.createDataFrame(sample_xrefs, ["card_num", "cust_id", "acct_id"])
    xref_df.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.silver.card_xref")
    logger.info(f"Loaded {xref_df.count()} sample card cross-references")
    
    # Sample daily transactions for testing
    sample_dalytran = [
        ("TRN0000000000001", "PR", 1001, "POS", "GROCERY STORE PURCHASE", -45.67, 123456789, "WHOLE FOODS", "NEW YORK", "10001", "4111111111111111", "2024-01-15-10.30.00.000000", None, "20240115120000"),
        ("TRN0000000000002", "PR", 1002, "ONLINE", "AMAZON PURCHASE", -129.99, 987654321, "AMAZON.COM", "SEATTLE", "98101", "4222222222222222", "2024-01-15-11.45.00.000000", None, "20240115120000"),
        ("TRN0000000000003", "CR", 2001, "PAYMENT", "PAYMENT RECEIVED", 500.00, 0, "CUSTOMER PAYMENT", "N/A", "00000", "4111111111111111", "2024-01-15-14.00.00.000000", None, "20240115120000"),
        ("TRN0000000000004", "PR", 1001, "POS", "GAS STATION", -55.00, 111222333, "SHELL", "CHICAGO", "60601", "9999999999999999", "2024-01-15-09.00.00.000000", None, "20240115120000"),  # Invalid card - will be rejected
        ("TRN0000000000005", "PR", 1003, "POS", "ELECTRONICS", -15000.00, 444555666, "BEST BUY", "LOS ANGELES", "90001", "4444444444444444", "2024-01-15-16.30.00.000000", None, "20240115120000"),  # Overlimit - will be rejected
    ]
    
    from pyspark.sql.functions import current_timestamp
    dalytran_df = spark.createDataFrame(
        sample_dalytran,
        ["tran_id", "tran_type_cd", "tran_cat_cd", "tran_source", "tran_desc", "tran_amt",
         "merchant_id", "merchant_name", "merchant_city", "merchant_zip", "card_num",
         "orig_ts", "proc_ts", "batch_id"]
    ).withColumn("ingestion_ts", current_timestamp())
    
    dalytran_df.write.format("delta").mode("overwrite").saveAsTable(f"{catalog}.bronze.dalytran")
    logger.info(f"Loaded {dalytran_df.count()} sample daily transactions")


def setup_all(spark: SparkSession, catalog: str = "carddemo", load_samples: bool = True):
    """
    Run complete setup: create catalog, schemas, tables, and optionally load sample data.
    """
    logger.info("=" * 60)
    logger.info("CBTRN02C Delta Lake Setup - Starting")
    logger.info("=" * 60)
    
    create_catalog_and_schemas(spark, catalog)
    create_dalytran_table(spark, catalog)
    create_transactions_table(spark, catalog)
    create_accounts_table(spark, catalog)
    create_card_xref_table(spark, catalog)
    create_tran_cat_balance_table(spark, catalog)
    create_rejects_table(spark, catalog)
    
    if load_samples:
        load_sample_data(spark, catalog)
    
    logger.info("=" * 60)
    logger.info("CBTRN02C Delta Lake Setup - Complete")
    logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Setup Delta Lake tables for CBTRN02C')
    parser.add_argument('--catalog', default='carddemo', help='Unity Catalog name')
    parser.add_argument('--no-samples', action='store_true', help='Skip loading sample data')
    args = parser.parse_args()
    
    spark = SparkSession.builder.appName("CBTRN02C-Setup").getOrCreate()
    setup_all(spark, args.catalog, load_samples=not args.no_samples)


if __name__ == "__main__":
    main()
