"""
Edge case tests for CBTRN02C PySpark migration.

Tests cover boundary conditions, unusual inputs, and corner cases
that may not be typical in production but should be handled correctly.
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
    REJECT_ACCOUNT_NOT_FOUND,
    REJECT_OVERLIMIT,
    REJECT_EXPIRED,
)
from helpers import (
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


class TestBoundaryAmounts:
    """Test boundary conditions for transaction amounts."""

    def test_one_cent_transaction(self, spark, clean_tables):
        """Smallest meaningful amount (0.01) should process correctly."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 0.01)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, curr_bal=0.0, credit_limit=10000.0, cyc_credit=0.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 1
        assert rejects.count() == 0

    def test_zero_credit_limit_all_positive_rejected(self, spark, clean_tables):
        """Zero credit limit should reject any positive transaction."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 0.01)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, curr_bal=0.0, credit_limit=0.0, cyc_credit=0.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 0
        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_OVERLIMIT

    def test_exact_credit_limit_boundary(self, spark, clean_tables):
        """Transaction that brings balance exactly to credit limit should be valid."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 5000.00)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, credit_limit=5000.0, cyc_credit=0.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 1
        assert rejects.count() == 0

    def test_one_cent_over_limit_rejected(self, spark, clean_tables):
        """One cent over credit limit should be rejected."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 5000.01)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, credit_limit=5000.0, cyc_credit=0.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 0
        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_OVERLIMIT


class TestBoundaryDates:
    """Test boundary conditions for expiration date validation."""

    def test_expiration_date_exactly_one_day_after_transaction(self, spark, clean_tables):
        """Account expiring one day after transaction should be valid."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2026-01-14-10.00.00.000000")],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, expiration_date="2026-01-15")],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 1
        assert rejects.count() == 0

    def test_expiration_date_one_day_before_transaction(self, spark, clean_tables):
        """Account expired one day before transaction should be rejected."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2026-01-16-10.00.00.000000")],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, expiration_date="2026-01-15")],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 0
        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_EXPIRED

    def test_year_end_boundary(self, spark, clean_tables):
        """Transaction on Dec 31 with expiration Dec 31 should be valid."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2026-12-31-23.59.59.000000")],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, expiration_date="2026-12-31")],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 1
        assert rejects.count() == 0

    def test_jan1_after_dec31_expiration(self, spark, clean_tables):
        """Transaction on Jan 1 with Dec 31 expiration should be rejected."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2027-01-01-00.00.00.000000")],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, expiration_date="2026-12-31")],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 0
        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_EXPIRED


class TestMultipleCardsPerAccount:
    """Test scenarios where multiple cards map to the same account."""

    def test_two_cards_same_account_both_valid(self, spark, clean_tables):
        """Two different cards on the same account should both be processed."""
        daily_tran = spark.createDataFrame(
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2026-01-15-10.00.00.000000"),
                make_daily_tran("TXN002", "4222222222222222", 200.00, orig_ts="2026-01-15-11.00.00.000000"),
            ],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [
                make_xref("4111111111111111", 100000001, 80000000001),
                make_xref("4222222222222222", 100000002, 80000000001),
            ],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, curr_bal=0.0, credit_limit=10000.0, cyc_credit=0.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 2
        assert rejects.count() == 0

    def test_two_cards_same_account_cumulative_overlimit(self, spark, clean_tables):
        """Two cards on same account: cumulative amount exceeds limit."""
        daily_tran = spark.createDataFrame(
            [
                make_daily_tran("TXN001", "4111111111111111", 3000.00, orig_ts="2026-01-15-10.00.00.000000"),
                make_daily_tran("TXN002", "4222222222222222", 3000.00, orig_ts="2026-01-15-11.00.00.000000"),
            ],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [
                make_xref("4111111111111111", 100000001, 80000000001),
                make_xref("4222222222222222", 100000002, 80000000001),
            ],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, credit_limit=5000.0, cyc_credit=0.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 1
        assert rejects.count() == 1

        valid_row = valid.select("dalytran_id").collect()[0]
        assert valid_row["dalytran_id"] == "TXN001"

        reject_row = rejects.collect()[0]
        assert reject_row["dalytran_id"] == "TXN002"
        assert reject_row["reject_reason_code"] == REJECT_OVERLIMIT


class TestHighVolumeProcessing:
    """Test with larger datasets to verify scalability."""

    def test_fifty_valid_transactions(self, spark, clean_tables):
        """50 valid transactions should all be processed correctly."""
        daily_rows = [
            make_daily_tran(f"TXN{i:03d}", "4111111111111111", 10.00,
                            orig_ts=f"2026-01-15-{(i % 24):02d}.{(i % 60):02d}.00.000000")
            for i in range(1, 51)
        ]
        daily_tran = spark.createDataFrame(daily_rows, schema=DAILY_TRAN_SCHEMA)
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, curr_bal=0.0, credit_limit=100000.0, cyc_credit=0.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 50
        assert rejects.count() == 0

    def test_ten_accounts_ten_transactions_each(self, spark, clean_tables):
        """10 accounts with 10 transactions each should all be processed."""
        daily_rows = []
        xref_rows = []
        acct_rows = []

        for a in range(10):
            card_num = f"41111111111111{a:02d}"
            acct_id = 80000000001 + a
            xref_rows.append(make_xref(card_num, 100000001 + a, acct_id))
            acct_rows.append(make_account(acct_id, curr_bal=0.0, credit_limit=100000.0,
                                          cyc_credit=0.0, cyc_debit=0.0))
            for t in range(10):
                daily_rows.append(
                    make_daily_tran(f"TXN{a:02d}{t:02d}", card_num, 50.00,
                                   orig_ts=f"2026-01-15-{(t % 24):02d}.{(t % 60):02d}.00.000000")
                )

        daily_tran = spark.createDataFrame(daily_rows, schema=DAILY_TRAN_SCHEMA)
        card_xref = spark.createDataFrame(xref_rows, schema=CARD_XREF_SCHEMA)
        account = spark.createDataFrame(acct_rows, schema=ACCOUNT_SCHEMA)

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 100
        assert rejects.count() == 0


class TestTransactionTypesAndCategories:
    """Test different transaction type codes and category codes."""

    def test_all_standard_type_codes(self, spark, clean_tables):
        """Multiple transaction type codes should all be accepted."""
        daily_tran = spark.createDataFrame(
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01"),
                make_daily_tran("TXN002", "4111111111111111", 100.00, type_cd="02"),
                make_daily_tran("TXN003", "4111111111111111", 100.00, type_cd="03"),
            ],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 3
        assert rejects.count() == 0

    def test_different_category_codes_tracked_separately(self, spark, clean_tables):
        """Different category codes should create separate tran_cat_balance rows."""
        daily_rows = [
            make_daily_tran("TXN001", "4111111111111111", 100.00, type_cd="01", cat_cd=5001),
            make_daily_tran("TXN002", "4111111111111111", 200.00, type_cd="01", cat_cd=5002),
            make_daily_tran("TXN003", "4111111111111111", 300.00, type_cd="01", cat_cd=5003),
        ]

        for row in [make_account(80000000001, curr_bal=0.0, credit_limit=10000.0,
                                  cyc_credit=0.0, cyc_debit=0.0)]:
            spark.createDataFrame([row], schema=ACCOUNT_SCHEMA).write.format(
                "delta"
            ).mode("append").saveAsTable(f"{TEST_SCHEMA}.account")

        daily_tran = spark.createDataFrame(daily_rows, schema=DAILY_TRAN_SCHEMA)
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.table(f"{TEST_SCHEMA}.account")
        valid, _ = validate_and_split(daily_tran, card_xref, account)

        import cbtrn02c_post_daily_transactions as mod
        original_schema = mod.SCHEMA
        mod.SCHEMA = TEST_SCHEMA
        try:
            update_tran_cat_balance(spark, valid)
        finally:
            mod.SCHEMA = original_schema

        result = spark.table(f"{TEST_SCHEMA}.tran_cat_balance")
        assert result.count() == 3

        rows = {r["trancat_cd"]: r["tran_cat_bal"] for r in result.collect()}
        assert rows[5001] == Decimal("100.00")
        assert rows[5002] == Decimal("200.00")
        assert rows[5003] == Decimal("300.00")


class TestNullAndMissingFields:
    """Test handling of null/optional fields in transactions."""

    def test_null_optional_fields_accepted(self, spark, clean_tables):
        """Transactions with null optional fields should still be valid."""
        daily_tran = spark.createDataFrame(
            [(
                "TXN001", "01", 5001, None, None,
                Decimal("100.00"), None, None,
                None, None, "4111111111111111",
                "2026-01-15-10.00.00.000000", None,
            )],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 1
        assert rejects.count() == 0

    def test_null_merchant_fields_posted(self, spark, clean_tables):
        """Null merchant fields should be preserved when posting."""
        daily_tran = spark.createDataFrame(
            [(
                "TXN001", "01", 5001, None, None,
                Decimal("100.00"), None, None,
                None, None, "4111111111111111",
                "2026-01-15-10.00.00.000000", None,
            )],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, _ = validate_and_split(daily_tran, card_xref, account)

        import cbtrn02c_post_daily_transactions as mod
        original_schema = mod.SCHEMA
        mod.SCHEMA = TEST_SCHEMA
        try:
            post_transactions(spark, valid)
        finally:
            mod.SCHEMA = original_schema

        row = spark.table(f"{TEST_SCHEMA}.transaction").collect()[0]
        assert row["tran_merchant_id"] is None
        assert row["tran_merchant_name"] is None
        assert row["tran_merchant_city"] is None
        assert row["tran_merchant_zip"] is None


class TestDuplicateTransactionIds:
    """Test handling of duplicate transaction IDs in daily input."""

    def test_duplicate_tran_ids_both_processed(self, spark, clean_tables):
        """Duplicate transaction IDs in input should both be processed (no dedup)."""
        daily_tran = spark.createDataFrame(
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2026-01-15-10.00.00.000000"),
                make_daily_tran("TXN001", "4111111111111111", 200.00, orig_ts="2026-01-15-11.00.00.000000"),
            ],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)
        assert valid.count() == 2
        assert rejects.count() == 0
