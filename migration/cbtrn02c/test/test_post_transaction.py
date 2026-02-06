"""
Test cases for CBTRN02C transaction posting logic.

Tests cover the post_transactions function which replicates COBOL paragraph
2000-POST-TRANSACTION and 2900-WRITE-TRANSACTION-FILE.
"""

import pytest
from decimal import Decimal
from pyspark.sql import functions as F

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cbtrn02c_post_daily_transactions import validate_and_split, post_transactions
from conftest import (
    TEST_SCHEMA,
    DAILY_TRAN_SCHEMA,
    CARD_XREF_SCHEMA,
    ACCOUNT_SCHEMA,
    make_daily_tran,
    make_xref,
    make_account,
)


class TestPostTransactions:
    """Test writing valid transactions to the transaction master table."""

    def test_single_valid_transaction_posted(self, spark, clean_tables):
        """A single valid transaction should appear in the transaction table."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00)],
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

        result = spark.table(f"{TEST_SCHEMA}.transaction")
        assert result.count() == 1

        row = result.collect()[0]
        assert row["tran_id"] == "TXN001"
        assert row["tran_amt"] == Decimal("100.00")
        assert row["tran_card_num"] == "4111111111111111"
        assert row["tran_type_cd"] == "01"
        assert row["tran_cat_cd"] == 5001
        assert row["tran_proc_ts"] is not None

    def test_multiple_valid_transactions_posted(self, spark, clean_tables):
        """Multiple valid transactions should all be written."""
        daily_tran = spark.createDataFrame(
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00),
                make_daily_tran("TXN002", "4222222222222222", 200.00),
                make_daily_tran("TXN003", "4333333333333333", 50.00),
            ],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [
                make_xref("4111111111111111", 100000001, 80000000001),
                make_xref("4222222222222222", 100000002, 80000000002),
                make_xref("4333333333333333", 100000003, 80000000003),
            ],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [
                make_account(80000000001),
                make_account(80000000002),
                make_account(80000000003),
            ],
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

        result = spark.table(f"{TEST_SCHEMA}.transaction")
        assert result.count() == 3

        posted_ids = sorted([r["tran_id"] for r in result.collect()])
        assert posted_ids == ["TXN001", "TXN002", "TXN003"]

    def test_field_mapping_from_daily_to_transaction(self, spark, clean_tables):
        """All fields from daily transaction should be correctly mapped."""
        daily_tran = spark.createDataFrame(
            [(
                "TXN001", "02", 5002, "ONLINE", "Test purchase desc",
                Decimal("250.75"), 900000099, "MerchantXYZ",
                "CityABC", "54321", "4111111111111111",
                "2026-01-15-14.30.00.000000", None,
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
        assert row["tran_id"] == "TXN001"
        assert row["tran_type_cd"] == "02"
        assert row["tran_cat_cd"] == 5002
        assert row["tran_source"] == "ONLINE"
        assert row["tran_desc"] == "Test purchase desc"
        assert row["tran_amt"] == Decimal("250.75")
        assert row["tran_merchant_id"] == 900000099
        assert row["tran_merchant_name"] == "MerchantXYZ"
        assert row["tran_merchant_city"] == "CityABC"
        assert row["tran_merchant_zip"] == "54321"
        assert row["tran_card_num"] == "4111111111111111"
        assert row["tran_orig_ts"] == "2026-01-15-14.30.00.000000"

    def test_refund_transaction_posted_with_negative_amount(self, spark, clean_tables):
        """Negative amount (refund) should be posted correctly."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", -150.00)],
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
        assert row["tran_amt"] == Decimal("-150.00")

    def test_zero_amount_transaction_posted(self, spark, clean_tables):
        """Zero amount transaction should be posted."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 0.00)],
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
        assert row["tran_amt"] == Decimal("0.00")
