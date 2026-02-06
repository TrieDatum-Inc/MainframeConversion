"""
Shared test helpers, schemas, and builder functions for CBTRN02C tests.
"""

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType,
    IntegerType,
    DecimalType,
)
from decimal import Decimal


TEST_SCHEMA = "carddemo_test"

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
    return (card_num, cust_id, acct_id)


def make_account(
    acct_id: int,
    curr_bal: float = 1000.0,
    credit_limit: float = 10000.0,
    cyc_credit: float = 1000.0,
    cyc_debit: float = 0.0,
    expiration_date: str = "2027-12-31",
) -> tuple:
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
    return (acct_id, type_cd, cat_cd, Decimal(str(bal)))
