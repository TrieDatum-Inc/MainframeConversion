"""
Test cases for CBTRN02C validation logic.

Tests cover all validation rules from the original COBOL program:
    100 - Card number not found in cross-reference file
    101 - Account record not found
    102 - Transaction would exceed account credit limit (overlimit)
    103 - Transaction received after account expiration date
"""

import pytest
from decimal import Decimal
from pyspark.sql import functions as F

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cbtrn02c_post_daily_transactions import (
    validate_and_split,
    REJECT_INVALID_CARD,
    REJECT_ACCOUNT_NOT_FOUND,
    REJECT_OVERLIMIT,
    REJECT_EXPIRED,
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


class TestReject100InvalidCard:
    """Test cases for rejection code 100: Invalid card number."""

    def test_card_not_in_xref_rejected(self, spark, clean_tables):
        """Transaction with card number not in XREF should be rejected with code 100."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "9999999999999999", 100.00)],
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

        assert valid.count() == 0
        assert rejects.count() == 1

        reject_row = rejects.collect()[0]
        assert reject_row["dalytran_id"] == "TXN001"
        assert reject_row["reject_reason_code"] == REJECT_INVALID_CARD
        assert "INVALID CARD" in reject_row["reject_reason_desc"]

    def test_empty_xref_all_rejected(self, spark, clean_tables):
        """All transactions rejected when XREF table is empty."""
        daily_tran = spark.createDataFrame(
            [
                make_daily_tran("TXN001", "4111111111111111", 100.00),
                make_daily_tran("TXN002", "4222222222222222", 200.00),
            ],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame([], schema=CARD_XREF_SCHEMA)
        account = spark.createDataFrame(
            [make_account(80000000001)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 0
        assert rejects.count() == 2
        assert all(
            r["reject_reason_code"] == REJECT_INVALID_CARD
            for r in rejects.collect()
        )

    def test_partial_card_number_match_rejected(self, spark, clean_tables):
        """Partial card number match should still be rejected (exact match required)."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111112", 100.00)],
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

        assert valid.count() == 0
        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_INVALID_CARD


class TestReject101AccountNotFound:
    """Test cases for rejection code 101: Account not found."""

    def test_xref_exists_but_account_missing(self, spark, clean_tables):
        """Card in XREF but referenced account missing should reject with 101."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame([], schema=ACCOUNT_SCHEMA)

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 0
        assert rejects.count() == 1

        reject_row = rejects.collect()[0]
        assert reject_row["reject_reason_code"] == REJECT_ACCOUNT_NOT_FOUND
        assert "ACCOUNT" in reject_row["reject_reason_desc"]

    def test_xref_points_to_wrong_account(self, spark, clean_tables):
        """XREF points to account ID that doesn't exist in account table."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000099)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 0
        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_ACCOUNT_NOT_FOUND


class TestReject102Overlimit:
    """Test cases for rejection code 102: Overlimit transaction."""

    def test_single_transaction_exceeds_limit(self, spark, clean_tables):
        """Single transaction that exceeds credit limit should be rejected."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 5000.00)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, credit_limit=5000.0, cyc_credit=1000.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 0
        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_OVERLIMIT

    def test_transaction_exactly_at_limit_valid(self, spark, clean_tables):
        """Transaction that brings balance exactly to limit should be valid."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 4000.00)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, credit_limit=5000.0, cyc_credit=1000.0, cyc_debit=0.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 1
        assert rejects.count() == 0

    def test_cumulative_transactions_exceed_limit(self, spark, clean_tables):
        """Multiple transactions that cumulatively exceed limit - later ones rejected."""
        daily_tran = spark.createDataFrame(
            [
                make_daily_tran("TXN001", "4111111111111111", 3000.00, orig_ts="2026-01-15-10.00.00.000000"),
                make_daily_tran("TXN002", "4111111111111111", 2000.00, orig_ts="2026-01-15-11.00.00.000000"),
                make_daily_tran("TXN003", "4111111111111111", 1000.00, orig_ts="2026-01-15-12.00.00.000000"),
            ],
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

        assert valid.count() == 2
        assert rejects.count() == 1

        valid_ids = [r["dalytran_id"] for r in valid.collect()]
        assert "TXN001" in valid_ids
        assert "TXN002" in valid_ids

        reject_row = rejects.collect()[0]
        assert reject_row["dalytran_id"] == "TXN003"
        assert reject_row["reject_reason_code"] == REJECT_OVERLIMIT

    def test_negative_amount_reduces_balance(self, spark, clean_tables):
        """Refund (negative amount) should reduce running balance, allowing more purchases."""
        daily_tran = spark.createDataFrame(
            [
                make_daily_tran("TXN001", "4111111111111111", 4000.00, orig_ts="2026-01-15-10.00.00.000000"),
                make_daily_tran("TXN002", "4111111111111111", -1000.00, orig_ts="2026-01-15-11.00.00.000000"),
                make_daily_tran("TXN003", "4111111111111111", 2000.00, orig_ts="2026-01-15-12.00.00.000000"),
            ],
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

        assert valid.count() == 3
        assert rejects.count() == 0

    def test_existing_debit_increases_available_credit(self, spark, clean_tables):
        """Existing cycle debit (negative) should increase available credit."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 5500.00)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, credit_limit=5000.0, cyc_credit=0.0, cyc_debit=-1000.0)],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 1
        assert rejects.count() == 0


class TestReject103Expired:
    """Test cases for rejection code 103: Expired account."""

    def test_transaction_after_expiration_rejected(self, spark, clean_tables):
        """Transaction dated after account expiration should be rejected."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2026-01-15-10.00.00.000000")],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, expiration_date="2025-12-31")],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 0
        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_EXPIRED

    def test_transaction_on_expiration_date_valid(self, spark, clean_tables):
        """Transaction on exact expiration date should be valid."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2025-12-31-23.59.59.000000")],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, expiration_date="2025-12-31")],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 1
        assert rejects.count() == 0

    def test_transaction_before_expiration_valid(self, spark, clean_tables):
        """Transaction before expiration date should be valid."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 100.00, orig_ts="2025-06-15-10.00.00.000000")],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, expiration_date="2025-12-31")],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert valid.count() == 1
        assert rejects.count() == 0


class TestValidationPriority:
    """Test validation order and priority when multiple failures apply."""

    def test_invalid_card_checked_before_account(self, spark, clean_tables):
        """Invalid card should be caught before account lookup."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "9999999999999999", 100.00)],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame([], schema=CARD_XREF_SCHEMA)
        account = spark.createDataFrame([], schema=ACCOUNT_SCHEMA)

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_INVALID_CARD

    def test_overlimit_checked_before_expiration(self, spark, clean_tables):
        """Overlimit should be checked before expiration in validation sequence."""
        daily_tran = spark.createDataFrame(
            [make_daily_tran("TXN001", "4111111111111111", 10000.00, orig_ts="2026-01-15-10.00.00.000000")],
            schema=DAILY_TRAN_SCHEMA,
        )
        card_xref = spark.createDataFrame(
            [make_xref("4111111111111111", 100000001, 80000000001)],
            schema=CARD_XREF_SCHEMA,
        )
        account = spark.createDataFrame(
            [make_account(80000000001, credit_limit=5000.0, expiration_date="2025-12-31")],
            schema=ACCOUNT_SCHEMA,
        )

        valid, rejects = validate_and_split(daily_tran, card_xref, account)

        assert rejects.count() == 1
        assert rejects.collect()[0]["reject_reason_code"] == REJECT_OVERLIMIT
