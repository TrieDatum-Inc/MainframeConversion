"""
Test cases for CBTRN02C account balance update logic.

Tests cover the update_account_balances function which replicates COBOL paragraph
2800-UPDATE-ACCOUNT-REC:
    ADD DALYTRAN-AMT TO ACCT-CURR-BAL
    IF DALYTRAN-AMT >= 0
        ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT
    ELSE
        ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT
"""

import pytest
from decimal import Decimal
from pyspark.sql import functions as F

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cbtrn02c_post_daily_transactions import (
    validate_and_split,
    update_account_balances,
)
from conftest import (
    TEST_SCHEMA,
    DAILY_TRAN_SCHEMA,
    CARD_XREF_SCHEMA,
    ACCOUNT_SCHEMA,
    make_daily_tran,
    make_xref,
    make_account,
)


class TestAccountBalanceUpdate:
    """Test account balance updates after posting valid transactions."""

    def _setup_and_run(self, spark, daily_rows, xref_rows, acct_rows):
        """Helper: load data, validate, update accounts, return account table."""
        daily_tran = spark.createDataFrame(daily_rows, schema=DAILY_TRAN_SCHEMA)
        card_xref = spark.createDataFrame(xref_rows, schema=CARD_XREF_SCHEMA)

        for row in acct_rows:
            spark.createDataFrame([row], schema=ACCOUNT_SCHEMA).write.format(
                "delta"
            ).mode("append").saveAsTable(f"{TEST_SCHEMA}.account")

        account = spark.table(f"{TEST_SCHEMA}.account")
        valid, _ = validate_and_split(daily_tran, card_xref, account)

        import cbtrn02c_post_daily_transactions as mod
        original_schema = mod.SCHEMA
        mod.SCHEMA = TEST_SCHEMA
        try:
            update_account_balances(spark, valid)
        finally:
            mod.SCHEMA = original_schema

        return spark.table(f"{TEST_SCHEMA}.account")

    def test_single_purchase_updates_balance(self, spark, clean_tables):
        """Single purchase: bal increases, cyc_credit increases, cyc_debit unchanged."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 250.00)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
        )

        row = result.filter(F.col("acct_id") == 80000000001).collect()[0]
        assert row["acct_curr_bal"] == Decimal("1250.00")
        assert row["acct_curr_cyc_credit"] == Decimal("1250.00")
        assert row["acct_curr_cyc_debit"] == Decimal("0.00")

    def test_refund_updates_debit(self, spark, clean_tables):
        """Refund (negative amount): bal decreases, cyc_debit increases, cyc_credit unchanged."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", -200.00)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
        )

        row = result.filter(F.col("acct_id") == 80000000001).collect()[0]
        assert row["acct_curr_bal"] == Decimal("800.00")
        assert row["acct_curr_cyc_credit"] == Decimal("1000.00")
        assert row["acct_curr_cyc_debit"] == Decimal("-200.00")

    def test_multiple_purchases_same_account(self, spark, clean_tables):
        """Multiple purchases on same account: all aggregated in single update."""
        result = self._setup_and_run(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00),
                make_daily_tran("TXN002", "4111111111111111", 200.00),
                make_daily_tran("TXN003", "4111111111111111", 50.00),
            ],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
        )

        row = result.filter(F.col("acct_id") == 80000000001).collect()[0]
        assert row["acct_curr_bal"] == Decimal("1350.00")
        assert row["acct_curr_cyc_credit"] == Decimal("1350.00")
        assert row["acct_curr_cyc_debit"] == Decimal("0.00")

    def test_mixed_purchases_and_refunds(self, spark, clean_tables):
        """Mix of purchases and refunds splits correctly to credit and debit."""
        result = self._setup_and_run(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 300.00),
                make_daily_tran("TXN002", "4111111111111111", -100.00),
                make_daily_tran("TXN003", "4111111111111111", 50.00),
            ],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
        )

        row = result.filter(F.col("acct_id") == 80000000001).collect()[0]
        assert row["acct_curr_bal"] == Decimal("1250.00")
        assert row["acct_curr_cyc_credit"] == Decimal("1350.00")
        assert row["acct_curr_cyc_debit"] == Decimal("-100.00")

    def test_multiple_accounts_updated_independently(self, spark, clean_tables):
        """Transactions on different accounts update each independently."""
        result = self._setup_and_run(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00),
                make_daily_tran("TXN002", "4222222222222222", 500.00),
            ],
            [
                make_xref("4111111111111111", 100000001, 80000000001),
                make_xref("4222222222222222", 100000002, 80000000002),
            ],
            [
                make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0),
                make_account(80000000002, curr_bal=2000.0, cyc_credit=2000.0, cyc_debit=0.0),
            ],
        )

        row1 = result.filter(F.col("acct_id") == 80000000001).collect()[0]
        assert row1["acct_curr_bal"] == Decimal("1100.00")

        row2 = result.filter(F.col("acct_id") == 80000000002).collect()[0]
        assert row2["acct_curr_bal"] == Decimal("2500.00")

    def test_zero_amount_no_balance_change(self, spark, clean_tables):
        """Zero amount transaction should not change balances."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 0.00)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
        )

        row = result.filter(F.col("acct_id") == 80000000001).collect()[0]
        assert row["acct_curr_bal"] == Decimal("1000.00")
        assert row["acct_curr_cyc_credit"] == Decimal("1000.00")
        assert row["acct_curr_cyc_debit"] == Decimal("0.00")

    def test_account_without_transactions_unchanged(self, spark, clean_tables):
        """Account with no transactions should remain unchanged after merge."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 100.00)],
            [
                make_xref("4111111111111111", 100000001, 80000000001),
            ],
            [
                make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0),
                make_account(80000000002, curr_bal=5000.0, cyc_credit=5000.0, cyc_debit=0.0),
            ],
        )

        row2 = result.filter(F.col("acct_id") == 80000000002).collect()[0]
        assert row2["acct_curr_bal"] == Decimal("5000.00")
        assert row2["acct_curr_cyc_credit"] == Decimal("5000.00")

    def test_large_amount_precision(self, spark, clean_tables):
        """Large amount with decimal precision should be handled correctly."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 99999999.99)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=0.0, credit_limit=999999999.0, cyc_credit=0.0, cyc_debit=0.0)],
        )

        row = result.filter(F.col("acct_id") == 80000000001).collect()[0]
        assert row["acct_curr_bal"] == Decimal("99999999.99")

    def test_small_decimal_amount(self, spark, clean_tables):
        """Small decimal amount (0.01) should be applied correctly."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 0.01)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, curr_bal=1000.0, cyc_credit=1000.0, cyc_debit=0.0)],
        )

        row = result.filter(F.col("acct_id") == 80000000001).collect()[0]
        assert row["acct_curr_bal"] == Decimal("1000.01")
