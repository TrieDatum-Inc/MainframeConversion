"""
Test cases for CBTRN02C reject writing logic.

Tests cover the write_rejects function which replicates COBOL paragraph
2500-WRITE-REJECT-REC: writes rejected transactions with failure reason
codes and descriptions to the daily_rejects Delta table.
"""

import pytest
from decimal import Decimal
from pyspark.sql import functions as F

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cbtrn02c_post_daily_transactions import (
    validate_and_split,
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
    make_daily_tran,
    make_xref,
    make_account,
)


class TestWriteRejects:
    """Test writing rejected transactions to the daily_rejects Delta table."""

    def _validate_and_write_rejects(self, spark, daily_rows, xref_rows, acct_rows):
        """Helper: validate transactions, write rejects, return rejects table."""
        daily_tran = spark.createDataFrame(daily_rows, schema=DAILY_TRAN_SCHEMA)
        card_xref = spark.createDataFrame(xref_rows, schema=CARD_XREF_SCHEMA)
        account = spark.createDataFrame(acct_rows, schema=ACCOUNT_SCHEMA)

        _, rejects = validate_and_split(daily_tran, card_xref, account)

        import cbtrn02c_post_daily_transactions as mod
        original_schema = mod.SCHEMA
        mod.SCHEMA = TEST_SCHEMA
        try:
            write_rejects(spark, rejects)
        finally:
            mod.SCHEMA = original_schema

        return spark.table(f"{TEST_SCHEMA}.daily_rejects")

    def test_invalid_card_reject_written(self, spark, clean_tables):
        """Reject for invalid card should be written with code 100."""
        result = self._validate_and_write_rejects(
            spark,
            [make_daily_tran("TXN001", "9999999999999999", 100.00)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
        )

        assert result.count() == 1
        row = result.collect()[0]
        assert row["dalytran_id"] == "TXN001"
        assert row["reject_reason_code"] == REJECT_INVALID_CARD
        assert "INVALID CARD" in row["reject_reason_desc"]
        assert row["reject_timestamp"] is not None

    def test_account_not_found_reject_written(self, spark, clean_tables):
        """Reject for account not found should be written with code 101."""
        result = self._validate_and_write_rejects(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 100.00)],
            [make_xref("4111111111111111", 100000001, 80000000099)],
            [make_account(80000000001)],
        )

        assert result.count() == 1
        row = result.collect()[0]
        assert row["reject_reason_code"] == REJECT_ACCOUNT_NOT_FOUND

    def test_overlimit_reject_written(self, spark, clean_tables):
        """Reject for overlimit should be written with code 102."""
        result = self._validate_and_write_rejects(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 10000.00)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, credit_limit=5000.0, cyc_credit=0.0)],
        )

        assert result.count() == 1
        row = result.collect()[0]
        assert row["reject_reason_code"] == REJECT_OVERLIMIT
        assert "OVERLIMIT" in row["reject_reason_desc"]

    def test_expired_reject_written(self, spark, clean_tables):
        """Reject for expired account should be written with code 103."""
        result = self._validate_and_write_rejects(
            spark,
            [make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2026-01-15-10.00.00.000000")],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001, expiration_date="2025-12-31")],
        )

        assert result.count() == 1
        row = result.collect()[0]
        assert row["reject_reason_code"] == REJECT_EXPIRED
        assert "EXPIRATION" in row["reject_reason_desc"]

    def test_multiple_rejects_all_written(self, spark, clean_tables):
        """Multiple rejects from different validation rules all written."""
        result = self._validate_and_write_rejects(
            spark,
            [
                make_daily_tran("TXN001", "9999999999999999", 100.00),
                make_daily_tran("TXN002", "4111111111111111", 10000.00),
                make_daily_tran("TXN003", "4222222222222222", 100.00, orig_ts="2026-06-15-10.00.00.000000"),
            ],
            [
                make_xref("4111111111111111", 100000001, 80000000001),
                make_xref("4222222222222222", 100000002, 80000000002),
            ],
            [
                make_account(80000000001, credit_limit=5000.0, cyc_credit=0.0),
                make_account(80000000002, expiration_date="2025-12-31"),
            ],
        )

        assert result.count() == 3
        codes = sorted([r["reject_reason_code"] for r in result.collect()])
        assert REJECT_INVALID_CARD in codes
        assert REJECT_OVERLIMIT in codes
        assert REJECT_EXPIRED in codes

    def test_reject_preserves_original_transaction_data(self, spark, clean_tables):
        """All original daily transaction fields should be preserved in reject record."""
        result = self._validate_and_write_rejects(
            spark,
            [(
                "TXN001", "02", 5002, "ONLINE", "Test purchase",
                Decimal("250.75"), 900000099, "MerchantXYZ",
                "CityABC", "54321", "9999999999999999",
                "2026-01-15-14.30.00.000000", None,
            )],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
        )

        row = result.collect()[0]
        assert row["dalytran_id"] == "TXN001"
        assert row["dalytran_type_cd"] == "02"
        assert row["dalytran_cat_cd"] == 5002
        assert row["dalytran_source"] == "ONLINE"
        assert row["dalytran_desc"] == "Test purchase"
        assert row["dalytran_amt"] == Decimal("250.75")
        assert row["dalytran_merchant_id"] == 900000099
        assert row["dalytran_merchant_name"] == "MerchantXYZ"
        assert row["dalytran_merchant_city"] == "CityABC"
        assert row["dalytran_merchant_zip"] == "54321"
        assert row["dalytran_card_num"] == "9999999999999999"
        assert row["dalytran_orig_ts"] == "2026-01-15-14.30.00.000000"

    def test_reject_timestamp_populated(self, spark, clean_tables):
        """Reject records should have a non-null reject_timestamp."""
        result = self._validate_and_write_rejects(
            spark,
            [make_daily_tran("TXN001", "9999999999999999", 100.00)],
            [make_xref("4111111111111111", 100000001, 80000000001)],
            [make_account(80000000001)],
        )

        row = result.collect()[0]
        assert row["reject_timestamp"] is not None

    def test_no_rejects_writes_nothing(self, spark, clean_tables):
        """When all transactions are valid, no rejects should be written."""
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

        _, rejects = validate_and_split(daily_tran, card_xref, account)

        import cbtrn02c_post_daily_transactions as mod
        original_schema = mod.SCHEMA
        mod.SCHEMA = TEST_SCHEMA
        try:
            if rejects.count() > 0:
                write_rejects(spark, rejects)
        finally:
            mod.SCHEMA = original_schema

        result = spark.table(f"{TEST_SCHEMA}.daily_rejects")
        assert result.count() == 0
