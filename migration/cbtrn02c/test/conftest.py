"""
Pytest fixtures for CBTRN02C PySpark migration tests.

Provides SparkSession, Delta table setup/teardown, and test data fixtures.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType,
    IntegerType,
    DecimalType,
    TimestampType,
)
from decimal import Decimal


TEST_SCHEMA = "carddemo_test"


@pytest.fixture(scope="session")
def spark():
    """Create a SparkSession for testing with Delta Lake support."""
    session = (
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
        .getOrCreate()
    )
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


DAILY_TRAN_SCHEMA = StructType([
    StructField("dalytran_id", StringType(), False),
    StructField("dalytran_type_cd", StringType(), False),
    StructField("dalytran_cat_cd", IntegerType(), False),
    StructField("dalytran_source", StringType(), True),
    StructField("dalytran_desc", StringType(), True),
    StructField("dalytran_amt", DecimalType(11, 2), False),
    StructField("dalytran_merchant_id", LongType(), True),
    StructField("dalytran_merchant_name", StringType(), True),
    StructField("dalytran_merchant_city", StringType(), True),
    StructField("dalytran_merchant_zip", StringType(), True),
    StructField("dalytran_card_num", StringType(), False),
    StructField("dalytran_orig_ts", StringType(), True),
    StructField("dalytran_proc_ts", StringType(), True),
])

CARD_XREF_SCHEMA = StructType([
    StructField("xref_card_num", StringType(), False),
    StructField("xref_cust_id", LongType(), False),
    StructField("xref_acct_id", LongType(), False),
])

ACCOUNT_SCHEMA = StructType([
    StructField("acct_id", LongType(), False),
    StructField("acct_active_status", StringType(), True),
    StructField("acct_curr_bal", DecimalType(12, 2), False),
    StructField("acct_credit_limit", DecimalType(12, 2), False),
    StructField("acct_cash_credit_limit", DecimalType(12, 2), False),
    StructField("acct_open_date", StringType(), True),
    StructField("acct_expiration_date", StringType(), True),
    StructField("acct_reissue_date", StringType(), True),
    StructField("acct_curr_cyc_credit", DecimalType(12, 2), False),
    StructField("acct_curr_cyc_debit", DecimalType(12, 2), False),
    StructField("acct_addr_zip", StringType(), True),
    StructField("acct_group_id", StringType(), True),
])

TRAN_CAT_BAL_SCHEMA = StructType([
    StructField("trancat_acct_id", LongType(), False),
    StructField("trancat_type_cd", StringType(), False),
    StructField("trancat_cd", IntegerType(), False),
    StructField("tran_cat_bal", DecimalType(11, 2), False),
])


def make_daily_tran(
    tran_id: str,
    card_num: str,
    amt: float,
    type_cd: str = "01",
    cat_cd: int = 5001,
    orig_ts: str = "2026-01-15-10.00.00.000000",
) -> tuple:
    """Helper to create a daily transaction tuple."""
    return (
        tran_id,
        type_cd,
        cat_cd,
        "POS",
        f"Test transaction {tran_id}",
        Decimal(str(amt)),
        900000001,
        "TestMerchant",
        "TestCity",
        "12345",
        card_num,
        orig_ts,
        None,
    )


def make_xref(card_num: str, cust_id: int, acct_id: int) -> tuple:
    """Helper to create a card cross-reference tuple."""
    return (card_num, cust_id, acct_id)


def make_account(
    acct_id: int,
    curr_bal: float = 1000.0,
    credit_limit: float = 10000.0,
    cyc_credit: float = 1000.0,
    cyc_debit: float = 0.0,
    expiration_date: str = "2027-12-31",
) -> tuple:
    """Helper to create an account tuple."""
    return (
        acct_id,
        "Y",
        Decimal(str(curr_bal)),
        Decimal(str(credit_limit)),
        Decimal("2000.00"),
        "2020-01-01",
        expiration_date,
        "2024-01-01",
        Decimal(str(cyc_credit)),
        Decimal(str(cyc_debit)),
        "12345",
        "GOLD",
    )


def make_tran_cat_bal(acct_id: int, type_cd: str, cat_cd: int, bal: float) -> tuple:
    """Helper to create a transaction category balance tuple."""
    return (acct_id, type_cd, cat_cd, Decimal(str(bal)))
