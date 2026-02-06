"""
Test cases for CBTRN02C transaction category balance update logic.

Tests cover the update_tran_cat_balance function which replicates COBOL paragraphs
2700-UPDATE-TCATBAL, 2700-A-CREATE-TCATBAL-REC, 2700-B-UPDATE-TCATBAL-REC:
    - Read TCATBAL by composite key (acct_id, type_cd, cat_cd)
    - If record exists: ADD DALYTRAN-AMT TO TRAN-CAT-BAL, REWRITE
    - If record not found: INITIALIZE new record, WRITE with amt as balance
"""

import pytest
from decimal import Decimal
from pyspark.sql import functions as F

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cbtrn02c_post_daily_transactions import (
    validate_and_split,
    update_tran_cat_balance,
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


class TestTranCatBalanceUpdate:
    """Test transaction category balance MERGE (insert/update) logic."""

    def _setup_and_run(self, spark, daily_rows, xref_rows, acct_rows, tcb_rows=None):
        """Helper: load data, validate, update tran cat balances, return table."""
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
        valid, _ = validate_and_split(daily_tran, card_xref, account)

        import cbtrn02c_post_daily_transactions as mod
        original_schema = mod.SCHEMA
        mod.SCHEMA = TEST_SCHEMA
        try:
            update_tran_cat_balance(spark, valid)
        finally:
            mod.SCHEMA = original_schema

        return spark.table(f"{TEST_SCHEMA}.tran_cat_balance")

    def test_new_category_balance_inserted(self, spark, clean_tables):
        """New (acct, type, cat) combination should INSERT a new row."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
        )

        assert result.count() == 1
        row = result.collect()[0]
        assert row["trancat_acct_id"] == 80000000001
        assert row["trancat_type_cd"] == "01"
        assert row["trancat_cd"] == 5001
        assert row["tran_cat_bal"] == Decimal("100.00")

    def test_existing_category_balance_updated(self, spark, clean_tables):
        """Existing (acct, type, cat) combination should UPDATE the balance."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 250.00, type_cd="01", cat_cd=5001)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
            [make_tran_cat_bal(80000000001, "01", 5001, 500.00)],
        )

        assert result.count() == 1
        row = result.collect()[0]
        assert row["tran_cat_bal"] == Decimal("750.00")

    def test_multiple_transactions_same_category(self, spark, clean_tables):
        """Multiple transactions with same (acct, type, cat) should aggregate."""
        result = self._setup_and_run(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001),
                make_daily_tran("TXN002", "4111111111111111", 200.00, type_cd="01", cat_cd=5001),
            ],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
            [make_tran_cat_bal(80000000001, "01", 5001, 500.00)],
        )

        assert result.count() == 1
        row = result.collect()[0]
        assert row["tran_cat_bal"] == Decimal("800.00")

    def test_different_categories_create_separate_rows(self, spark, clean_tables):
        """Different category codes on same account should create separate rows."""
        result = self._setup_and_run(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001),
                make_daily_tran("TXN002", "4111111111111111", 200.00, type_cd="01", cat_cd=5002),
            ],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
        )

        assert result.count() == 2
        rows = {r["trancat_cd"]: r["tran_cat_bal"] for r in result.collect()}
        assert rows[5001] == Decimal("100.00")
        assert rows[5002] == Decimal("200.00")

    def test_different_type_codes_create_separate_rows(self, spark, clean_tables):
        """Different type codes on same account/category should create separate rows."""
        result = self._setup_and_run(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001),
                make_daily_tran("TXN002", "4111111111111111", 200.00, type_cd="02", cat_cd=5001),
            ],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
        )

        assert result.count() == 2
        rows = {r["trancat_type_cd"]: r["tran_cat_bal"] for r in result.collect()}
        assert rows["01"] == Decimal("100.00")
        assert rows["02"] == Decimal("200.00")

    def test_mix_of_new_and_existing_categories(self, spark, clean_tables):
        """Some categories already exist, some are new - both handled correctly."""
        result = self._setup_and_run(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001),
                make_daily_tran("TXN002", "4111111111111111", 200.00, type_cd="01", cat_cd=5002),
            ],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
            [make_tran_cat_bal(80000000001, "01", 5001, 500.00)],
        )

        assert result.count() == 2
        rows = {r["trancat_cd"]: r["tran_cat_bal"] for r in result.collect()}
        assert rows[5001] == Decimal("600.00")
        assert rows[5002] == Decimal("200.00")

    def test_refund_reduces_category_balance(self, spark, clean_tables):
        """Negative amount (refund) should reduce the category balance."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", -150.00, type_cd="01", cat_cd=5001)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
            [make_tran_cat_bal(80000000001, "01", 5001, 500.00)],
        )

        row = result.collect()[0]
        assert row["tran_cat_bal"] == Decimal("350.00")

    def test_multiple_accounts_independent_categories(self, spark, clean_tables):
        """Category balances for different accounts should be independent."""
        result = self._setup_and_run(
            spark,
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001),
                make_daily_tran("TXN002", "4222222222222222", 200.00, type_cd="01", cat_cd=5001),
            ],
            [
                make_xref("4111111111111111", 100000001, 80000000001),
                make_xref("4222222222222222", 100000002, 80000000002),
            ],
            [
                make_account(80000000001),
                make_account(80000000002),
            ],
        )

        assert result.count() == 2
        rows = {r["trancat_acct_id"]: r["tran_cat_bal"] for r in result.collect()}
        assert rows[80000000001] == Decimal("100.00")
        assert rows[80000000002] == Decimal("200.00")

    def test_existing_unrelated_categories_preserved(self, spark, clean_tables):
        """Pre-existing category balances not touched by transactions should remain."""
        result = self._setup_and_run(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
            [
                make_tran_cat_bal(80000000001, "01", 5001, 500.00),
                make_tran_cat_bal(80000000001, "02", 5003, 999.00),
            ],
        )

        assert result.count() == 2
        rows = {(r["trancat_type_cd"], r["trancat_cd"]): r["tran_cat_bal"] for r in result.collect()}
        assert rows[("01", 5001)] == Decimal("600.00")
        assert rows[("02", 5003)] == Decimal("999.00")
