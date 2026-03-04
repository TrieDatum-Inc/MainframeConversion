import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jobs.cbact04c_interest_calculator import INTEREST_TRAN_ID_PREFIX_FORMAT


class TestInterestTranIdFormat:
    def test_format_string(self):
        assert INTEREST_TRAN_ID_PREFIX_FORMAT == "%Y%m%d"

    def test_format_produces_8_chars(self):
        from datetime import datetime
        result = datetime(2025, 1, 15).strftime(INTEREST_TRAN_ID_PREFIX_FORMAT)
        assert result == "20250115"
        assert len(result) == 8


class TestInterestCalculationLogic:
    """Test interest computation formulas without Spark."""

    def test_monthly_interest_formula(self):
        tran_cat_bal = 1000.0
        int_rate = 18.0
        monthly_interest = round((tran_cat_bal * int_rate) / 1200, 2)
        assert monthly_interest == 15.0

    def test_zero_rate_no_interest(self):
        tran_cat_bal = 5000.0
        int_rate = 0.0
        monthly_interest = round((tran_cat_bal * int_rate) / 1200, 2)
        assert monthly_interest == 0.0

    def test_high_balance_interest(self):
        tran_cat_bal = 50000.0
        int_rate = 24.0
        monthly_interest = round((tran_cat_bal * int_rate) / 1200, 2)
        assert monthly_interest == 1000.0

    def test_small_balance_interest(self):
        tran_cat_bal = 10.0
        int_rate = 12.0
        monthly_interest = round((tran_cat_bal * int_rate) / 1200, 2)
        assert monthly_interest == 0.1

    def test_run_prefix_generation(self):
        parm_date = "2025-03-15"
        run_prefix = parm_date.replace("-", "")
        assert run_prefix == "20250315"

    def test_idempotency_check_logic(self):
        existing_tran_ids = ["20250315000001", "20250315000002"]
        run_prefix = "20250315"
        matching = [t for t in existing_tran_ids if t.startswith(run_prefix)]
        assert len(matching) == 2

        run_prefix_other = "20250316"
        matching_other = [t for t in existing_tran_ids if t.startswith(run_prefix_other)]
        assert len(matching_other) == 0

    def test_interest_tran_id_structure(self):
        run_prefix = "20250315"
        row_num = 1
        tran_id = f"{run_prefix}{row_num:06d}"
        assert tran_id == "20250315000001"
        assert len(tran_id) == 14

    def test_total_interest_per_account(self):
        interest_rows = [
            {"acct_id": 1, "monthly_interest": 15.0},
            {"acct_id": 1, "monthly_interest": 10.0},
            {"acct_id": 2, "monthly_interest": 25.0},
        ]
        from collections import defaultdict
        totals = defaultdict(float)
        for row in interest_rows:
            totals[row["acct_id"]] += row["monthly_interest"]
        assert totals[1] == 25.0
        assert totals[2] == 25.0
