"""
End-to-end integration tests for CBTRN02C PySpark migration.

Tests the complete pipeline: validate -> post -> update accounts ->
update category balances -> write rejects, verifying all outputs together.
"""

import pytest
from decimal import Decimal
from pyspark.sql import functions as F

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cbtrn02c_post_daily_transactions import (
    validate_and_split,
    post_transactions,
    update_account_balances,
    update_tran_cat_balance,
    write_rejects,
    REJECT_INVALID_CARD,
    REJECT_OVERLIMIT,
    REJECT_EXPIRED,
)
from conftest import (
    TEST_SCHEMA,
    DAILY_TRAN_SCHEMA,
    CARD_XREF_SCHEMA,
    ACCOUNT_SCHEMA,
    TRAN_CAT_BAL_SCHEMA,
    make_daily_tran,
    make_xref,
    make_account,
    make_tran_cat_bal,
)


def _run_full_pipeline(spark, daily_rows, xref_rows, acct_rows, tcb_rows=None):
    """Execute the full CBTRN02C pipeline and return all output tables."""
    daily_tran = spark.createDataFrame(daily_rows, schema=DAILY_TRAN_SCHEMA)
    card_xref = spark.createDataFrame(xref_rows, schema=CARD_XREF_SCHEMA)

    for row in acct_rows:
        spark.createDataFrame([row], schema=ACCOUNT_SCHEMA).write.format(
            "delta"
        ).mode("append").saveAsTable(f"{TEST_SCHEMA}.account")

    if tcb_rows:
        for row in tcb_rows:
            spark.createDataFrame([row], schema=TRAN_CAT_BAL_SCHEMA).write.format(
                "delta"
            ).mode("append").saveAsTable(f"{TEST_SCHEMA}.tran_cat_balance")

    account = spark.table(f"{TEST_SCHEMA}.account")
    valid, rejects = validate_and_split(daily_tran, card_xref, account)
    valid.cache()
    rejects.cache()

    import cbtrn02c_post_daily_transactions as mod
    original_schema = mod.SCHEMA
    mod.SCHEMA = TEST_SCHEMA
    try:
        valid_count = valid.count()
        reject_count = rejects.count()

        if valid_count > 0:
            post_transactions(spark, valid)
            update_account_balances(spark, valid)
            update_tran_cat_balance(spark, valid)

        if reject_count > 0:
            write_rejects(spark, rejects)
    finally:
        mod.SCHEMA = original_schema

    valid.unpersist()
    rejects.unpersist()

    return {
        "transaction": spark.table(f"{TEST_SCHEMA}.transaction"),
        "account": spark.table(f"{TEST_SCHEMA}.account"),
        "tran_cat_balance": spark.table(f"{TEST_SCHEMA}.tran_cat_balance"),
        "daily_rejects": spark.table(f"{TEST_SCHEMA}.daily_rejects"),
        "valid_count": valid_count,
        "reject_count": reject_count,
    }


class TestEndToEndAllValid:
    """End-to-end tests where all transactions are valid."""

    def test_single_valid_transaction_full_flow(self, spark, clean_tables):
        """Single valid transaction updates all output tables correctly."""
        result = _run_full_pipeline(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 250.00, type_cd="01", cat_cd=5001)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
        )

        assert result["valid_count"] == 1
        assert result["reject_count"] == 0

        assert result["transaction"].count() == 1
        tran = result["transaction"].collect()[0]
        assert tran["tran_id"] == "TXN001"
        assert tran["tran_amt"] == Decimal("250.00")

        acct = result["account"].filter(F.col("acct_id") == 80000000001).collect()[0]
        assert acct["acct_curr_bal"] == Decimal("1250.00")
        assert acct["acct_curr_cyc_credit"] == Decimal("1250.00")

        assert result["tran_cat_balance"].count() == 1
        tcb = result["tran_cat_balance"].collect()[0]
        assert tcb["tran_cat_bal"] == Decimal("250.00")

        assert result["daily_rejects"].count() == 0

    def test_multiple_accounts_full_flow(self, spark, clean_tables):
        """Transactions across multiple accounts all processed correctly."""
        result = _run_full_pipeline(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001),
                make_daily_tran("TXN002", "4222222222222222", 200.00, type_cd="01", cat_cd=5001),
                make_daily_tran("TXN003", "4333333333333333", 300.00, type_cd="02", cat_cd=5002),
            ],
            [
                make_xref("4111111111111111", 100000001, 80000000001),
                make_xref("4222222222222222", 100000002, 80000000002),
                make_xref("4333333333333333", 100000003, 80000000003),
            ],
            [
                make_account(80000000001, curr_bal=500.0, cyc_credit=500.0, cyc_debit=0.0),
                make_account(80000000002, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0),
                make_account(80000000003, curr_bal=2000.0, cyc_credit=2000.0, cyc_debit=0.0),
            ],
        )

        assert result["valid_count"] == 3
        assert result["transaction"].count() == 3

        acct1 = result["account"].filter(F.col("acct_id") == 80000000001).collect()[0]
        assert acct1["acct_curr_bal"] == Decimal("600.00")

        acct2 = result["account"].filter(F.col("acct_id") == 80000000002).collect()[0]
        assert acct2["acct_curr_bal"] == Decimal("1200.00")

        acct3 = result["account"].filter(F.col("acct_id") == 80000000003).collect()[0]
        assert acct3["acct_curr_bal"] == Decimal("2300.00")

        assert result["tran_cat_balance"].count() == 2
        assert result["daily_rejects"].count() == 0


class TestEndToEndAllRejected:
    """End-to-end tests where all transactions are rejected."""

    def test_all_invalid_cards(self, spark, clean_tables):
        """All transactions with invalid cards: nothing posted, all rejected."""
        result = _run_full_pipeline(
            spark,
            [
                make_daily_tran("TXN001", "9999999999999999", 100.00),
                make_daily_tran("TXN002", "8888888888888888", 200.00),
            ],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
        )

        assert result["valid_count"] == 0
        assert result["reject_count"] == 2
        assert result["transaction"].count() == 0
        assert result["daily_rejects"].count() == 2

        acct = result["account"].filter(F.col("acct_id") == 80000000001).collect()[0]
        assert acct["acct_curr_bal"] == Decimal("1000.00")


class TestEndToEndMixed:
    """End-to-end tests with a mix of valid and rejected transactions."""

    def test_mixed_valid_and_rejected(self, spark, clean_tables):
        """Mix of valid, invalid-card, overlimit, and expired transactions."""
        result = _run_full_pipeline(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001,
                                orig_ts="2026-01-15-10.00.00.000000"),
                make_daily_tran("TXN002", "4222222222222222", 200.00, type_cd="01", cat_cd=5001,
                                orig_ts="2026-01-15-11.00.00.000000"),
                make_daily_tran("TXN003", "9999999999999999", 300.00, type_cd="01", cat_cd=5001,
                                orig_ts="2026-01-15-12.00.00.000000"),
                make_daily_tran("TXN004", "4333333333333333", 5000.00, type_cd="01", cat_cd=5001,
                                orig_ts="2026-01-15-13.00.00.000000"),
            ],
            [
                make_xref("4111111111111111", 100000001, 80000000001),
                make_xref("4222222222222222", 100000002, 80000000002),
                make_xref("4333333333333333", 100000003, 80000000003),
            ],
            [
                make_account(80000000001, curr_bal=500.0, cyc_credit=500.0, cyc_debit=0.0),
                make_account(80000000002, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0),
                make_account(80000000003, curr_bal=0.0, credit_limit=3000.0, cyc_credit=0.0, cyc_debit=0.0),
            ],
        )

        assert result["valid_count"] == 2
        assert result["reject_count"] == 2

        assert result["transaction"].count() == 2
        posted_ids = sorted([r["tran_id"] for r in result["transaction"].collect()])
        assert posted_ids == ["TXN001", "TXN002"]

        assert result["daily_rejects"].count() == 2
        reject_codes = sorted([r["reject_reason_code"] for r in result["daily_rejects"].collect()])
        assert REJECT_INVALID_CARD in reject_codes
        assert REJECT_OVERLIMIT in reject_codes

        acct1 = result["account"].filter(F.col("acct_id") == 80000000001).collect()[0]
        assert acct1["acct_curr_bal"] == Decimal("600.00")

        acct2 = result["account"].filter(F.col("acct_id") == 80000000002).collect()[0]
        assert acct2["acct_curr_bal"] == Decimal("1200.00")

        acct3 = result["account"].filter(F.col("acct_id") == 80000000003).collect()[0]
        assert acct3["acct_curr_bal"] == Decimal("0.00")

    def test_sample_data_scenario(self, spark, clean_tables):
        """Replicate the scenario from 02_sample_data.sql for regression testing."""
        xref_rows = [
            make_xref("4111111111111111", 100000001, 80000000001),
            make_xref("4222222222222222", 100000002, 80000000002),
            make_xref("4333333333333333", 100000003, 80000000003),
            make_xref("4444444444444444", 100000004, 80000000004),
            make_xref("4555555555555555", 100000005, 80000000005),
        ]

        acct_rows = [
            make_account(80000000001, curr_bal=1500.0, credit_limit=10000.0,
                         cyc_credit=1500.0, cyc_debit=0.0, expiration_date="2027-12-31"),
            make_account(80000000002, curr_bal=3200.0, credit_limit=15000.0,
                         cyc_credit=3200.0, cyc_debit=0.0, expiration_date="2028-06-30"),
            make_account(80000000003, curr_bal=8500.0, credit_limit=9000.0,
                         cyc_credit=8500.0, cyc_debit=0.0, expiration_date="2027-03-31"),
            make_account(80000000004, curr_bal=250.0, credit_limit=5000.0,
                         cyc_credit=250.0, cyc_debit=0.0, expiration_date="2025-06-30"),
            make_account(80000000005, curr_bal=0.0, credit_limit=20000.0,
                         cyc_credit=0.0, cyc_debit=0.0, expiration_date="2029-12-31"),
        ]

        tcb_rows = [
            make_tran_cat_bal(80000000001, "01", 5001, 800.0),
            make_tran_cat_bal(80000000001, "02", 5002, 200.0),
            make_tran_cat_bal(80000000002, "01", 5001, 1500.0),
            make_tran_cat_bal(80000000003, "01", 5001, 4000.0),
            make_tran_cat_bal(80000000005, "01", 5001, 0.0),
        ]

        daily_rows = [
            make_daily_tran("TXN0000000000001", "4111111111111111", 125.50,
                            type_cd="01", cat_cd=5001, orig_ts="2026-01-15-10.30.00.000000"),
            make_daily_tran("TXN0000000000002", "4111111111111111", 75.25,
                            type_cd="02", cat_cd=5002, orig_ts="2026-01-15-11.00.00.000000"),
            make_daily_tran("TXN0000000000003", "4222222222222222", 1250.00,
                            type_cd="01", cat_cd=5001, orig_ts="2026-01-15-09.15.00.000000"),
            make_daily_tran("TXN0000000000004", "9999999999999999", 55.00,
                            type_cd="01", cat_cd=5001, orig_ts="2026-01-15-14.00.00.000000"),
            make_daily_tran("TXN0000000000005", "4333333333333333", 500.00,
                            type_cd="01", cat_cd=5001, orig_ts="2026-01-15-16.45.00.000000"),
            make_daily_tran("TXN0000000000006", "4444444444444444", 85.00,
                            type_cd="01", cat_cd=5001, orig_ts="2026-01-15-19.00.00.000000"),
            make_daily_tran("TXN0000000000007", "4555555555555555", 3500.00,
                            type_cd="01", cat_cd=5001, orig_ts="2026-01-15-08.00.00.000000"),
            make_daily_tran("TXN0000000000008", "4555555555555555", -150.00,
                            type_cd="01", cat_cd=5001, orig_ts="2026-01-15-08.30.00.000000"),
            make_daily_tran("TXN0000000000009", "4222222222222222", 320.00,
                            type_cd="02", cat_cd=5002, orig_ts="2026-01-15-12.00.00.000000"),
            make_daily_tran("TXN0000000000010", "4111111111111111", 45.00,
                            type_cd="01", cat_cd=5001, orig_ts="2026-01-15-15.00.00.000000"),
        ]

        result = _run_full_pipeline(spark, daily_rows, xref_rows, acct_rows, tcb_rows)

        assert result["valid_count"] == 7
        assert result["reject_count"] == 3

        assert result["transaction"].count() == 7

        assert result["daily_rejects"].count() == 3
        reject_ids = sorted([r["dalytran_id"] for r in result["daily_rejects"].collect()])
        assert "TXN0000000000004" in reject_ids
        assert "TXN0000000000005" in reject_ids
        assert "TXN0000000000006" in reject_ids

        acct1 = result["account"].filter(F.col("acct_id") == 80000000001).collect()[0]
        assert acct1["acct_curr_bal"] == Decimal("1745.75")

        acct2 = result["account"].filter(F.col("acct_id") == 80000000002).collect()[0]
        assert acct2["acct_curr_bal"] == Decimal("4770.00")

        acct5 = result["account"].filter(F.col("acct_id") == 80000000005).collect()[0]
        assert acct5["acct_curr_bal"] == Decimal("3350.00")


class TestEndToEndWithPreExistingData:
    """End-to-end tests with pre-existing transaction category balances."""

    def test_updates_existing_and_inserts_new_categories(self, spark, clean_tables):
        """Pipeline should update existing category balances and insert new ones."""
        result = _run_full_pipeline(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001),
                make_daily_tran("TXN002", "4111111111111111", 200.00, type_cd="02", cat_cd=5002),
            ],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
            [make_tran_cat_bal(80000000001, "01", 5001, 500.0)],
        )

        assert result["tran_cat_balance"].count() == 2

        rows = {
            (r["trancat_type_cd"], r["trancat_cd"]): r["tran_cat_bal"]
            for r in result["tran_cat_balance"].collect()
        }
        assert rows[("01", 5001)] == Decimal("600.00")
        assert rows[("02", 5002)] == Decimal("200.00")


class TestEndToEndEmptyInput:
    """End-to-end tests with empty input."""

    def test_no_daily_transactions(self, spark, clean_tables):
        """Empty daily transaction input should produce no output changes."""
        daily_tran = spark.createDataFrame([], schema=DAILY_TRAN_SCHEMA)
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )

        for row in [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)]:
            spark.createDataFrame([row], schema=ACCOUNT_SCHEMA).write.format(
                "delta"
            ).mode("append").saveAsTable(f"{TEST_SCHEMA}.account")

        account = spark.table(f"{TEST_SCHEMA}.account")
        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 0
        assert rejects.count() == 0

        acct = spark.table(f"{TEST_SCHEMA}.account").collect()[0]
        assert acct["acct_curr_bal"] == Decimal("1000.00")
