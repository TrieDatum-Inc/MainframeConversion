"""
Pytest fixtures for CBTRN02C PySpark migration tests.

Provides SparkSession, Delta table setup/teardown, and test data fixtures.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

from helpers import TEST_SCHEMA


@pytest.fixture(scope="session")
def spark():
    """Create a SparkSession for testing with Delta Lake support."""
    builder = (
        SparkSession.builder
        .appName("CBTRN02C_Tests")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse-test")
        .config("spark.driver.extraJavaOptions", "-Dderby.system.home=/tmp/derby-test")
    )
    session = configure_spark_with_delta_pip(builder).getOrCreate()
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}")
    yield session
    session.sql(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
    session.stop()


@pytest.fixture(scope="function")
def clean_tables(spark):
    """Drop and recreate all test tables before each test function."""
    tables = [
        "daily_transaction",
        "transaction",
        "card_xref",
        "account",
        "tran_cat_balance",
        "daily_rejects",
    ]
    for table in tables:
        spark.sql(f"DROP TABLE IF EXISTS {TEST_SCHEMA}.{table}")

    spark.sql(f"""
        CREATE TABLE {TEST_SCHEMA}.daily_transaction (
            dalytran_id STRING,
            dalytran_type_cd STRING,
            dalytran_cat_cd INT,
            dalytran_source STRING,
            dalytran_desc STRING,
            dalytran_amt DECIMAL(11,2),
            dalytran_merchant_id BIGINT,
            dalytran_merchant_name STRING,
            dalytran_merchant_city STRING,
            dalytran_merchant_zip STRING,
            dalytran_card_num STRING,
            dalytran_orig_ts STRING,
            dalytran_proc_ts STRING
        ) USING DELTA
    """)

    spark.sql(f"""
        CREATE TABLE {TEST_SCHEMA}.transaction (
            tran_id STRING,
            tran_type_cd STRING,
            tran_cat_cd INT,
            tran_source STRING,
            tran_desc STRING,
            tran_amt DECIMAL(11,2),
            tran_merchant_id BIGINT,
            tran_merchant_name STRING,
            tran_merchant_city STRING,
            tran_merchant_zip STRING,
            tran_card_num STRING,
            tran_orig_ts STRING,
            tran_proc_ts STRING
        ) USING DELTA
    """)

    spark.sql(f"""
        CREATE TABLE {TEST_SCHEMA}.card_xref (
            xref_card_num STRING,
            xref_cust_id BIGINT,
            xref_acct_id BIGINT
        ) USING DELTA
    """)

    spark.sql(f"""
        CREATE TABLE {TEST_SCHEMA}.account (
            acct_id BIGINT,
            acct_active_status STRING,
            acct_curr_bal DECIMAL(12,2),
            acct_credit_limit DECIMAL(12,2),
            acct_cash_credit_limit DECIMAL(12,2),
            acct_open_date STRING,
            acct_expiration_date STRING,
            acct_reissue_date STRING,
            acct_curr_cyc_credit DECIMAL(12,2),
            acct_curr_cyc_debit DECIMAL(12,2),
            acct_addr_zip STRING,
            acct_group_id STRING
        ) USING DELTA
    """)

    spark.sql(f"""
        CREATE TABLE {TEST_SCHEMA}.tran_cat_balance (
            trancat_acct_id BIGINT,
            trancat_type_cd STRING,
            trancat_cd INT,
            tran_cat_bal DECIMAL(11,2)
        ) USING DELTA
    """)

    spark.sql(f"""
        CREATE TABLE {TEST_SCHEMA}.daily_rejects (
            dalytran_id STRING,
            dalytran_type_cd STRING,
            dalytran_cat_cd INT,
            dalytran_source STRING,
            dalytran_desc STRING,
            dalytran_amt DECIMAL(11,2),
            dalytran_merchant_id BIGINT,
            dalytran_merchant_name STRING,
            dalytran_merchant_city STRING,
            dalytran_merchant_zip STRING,
            dalytran_card_num STRING,
            dalytran_orig_ts STRING,
            dalytran_proc_ts STRING,
            reject_reason_code INT,
            reject_reason_desc STRING,
            reject_timestamp TIMESTAMP
        ) USING DELTA
    """)

    yield

    for table in tables:
        spark.sql(f"DROP TABLE IF EXISTS {TEST_SCHEMA}.{table}")
