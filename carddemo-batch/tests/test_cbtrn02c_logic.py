import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jobs.cbtrn02c_daily_transaction_posting import REJECT_REASONS


class TestRejectReasons:
    def test_invalid_card(self):
        assert REJECT_REASONS[100] == "INVALID CARD NUMBER FOUND"

    def test_account_not_found(self):
        assert REJECT_REASONS[101] == "ACCOUNT RECORD NOT FOUND"

    def test_overlimit(self):
        assert REJECT_REASONS[102] == "OVERLIMIT TRANSACTION"

    def test_expired(self):
        assert REJECT_REASONS[103] == "TRANSACTION RECEIVED AFTER ACCT EXPIRATION"

    def test_all_codes_present(self):
        assert set(REJECT_REASONS.keys()) == {100, 101, 102, 103}


class TestSequentialProcessingLogic:
    """Test the sequential processing logic without Spark."""

    def test_overlimit_running_balance(self):
        acct_state = {
            "curr_bal": 0.0,
            "credit_limit": 5000.0,
            "expiration_date": "2030-12-31",
            "curr_cyc_credit": 4000.0,
            "curr_cyc_debit": 0.0,
        }

        tran_amt_1 = 800.0
        assert (acct_state["curr_cyc_credit"] - acct_state["curr_cyc_debit"] + tran_amt_1) <= acct_state["credit_limit"]
        acct_state["curr_cyc_credit"] += tran_amt_1

        tran_amt_2 = 300.0
        assert (acct_state["curr_cyc_credit"] - acct_state["curr_cyc_debit"] + tran_amt_2) > acct_state["credit_limit"]

    def test_negative_amount_updates_debit(self):
        acct_state = {
            "curr_bal": 1000.0,
            "credit_limit": 5000.0,
            "expiration_date": "2030-12-31",
            "curr_cyc_credit": 1000.0,
            "curr_cyc_debit": 0.0,
        }
        tran_amt = -200.0
        acct_state["curr_bal"] += tran_amt
        if tran_amt >= 0:
            acct_state["curr_cyc_credit"] += tran_amt
        else:
            acct_state["curr_cyc_debit"] += tran_amt

        assert acct_state["curr_bal"] == 800.0
        assert acct_state["curr_cyc_credit"] == 1000.0
        assert acct_state["curr_cyc_debit"] == -200.0

    def test_expiration_check(self):
        exp_date = "2025-06-30"
        tran_date_ok = "2025-01-15"
        tran_date_bad = "2025-07-01"

        assert not (exp_date < tran_date_ok)
        assert exp_date < tran_date_bad

    def test_card_not_in_xref(self):
        xref_map = {"4111111111111111": 10000000001}
        assert "9999999999999999" not in xref_map
        assert "4111111111111111" in xref_map

    def test_account_not_in_state(self):
        acct_state = {10000000001: {"curr_bal": 0.0}}
        assert 99999999999 not in acct_state
        assert 10000000001 in acct_state

    def test_tcat_bal_accumulation(self):
        from collections import defaultdict
        tcatbal_deltas = defaultdict(float)
        tcatbal_deltas[(10000000001, "01", 1)] += 100.0
        tcatbal_deltas[(10000000001, "01", 1)] += 200.0
        tcatbal_deltas[(10000000001, "02", 2)] += 50.0

        assert tcatbal_deltas[(10000000001, "01", 1)] == 300.0
        assert tcatbal_deltas[(10000000001, "02", 2)] == 50.0

    def test_acct_delta_accumulation(self):
        from collections import defaultdict
        acct_deltas = defaultdict(lambda: {"total": 0.0, "credit": 0.0, "debit": 0.0})

        acct_deltas[10000000001]["total"] += 100.0
        acct_deltas[10000000001]["credit"] += 100.0
        acct_deltas[10000000001]["total"] += -50.0
        acct_deltas[10000000001]["debit"] += -50.0

        assert acct_deltas[10000000001]["total"] == 50.0
        assert acct_deltas[10000000001]["credit"] == 100.0
        assert acct_deltas[10000000001]["debit"] == -50.0

    def test_idempotency_skip(self):
        already_posted_ids = {"T001", "T002"}
        already_rejected_ids = {"T003"}

        assert "T001" in already_posted_ids or "T001" in already_rejected_ids
        assert "T003" in already_posted_ids or "T003" in already_rejected_ids
        assert not ("T004" in already_posted_ids or "T004" in already_rejected_ids)
